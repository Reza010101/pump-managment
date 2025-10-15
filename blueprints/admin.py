from flask import Blueprint, render_template, request, session, redirect, flash, send_file
import pandas as pd
from datetime import datetime
from database.users import get_all_users, create_new_user, delete_existing_user
from database.models import get_db_connection
from database.operations import update_pump_current_status
from utils.date_utils import jalali_to_gregorian
from utils.export_utils import create_sample_excel_file

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users')
def manage_users():
    if 'user_id' not in session:
        return redirect('/login')
    
    if session['role'] != 'admin':
        flash('شما دسترسی به این صفحه را ندارید!', 'error')
        return redirect('/')
    
    users = get_all_users()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/admin/create-user', methods=['GET', 'POST'])
def create_user():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        
        result = create_new_user(username, password, full_name, role)
        
        if result['success']:
            flash(f'کاربر {full_name} با موفقیت ایجاد شد!', 'success')
            return redirect('/admin/users')
        else:
            flash(result['error'], 'error')
    
    return render_template('create_user.html')

@admin_bp.route('/admin/delete-user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    if user_id == session['user_id']:
        flash('شما نمی‌توانید حساب خود را حذف کنید!', 'error')
        return redirect('/admin/users')
    
    result = delete_existing_user(user_id)
    
    if result['success']:
        flash('کاربر با موفقیت حذف شد!', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect('/admin/users')

@admin_bp.route('/admin/import-history', methods=['GET', 'POST'])
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

@admin_bp.route('/admin/download-sample')
def download_sample():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    return create_sample_excel_file()

@admin_bp.route('/admin/deletion-logs')
def deletion_logs():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    conn = get_db_connection()
    
    try:
        # تعداد کل لاگ‌ها
        total = conn.execute('SELECT COUNT(*) FROM deletion_logs').fetchone()[0]
        
        # محاسبه offset
        offset = (page - 1) * per_page
        
        # دریافت لاگ‌ها با صفحه‌بندی
        logs = conn.execute('''
            SELECT dl.*, u1.username as deleted_by_username
            FROM deletion_logs dl
            JOIN users u1 ON dl.deleted_by_user_id = u1.id
            ORDER BY dl.deleted_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset)).fetchall()
        
        # تبدیل تاریخ‌ها به شمسی
        from utils.date_utils import gregorian_to_jalali
        logs_with_jalali = []
        for log in logs:
            log_dict = dict(log)
            if log['deleted_at']:
                jalali_datetime = gregorian_to_jalali(log['deleted_at'])
                parts = jalali_datetime.split(' ')
                log_dict['deleted_at_jalali_date'] = parts[0]
                log_dict['deleted_at_jalali_time'] = parts[1] if len(parts) > 1 else '00:00:00'
            logs_with_jalali.append(log_dict)
        
        pagination = {
            'total': total,
            'per_page': per_page,
            'current_page': page,
            'total_pages': (total + per_page - 1) // per_page
        }
        
        return render_template('deletion_logs.html', 
                             logs=logs_with_jalali, 
                             pagination=pagination)
        
    except Exception as e:
        flash(f'خطا در دریافت لاگ‌ها: {str(e)}', 'error')
        return render_template('deletion_logs.html', logs=[], pagination={})
    finally:
        conn.close()