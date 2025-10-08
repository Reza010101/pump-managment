from flask import Flask, render_template, request, redirect, session, jsonify, flash, send_file
import sqlite3
from datetime import datetime, timedelta
import os
from date_converter import gregorian_to_jalali, jalali_to_gregorian
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'pump_management_secret_key_2024'

def get_db_connection():
    conn = sqlite3.connect('pump_management.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_pump_history_from_db(pump_number):
    """دریافت تاریخچه یک پمپ خاص از دیتابیس"""
    conn = get_db_connection()
    
    pump = conn.execute(
        'SELECT id FROM pumps WHERE pump_number = ?', (pump_number,)
    ).fetchone()
    
    if not pump:
        conn.close()
        return []
    
    pump_id = pump['id']
    
    history = conn.execute('''
        SELECT action, event_time, reason, notes 
        FROM pump_history 
        WHERE pump_id = ? 
        ORDER BY event_time
    ''', (pump_id,)).fetchall()
    
    conn.close()
    
    events = []
    for event in history:
        events.append({
            'action': event['action'],
            'event_time': event['event_time'],
            'reason': event['reason'],
            'notes': event['notes'],
            'source': 'existing'
        })
    
    return events

def get_last_event_before(pump_id, datetime_obj):
    """پیدا کردن آخرین رویداد قبل از زمان مشخص"""
    conn = get_db_connection()
    event = conn.execute('''
        SELECT action, event_time 
        FROM pump_history 
        WHERE pump_id = ? AND event_time < ?
        ORDER BY event_time DESC 
        LIMIT 1
    ''', (pump_id, datetime_obj.strftime('%Y-%m-%d %H:%M:%S'))).fetchone()
    conn.close()
    
    if event:
        return {
            'action': event['action'],
            'event_time': datetime.strptime(event['event_time'], '%Y-%m-%d %H:%M:%S')
        }
    return None

def get_pump_events_in_range(pump_id, start_time, end_time):
    """دریافت رویدادهای یک پمپ در بازه زمانی مشخص"""
    conn = get_db_connection()
    events = conn.execute('''
        SELECT action, event_time 
        FROM pump_history 
        WHERE pump_id = ? AND event_time BETWEEN ? AND ?
        ORDER BY event_time
    ''', (pump_id, start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()
    conn.close()
    
    result = []
    for event in events:
        result.append({
            'action': event['action'],
            'event_time': datetime.strptime(event['event_time'], '%Y-%m-%d %H:%M:%S')
        })
    return result

def calculate_daily_operating_hours(pump_id, target_date_jalali):
    """محاسبه ساعات کارکرد یک پمپ در یک روز خاص"""
    try:
        start_of_day_str = jalali_to_gregorian(f"{target_date_jalali} 00:00:00")
        end_of_day_str = jalali_to_gregorian(f"{target_date_jalali} 23:59:59")
        
        start_of_day = datetime.strptime(start_of_day_str, '%Y-%m-%d %H:%M:%S')
        end_of_day = datetime.strptime(end_of_day_str, '%Y-%m-%d %H:%M:%S')
        
        last_event_before = get_last_event_before(pump_id, start_of_day)
        
        days_events = get_pump_events_in_range(pump_id, start_of_day, end_of_day)
        
        if last_event_before:
            current_status = last_event_before['action']
        else:
            current_status = 'OFF'
        
        if not days_events:
            return 24.0 if current_status == 'ON' else 0.0
        
        total_seconds = 0
        current_time = start_of_day
        
        all_events = days_events + [{'event_time': end_of_day, 'action': 'END'}]
        
        for event in all_events:
            if current_status == 'ON':
                time_diff = (event['event_time'] - current_time).total_seconds()
                total_seconds += time_diff
            
            if event['action'] != 'END':
                current_status = event['action']
                current_time = event['event_time']
        
        hours = total_seconds / 3600
        return round(hours, 2)
        
    except Exception as e:
        return 0.0
    
def calculate_monthly_operating_hours(pump_id, target_month_jalali):
    """محاسبه ساعات کارکرد یک پمپ در یک ماه خاص"""
    try:
        year, month = map(int, target_month_jalali.split('/'))
        total_hours = 0
        
        for day in range(1, 32):
            try:
                date_jalali = f"{year}/{month:02d}/{day:02d}"
                daily_hours = calculate_daily_operating_hours(pump_id, date_jalali)
                total_hours += daily_hours
            except Exception:
                continue
        
        return round(total_hours, 2)
        
    except Exception as e:
        return 0.0

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', 
            (username, password)
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            update_pump_current_status()
            flash('با موفقیت وارد شدید!', 'success')
            return redirect('/')
        else:
            flash('نام کاربری یا رمز عبور اشتباه است!', 'error')
    
    return render_template('login.html')

@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    
    # 🔽 این کوئری رو اصلاح کن 🔽
    pumps = conn.execute('''
        SELECT p.*, 
               (SELECT action FROM pump_history 
                WHERE pump_id = p.id 
                ORDER BY event_time DESC, id DESC LIMIT 1) as last_action,
               (SELECT COUNT(*) FROM pump_history WHERE pump_id = p.id) as has_history
        FROM pumps p 
        ORDER BY p.pump_number
    ''').fetchall()
    
    conn.close()
    
    pumps_with_jalali = []
    for pump in pumps:
        pump_dict = dict(pump)
        pump_dict['has_history'] = pump['has_history']
        
        # 🔽 وضعیت رو بر اساس last_action تنظیم کن 🔽
        if pump['last_action']:
            pump_dict['status'] = 1 if pump['last_action'] == 'ON' else 0
        else:
            pump_dict['status'] = 0  # اگر تاریخچه نداره، خاموش
            
        if pump['last_change']:
            pump_dict['last_change_jalali'] = gregorian_to_jalali(pump['last_change'])
        else:
            pump_dict['last_change_jalali'] = 'بدون تاریخچه'
        pumps_with_jalali.append(pump_dict)
    
    return render_template('dashboard.html', pumps=pumps_with_jalali)

@app.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت خارج شدید!', 'success')
    return redirect('/login')

@app.route('/pump/change-status', methods=['POST'])
def change_pump_status_detailed():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    data = request.get_json()
    pump_id = data.get('pump_id')
    action = data.get('action').upper()  # 🔽 این خط رو تغییر بده 🔽
    reason = data.get('reason')
    notes = data.get('notes', '')
    action_date_jalali = data.get('action_date_jalali')
    action_time = data.get('action_time')
    manual_time = data.get('manual_time', False)
    
    conn = get_db_connection()
    
    try:
        current_pump = conn.execute(
            'SELECT status FROM pumps WHERE id = ?', (pump_id,)
        ).fetchone()
        
        if not current_pump:
            return jsonify({'success': False, 'error': 'پمپ پیدا نشد'})
        
        current_status = current_pump['status']
        new_status = True if action == 'ON' else False  # 🔽 اینجا هم ON باشه 🔽
        
        # اینجا سیستم درست چک میکنه چون action الان ON/OFF هست
        if current_status == new_status and get_last_pump_event_time(pump_id):
            return jsonify({
                'success': False, 
                'error': f'پمپ در حال حاضر {"روشن" if current_status else "خاموش"} است'
            })
                      
        event_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        recorded_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if manual_time and action_date_jalali and action_time:
            jalali_datetime_str = f"{action_date_jalali} {action_time}:00"
            event_time = jalali_to_gregorian(jalali_datetime_str)
            
            last_event_time = get_last_pump_event_time(pump_id)
            if last_event_time and event_time <= last_event_time:
                last_event_jalali = gregorian_to_jalali(last_event_time)
                return jsonify({
                    'success': False, 
                    'error': f'تاریخ انتخاب شده باید بعد از آخرین ثبت ({last_event_jalali[:16]}) باشد'
                })

        conn.execute(
            'UPDATE pumps SET status = ?, last_change = ? WHERE id = ?',
            (new_status, event_time, pump_id)
        )
        
        # 🔽 action اینجا هم به حروف بزرگ ذخیره میشه 🔽
        conn.execute(
            '''INSERT INTO pump_history 
            (pump_id, user_id, action, event_time, recorded_time, reason, notes, manual_time) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (pump_id, session['user_id'], action, event_time, recorded_time, reason, notes, manual_time)
        )
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'پمپ با موفقیت {"روشن" if new_status else "خاموش"} شد'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/report/history')
def history_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    return "صفحه گزارش تاریخی - به زودی..."

@app.route('/report/operating-hours')
def operating_hours_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    month_jalali = request.args.get('month')
    report_type = request.args.get('report_type', 'daily')
    
    results = []
    
    if report_type == 'daily' and date_jalali:
        for pump_id in range(1, 59):
            pump_hours = calculate_daily_operating_hours(pump_id, date_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'name': pump['name'],
                    'operating_hours': pump_hours
                })
                
    elif report_type == 'monthly' and month_jalali:
        for pump_id in range(1, 59):
            pump_hours = calculate_monthly_operating_hours(pump_id, month_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'name': pump['name'],
                    'operating_hours': pump_hours
                })
    
    results.sort(key=lambda x: x['pump_number'])
    
    return render_template('operating_hours_report.html', 
                         results=results,
                         date_jalali=date_jalali,
                         month_jalali=month_jalali,
                         report_type=report_type)

@app.route('/report/operating-hours/export')
def export_operating_hours():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    month_jalali = request.args.get('month')
    report_type = request.args.get('report_type', 'daily')
    
    results = []
    
    if report_type == 'daily' and date_jalali:
        period_title = f"گزارش ساعات کارکرد روزانه - تاریخ: {date_jalali}"
        for pump_id in range(1, 59):
            pump_hours = calculate_daily_operating_hours(pump_id, date_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'name': pump['name'],
                    'operating_hours': pump_hours
                })
                
    elif report_type == 'monthly' and month_jalali:
        period_title = f"گزارش ساعات کارکرد ماهانه - ماه: {month_jalali}"
        for pump_id in range(1, 59):
            pump_hours = calculate_monthly_operating_hours(pump_id, month_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'name': pump['name'],
                    'operating_hours': pump_hours
                })
    
    results.sort(key=lambda x: x['pump_number'])
    
    df = pd.DataFrame(results)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='گزارش ساعات کارکرد', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['گزارش ساعات کارکرد']
        
        worksheet['A1'] = period_title
        worksheet.merge_cells('A1:C1')
        
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 25
        worksheet.column_dimensions['C'].width = 20
    
    output.seek(0)
    
    if report_type == 'daily':
        filename = f'operating_hours_daily_{date_jalali.replace("/", "-")}.xlsx'
    else:
        filename = f'operating_hours_monthly_{month_jalali.replace("/", "-")}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/admin/users')
def manage_users():
    if 'user_id' not in session:
        return redirect('/login')
    
    if session['role'] != 'admin':
        flash('شما دسترسی به این صفحه را ندارید!', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_date DESC').fetchall()
    conn.close()
    
    return render_template('manage_users.html', users=users)

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        conn = get_db_connection()
        
        user = conn.execute(
            'SELECT * FROM users WHERE id = ? AND password = ?',
            (session['user_id'], current_password)
        ).fetchone()
        
        if not user:
            flash('پسورد فعلی اشتباه است!', 'error')
            return redirect('/change-password')
        
        if new_password != confirm_password:
            flash('پسورد جدید و تکرار آن مطابقت ندارند!', 'error')
            return redirect('/change-password')
        
        if len(new_password) < 4:
            flash('پسورد جدید باید حداقل ۴ کاراکتر باشد!', 'error')
            return redirect('/change-password')
        
        conn.execute(
            'UPDATE users SET password = ?, last_password_change = CURRENT_TIMESTAMP WHERE id = ?',
            (new_password, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        flash('پسورد با موفقیت تغییر کرد!', 'success')
        return redirect('/')
    
    return render_template('change_password.html')

@app.route('/admin/create-user', methods=['GET', 'POST'])
def create_user():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        
        conn = get_db_connection()
        
        try:
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            if existing_user:
                flash('نام کاربری قبلاً استفاده شده است!', 'error')
                return redirect('/admin/create-user')
            
            conn.execute(
                'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
                (username, password, full_name, role)
            )
            conn.commit()
            conn.close()
            
            flash(f'کاربر {full_name} با موفقیت ایجاد شد!', 'success')
            return redirect('/admin/users')
            
        except Exception as e:
            conn.rollback()
            flash(f'خطا در ایجاد کاربر: {str(e)}', 'error')
            return redirect('/admin/create-user')
    
    return render_template('create_user.html')

@app.route('/admin/delete-user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    if user_id == session['user_id']:
        flash('شما نمی‌توانید حساب خود را حذف کنید!', 'error')
        return redirect('/admin/users')
    
    conn = get_db_connection()
    
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        flash('کاربر با موفقیت حذف شد!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'خطا در حذف کاربر: {str(e)}', 'error')
    
    return redirect('/admin/users')

@app.route('/admin/import-history', methods=['GET', 'POST'])
def import_history():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('لطفا فایل اکسل را انتخاب کنید', 'error')
            return redirect('/admin/import-history')
        
        file = request.files['excel_file']
        
        if file.filename == '':
            flash('لطفا فایل اکسل را انتخاب کنید', 'error')
            return redirect('/admin/import-history')
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('لطفا فایل اکسل معتبر انتخاب کنید (xlsx یا xls)', 'error')
            return redirect('/admin/import-history')
        
        try:
            df = pd.read_excel(file)
            
            required_columns = ['Pump_Number', 'Action', 'Reason', 'Date_Jalali', 'Time_Jalali']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'ستون‌های ضروری وجود ندارند: {", ".join(missing_columns)}', 'error')
                return redirect('/admin/import-history')
            
            conn = get_db_connection()
            success_count = 0
            error_count = 0
            error_messages = []
            
            pump_groups = {}
            for index, row in df.iterrows():
                try:
                    pump_num = int(row['Pump_Number'])
                    if pump_num not in pump_groups:
                        pump_groups[pump_num] = []
                    
                    date_jalali = str(row['Date_Jalali']).strip()
                    time_jalali = str(row['Time_Jalali']).strip()
                    
                    if ':' not in time_jalali:
                        time_jalali += ':00'
                    elif time_jalali.count(':') == 1:
                        time_jalali += ':00'
                    
                    jalali_datetime = f"{date_jalali} {time_jalali}"
                    event_time_gregorian = jalali_to_gregorian(jalali_datetime)
                    
                    pump_groups[pump_num].append({
                        'row_index': index + 2,
                        'action': str(row['Action']).upper().strip(),
                        'event_time': event_time_gregorian,
                        'reason': str(row['Reason']).strip(),
                        'notes': str(row['Notes']) if 'Notes' in df.columns and pd.notna(row['Notes']) else '',
                        'jalali_time': jalali_datetime,
                        'source': 'new'
                    })
                    
                except Exception as e:
                    error_messages.append(f'خط {index+2}: پمپ {pump_num} - خطا در پردازش داده ({str(e)})')
                    error_count += 1
            
            for pump_num, new_events in pump_groups.items():
                try:
                    existing_events = get_pump_history_from_db(pump_num)
                    
                    all_events = existing_events + new_events
                    all_events.sort(key=lambda x: x['event_time'])
                    
                    timeline_errors = []
                    for i in range(1, len(all_events)):
                        prev_action = all_events[i-1]['action']
                        current_action = all_events[i]['action']
                        
                        if prev_action == current_action:
                            error_event = all_events[i]
                            prev_event = all_events[i-1]
                            
                            timeline_errors.append({
                                'row_index': error_event.get('row_index', 'موجود'),
                                'message': f'پمپ {pump_num}: {current_action} در {error_event["jalali_time"]} - مغایرت منطقی (پمپ از {prev_event["jalali_time"]} در حالت {prev_action} بوده)'
                            })
                                                
                    if timeline_errors:
                        error_count += len(timeline_errors)
                        for error in timeline_errors:
                            error_messages.append(f'خط {error["row_index"]}: {error["message"]}')
                    else:
                        for event in new_events:
                            try:
                                pump = conn.execute(
                                    'SELECT id FROM pumps WHERE pump_number = ?', (pump_num,)
                                ).fetchone()
                                
                                if pump:
                                    conn.execute(
                                    '''INSERT INTO pump_history 
                                    (pump_id, user_id, action, event_time, recorded_time, reason, notes, manual_time) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (pump['id'], session['user_id'], event['action'], 
                                    event['event_time'], datetime.now(), event['reason'], event['notes'], True)
                                )
                                    success_count += 1
                                else:
                                    error_messages.append(f'خط {event["row_index"]}: پمپ با شماره {pump_num} یافت نشد')
                                    error_count += 1
                                
                            except Exception as e:
                                error_messages.append(f'خط {event["row_index"]}: پمپ {pump_num} - خطا در ذخیره‌سازی ({str(e)})')
                                error_count += 1
                
                except Exception as e:
                    error_messages.append(f'پمپ {pump_num}: خطا در پردازش - {str(e)}')
                    error_count += 1
            
            if success_count > 0:
                conn.commit()
                update_pump_current_status()
                flash(f'✅ {success_count} رکورد با موفقیت وارد شد', 'success')
            
            if error_count > 0:
                flash(f'❌ {error_count} خطا در پردازش', 'error')
                for i, error_msg in enumerate(error_messages[:10]):
                    flash(f'خطا {i+1}: {error_msg}', 'warning')
                if len(error_messages) > 10:
                    flash(f'... و {len(error_messages) - 10} خطای دیگر', 'warning')
            
            conn.close()
            return redirect('/admin/import-history')
            
        except Exception as e:
            flash(f'خطا در پردازش فایل: {str(e)}', 'error')
            return redirect('/admin/import-history')
    
    return render_template('import_history.html')

@app.route('/admin/download-sample')
def download_sample():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    sample_data = {
        'Pump_Number': [1, 1, 2, 3],
        'Action': ['ON', 'OFF', 'ON', 'OFF'],
        'Date_Jalali': ['1403/07/10', '1403/07/10', '1403/07/11', '1403/07/11'],
        'Time_Jalali': ['08:00', '12:30', '09:15', '17:45'],
        'Reason': ['برنامه ریزی شده', 'قطع برق', 'تعمیرات', 'پایان شیفت'],
        'Notes': ['', 'قطع ۲ ساعته', 'تعویض قطعه', '']
    }
    
    df = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sample', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='pump_history_sample.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def update_pump_current_status():
    """آپدیت وضعیت فعلی پمپ‌ها بر اساس آخرین رویداد واقعی"""
    conn = get_db_connection()
    
    for pump_id in range(1, 59):
        # پیدا کردن آخرین رویداد بر اساس event_time (زمان واقعی رویداد)
        last_event = conn.execute('''
            SELECT action, event_time 
            FROM pump_history 
            WHERE pump_id = ? 
            ORDER BY event_time DESC, id DESC
            LIMIT 1
        ''', (pump_id,)).fetchone()
        
        if last_event:
            # آپدیت وضعیت فعلی پمپ بر اساس آخرین رویداد واقعی
            current_status = 1 if last_event['action'].upper() == 'ON' else 0
            conn.execute(
                'UPDATE pumps SET status = ?, last_change = ? WHERE id = ?',
                (current_status, last_event['event_time'], pump_id)
            )
        else:
            # اگر هیچ رویدادی نداره، خاموش باشه
            conn.execute(
                'UPDATE pumps SET status = 0, last_change = CURRENT_TIMESTAMP WHERE id = ?',
                (pump_id,)
            )
    
    conn.commit()
    conn.close()

@app.route('/reports')
def reports_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('reports.html')

@app.route('/report/status-at-time')
def status_at_time_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    time = request.args.get('time')
    display_type = request.args.get('display_type', 'off')
    
    if not date_jalali or not time:
        return render_template('status_at_time_report.html')
    
    target_datetime_jalali = f"{date_jalali} {time}:00"
    target_datetime_gregorian = jalali_to_gregorian(target_datetime_jalali)

    conn = get_db_connection()
    results = []

    for pump_id in range(1, 59):
        last_event = conn.execute('''
            SELECT ph.action, ph.event_time, ph.reason, ph.notes, p.pump_number, p.name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            WHERE ph.pump_id = ? AND ph.event_time <= ?
            ORDER BY ph.event_time DESC 
            LIMIT 1
        ''', (pump_id, target_datetime_gregorian)).fetchone()
        
        if last_event:
            status = 'ON' if last_event['action'].upper() == 'ON' else 'OFF'
            last_change_jalali = gregorian_to_jalali(last_event['event_time'])
            
            if display_type == 'all' or (display_type == 'on' and status == 'ON') or (display_type == 'off' and status == 'OFF'):
                results.append({
                    'pump_number': last_event['pump_number'],
                    'name': last_event['name'],
                    'status': status,
                    'last_change': last_change_jalali,
                    'reason': last_event['reason'],
                    'notes': last_event['notes']
                })

    conn.close()
    
    return render_template('status_at_time_report.html', 
                         results=results, 
                         date_jalali=date_jalali, 
                         time=time, 
                         display_type=display_type)

@app.route('/report/status-at-time/export')
def export_status_at_time():
    if 'user_id' not in session:
        return redirect('/login')
    
    date_jalali = request.args.get('date')
    time = request.args.get('time')
    display_type = request.args.get('display_type', 'off')
    
    target_datetime_jalali = f"{date_jalali} {time}:00"
    target_datetime_gregorian = jalali_to_gregorian(target_datetime_jalali)

    conn = get_db_connection()
    results = []

    for pump_id in range(1, 59):
        last_event = conn.execute('''
            SELECT ph.action, ph.event_time, ph.reason, ph.notes, p.pump_number, p.name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            WHERE ph.pump_id = ? AND ph.event_time <= ?
            ORDER BY ph.event_time DESC 
            LIMIT 1
        ''', (pump_id, target_datetime_gregorian)).fetchone()
        
        if last_event:
            status = 'ON' if last_event['action'] == 'ON' else 'OFF'
            last_change_jalali = gregorian_to_jalali(last_event['event_time'])
            
            if display_type == 'all' or (display_type == 'on' and status == 'ON') or (display_type == 'off' and status == 'OFF'):
                results.append({
                    'pump_number': last_event['pump_number'],
                    'name': last_event['name'],
                    'status': status,
                    'last_change': last_change_jalali,
                    'reason': last_event['reason'],
                    'notes': last_event['notes']
                })

    conn.close()
    
    df = pd.DataFrame(results)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='گزارش وضعیت', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'status_report_{date_jalali}_{time}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def get_last_pump_event_time(pump_id):
    """آخرین زمان ثبت شده برای پمپ را برمی‌گرداند"""
    conn = get_db_connection()
    last_event = conn.execute(
        'SELECT event_time FROM pump_history WHERE pump_id = ? ORDER BY event_time DESC LIMIT 1',
        (pump_id,)
    ).fetchone()
    conn.close()
    
    return last_event['event_time'] if last_event else None

@app.route('/report/full-history')
def full_history_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    from_date_jalali = request.args.get('from_date')
    to_date_jalali = request.args.get('to_date')
    pump_id = request.args.get('pump_id', 'all')
    
    results = []
    
    if from_date_jalali and to_date_jalali:
        start_date = jalali_to_gregorian(f"{from_date_jalali} 00:00:00")
        end_date = jalali_to_gregorian(f"{to_date_jalali} 23:59:59")
        
        conn = get_db_connection()
        
        if pump_id == 'all':
            query = '''
                SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                       ph.reason, ph.notes, u.full_name as user_name
                FROM pump_history ph
                JOIN pumps p ON ph.pump_id = p.id
                JOIN users u ON ph.user_id = u.id
                WHERE ph.event_time BETWEEN ? AND ?
                ORDER BY ph.event_time DESC
            '''
            params = (start_date, end_date)
        else:
            query = '''
                SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                       ph.reason, ph.notes, u.full_name as user_name
                FROM pump_history ph
                JOIN pumps p ON ph.pump_id = p.id
                JOIN users u ON ph.user_id = u.id
                WHERE p.pump_number = ? AND ph.event_time BETWEEN ? AND ?
                ORDER BY ph.event_time DESC
            '''
            params = (pump_id, start_date, end_date)
        
        results = conn.execute(query, params).fetchall()
        conn.close()
        
        formatted_results = []
        for row in results:
            row_dict = dict(row)
            
            jalali_datetime = gregorian_to_jalali(row['event_time'])
            jalali_parts = jalali_datetime.split(' ')
            row_dict['action_date'] = jalali_parts[0]
            row_dict['action_time'] = jalali_parts[1][:5] if len(jalali_parts) > 1 else '00:00'
            row_dict['action_persian'] = 'روشن' if row['action'].upper() == 'ON' else 'خاموش'
            
            formatted_results.append(row_dict)
        
        results = formatted_results
    
    return render_template('full_history_report.html',
                         results=results,
                         from_date_jalali=from_date_jalali,
                         to_date_jalali=to_date_jalali,
                         pump_id=pump_id)

@app.route('/report/full-history/export')
def export_full_history():
    if 'user_id' not in session:
        return redirect('/login')
    
    from_date_jalali = request.args.get('from_date')
    to_date_jalali = request.args.get('to_date')
    pump_id = request.args.get('pump_id', 'all')
    
    if not from_date_jalali or not to_date_jalali:
        flash('لطفا تاریخ شروع و پایان را انتخاب کنید', 'error')
        return redirect('/report/full-history')
    
    try:
        start_date = jalali_to_gregorian(f"{from_date_jalali} 00:00:00")
        end_date = jalali_to_gregorian(f"{to_date_jalali} 23:59:59")
        
        conn = get_db_connection()
        
        if pump_id == 'all':
            query = '''
                SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                       ph.reason, ph.notes, u.full_name as user_name
                FROM pump_history ph
                JOIN pumps p ON ph.pump_id = p.id
                JOIN users u ON ph.user_id = u.id
                WHERE ph.event_time BETWEEN ? AND ?
                ORDER BY ph.event_time DESC
            '''
            params = (start_date, end_date)
        else:
            query = '''
                SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                       ph.reason, ph.notes, u.full_name as user_name
                FROM pump_history ph
                JOIN pumps p ON ph.pump_id = p.id
                JOIN users u ON ph.user_id = u.id
                WHERE p.pump_number = ? AND ph.event_time BETWEEN ? AND ?
                ORDER BY ph.event_time DESC
            '''
            params = (pump_id, start_date, end_date)
        
        results = conn.execute(query, params).fetchall()
        conn.close()
        
        data = []
        for row in results:
            jalali_datetime = gregorian_to_jalali(row['event_time'])
            jalali_parts = jalali_datetime.split(' ')
            jalali_date = jalali_parts[0]
            jalali_time = jalali_parts[1] if len(jalali_parts) > 1 else '00:00:00'
            
            data.append({
                'شماره پمپ': row['pump_number'],
                'نام پمپ': row['name'],
                'وضعیت': 'روشن' if row['action'] == 'ON' else 'خاموش',
                'تاریخ': jalali_date,
                'ساعت': jalali_time[:5],
                'علت': row['reason'],
                'توضیحات': row['notes'] or '',
                'کاربر': row['user_name']
            })
        
        if not data:
            flash('هیچ داده‌ای برای دانلود وجود ندارد', 'warning')
            return redirect('/report/full-history')
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='تاریخچه تغییرات', index=False)
            
            worksheet = writer.sheets['تاریخچه تغییرات']
            worksheet.column_dimensions['A'].width = 12
            worksheet.column_dimensions['B'].width = 20
            worksheet.column_dimensions['C'].width = 10
            worksheet.column_dimensions['D'].width = 12
            worksheet.column_dimensions['E'].width = 8
            worksheet.column_dimensions['F'].width = 20
            worksheet.column_dimensions['G'].width = 25
            worksheet.column_dimensions['H'].width = 15
        
        output.seek(0)
        
        filename = f'full_history_{from_date_jalali.replace("/", "-")}_to_{to_date_jalali.replace("/", "-")}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'خطا در تولید فایل: {str(e)}', 'error')
        return redirect('/report/full-history')
    
if __name__ == '__main__':
    if not os.path.exists('pump_management.db'):
        print("⚠️ دیتابیس وجود ندارد، لطفا ابتدا database.py را اجرا کنید")
        exit(1)
    
    print("🚀 سرور در حال اجراست...")
    print("📧 برای ورود: http://localhost:5000/login")
    print("   کاربران:")
    print("   - admin / 1234 (مدیر)")
    print("   - user1 / 1234 (کاربر)")
    
    app.run(debug=True, host='0.0.0.0', port=5000)