from flask import Flask, render_template, request, redirect, session, jsonify, flash
import sqlite3
from datetime import datetime, timedelta
import os
from date_converter import gregorian_to_jalali, jalali_to_gregorian


app = Flask(__name__)
app.secret_key = 'pump_management_secret_key_2024'

# تابع کمکی برای اتصال به دیتابیس
def get_db_connection():
    conn = sqlite3.connect('pump_management.db')
    conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
    return conn

# صفحه لاگین
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
            flash('با موفقیت وارد شدید!', 'success')
            return redirect('/')
        else:
            flash('نام کاربری یا رمز عبور اشتباه است!', 'error')
    
    return render_template('login.html')

# صفحه اصلی - نمایش پمپ‌ها
@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    
    # دریافت وضعیت پمپ‌ها
    pumps = conn.execute('''
        SELECT p.*, 
               (SELECT action FROM pump_history 
                WHERE pump_id = p.id 
                ORDER BY action_time DESC LIMIT 1) as last_action
        FROM pumps p 
        ORDER BY p.pump_number
    ''').fetchall()
    
    conn.close()
    
    # تبدیل تاریخ‌ها به شمسی 
    pumps_with_jalali = []
    for pump in pumps:
        pump_dict = dict(pump)
        if pump['last_change']:
            pump_dict['last_change_jalali'] = gregorian_to_jalali(pump['last_change'])
        else:
            pump_dict['last_change_jalali'] = 'بدون تاریخچه'
        pumps_with_jalali.append(pump_dict)
    
    return render_template('dashboard.html', pumps=pumps_with_jalali)  # 🆕 pumps_with_jalali

# خروج
@app.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت خارج شدید!', 'success')
    return redirect('/login')
# تغییر وضعیت پمپ با جزئیات
@app.route('/pump/change-status', methods=['POST'])
def change_pump_status_detailed():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    data = request.get_json()
    pump_id = data.get('pump_id')
    action = data.get('action')
    reason = data.get('reason')
    notes = data.get('notes', '')
    action_date_jalali = data.get('action_date_jalali')  # تاریخ شمسی از کاربر
    action_time = data.get('action_time')
    manual_time = data.get('manual_time', False)
    
    conn = get_db_connection()
    
    try:
        # بررسی وضعیت فعلی پمپ
        current_pump = conn.execute(
            'SELECT status FROM pumps WHERE id = ?', (pump_id,)
        ).fetchone()
        
        if not current_pump:
            return jsonify({'success': False, 'error': 'پمپ پیدا نشد'})
        
        current_status = current_pump['status']
        new_status = True if action == 'on' else False
        
        # جلوگیری از تغییر تکراری
        if current_status == new_status:
            return jsonify({
                'success': False, 
                'error': f'پمپ در حال حاضر {"روشن" if current_status else "خاموش"} است'
            })
        
        # بررسی دسترسی کاربر برای تاریخ دستی
        if manual_time and session['role'] != 'admin':
            return jsonify({
                'success': False, 
                'error': 'شما مجوز ثبت تاریخ دستی ندارید'
            })
        
        # آماده کردن timestamp
        if manual_time and action_date_jalali and action_time:
        # تبدیل شمسی به میلادی
            jalali_datetime_str = f"{action_date_jalali} {action_time}:00"
            action_timestamp = jalali_to_gregorian(jalali_datetime_str)  # از date_converter استفاده میکنه
        else:
            action_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # آپدیت وضعیت پمپ
        conn.execute(
            'UPDATE pumps SET status = ?, last_change = ? WHERE id = ?',
            (new_status, action_timestamp, pump_id)
        )
        
        # ثبت در تاریخچه با جزئیات
        conn.execute(
            '''INSERT INTO pump_history 
               (pump_id, user_id, action, action_time, reason, notes, manual_time) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (pump_id, session['user_id'], action.upper(), action_timestamp, 
             reason, notes, manual_time)
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


# صفحه گزارش تاریخی (موقت)
@app.route('/report/history')
def history_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    return "صفحه گزارش تاریخی - به زودی..."

# صفحه ساعات کارکرد (موقت)
@app.route('/report/hours')
def hours_report():
    if 'user_id' not in session:
        return redirect('/login')
    
    return "صفحه ساعات کارکرد - به زودی..."
# صفحه مدیریت کاربران
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

# تغییر پسورد
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        conn = get_db_connection()
        
        # بررسی پسورد فعلی
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
        
        # آپدیت پسورد
        conn.execute(
            'UPDATE users SET password = ?, last_password_change = CURRENT_TIMESTAMP WHERE id = ?',
            (new_password, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        flash('پسورد با موفقیت تغییر کرد!', 'success')
        return redirect('/')
    
    return render_template('change_password.html')

# ایجاد کاربر جدید (فقط مدیر)
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
            # بررسی وجود کاربر
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            if existing_user:
                flash('نام کاربری قبلاً استفاده شده است!', 'error')
                return redirect('/admin/create-user')
            
            # ایجاد کاربر جدید
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

# حذف کاربر (فقط مدیر)
@app.route('/admin/delete-user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    # جلوگیری از حذف خود
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

if __name__ == '__main__':
    # مطمئن شو دیتابیس وجود دارد
    if not os.path.exists('pump_management.db'):
        print("⚠️database dont exist , please run database.py")
        exit(1)
    
    print("🚀 server is running...")
    print("📧 for enter: http://localhost:5000/login")
    print("   users:")
    print("   - admin / 1234 (admin)")
    print("   - user1 / 1234 (user)")
    
    app.run(debug=True, host='0.0.0.0', port=5000)