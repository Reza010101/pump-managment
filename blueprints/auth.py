from flask import Blueprint, render_template, request, session, redirect, flash
from database.users import get_user_by_credentials
from database.operations import update_pump_current_status

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = get_user_by_credentials(username, password)
        
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

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت خارج شدید!', 'success')
    return redirect('/login')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # اعتبارسنجی
        if new_password != confirm_password:
            flash('پسورد جدید و تکرار آن مطابقت ندارند!', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 4:
            flash('پسورد جدید باید حداقل ۴ کاراکتر باشد!', 'error')
            return render_template('change_password.html')
        
        # تغییر پسورد
        from database.users import change_user_password
        result = change_user_password(
            user_id=session['user_id'],
            current_password=current_password,
            new_password=new_password
        )
        
        if result['success']:
            flash('پسورد با موفقیت تغییر کرد!', 'success')
            return redirect('/')
        else:
            flash(result['error'], 'error')
            return render_template('change_password.html')
    
    return render_template('change_password.html')