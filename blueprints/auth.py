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