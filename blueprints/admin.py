from flask import Blueprint, render_template, request, session, redirect, flash, send_file
from database.users import get_all_users, create_new_user, delete_existing_user
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
    
    # این قسمت بعداً تکمیل می‌شود
    return render_template('import_history.html')

@admin_bp.route('/admin/download-sample')
def download_sample():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    
    return create_sample_excel_file()