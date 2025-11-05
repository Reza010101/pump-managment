from .models import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

def get_all_users():
    """دریافت لیست تمام کاربران"""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_date DESC').fetchall()
    conn.close()
    return users

def get_user_by_credentials(username, password):
    """احراز هویت کاربر"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    # اگر کاربر یافت شد، پسورد هش‌شده را بررسی کن
    if user and check_password_hash(user['password'], password):
        return user
    return None

def create_new_user(username, password, full_name, role):
    """ایجاد کاربر جدید"""
    conn = get_db_connection()
    
    try:
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        
        if existing_user:
            return {'success': False, 'error': 'نام کاربری قبلاً استفاده شده است!'}
        
        # هش کردن پسورد قبل از ذخیره
        hashed = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
            (username, hashed, full_name, role)
        )
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'کاربر {full_name} با موفقیت ایجاد شد!'}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': f'خطا در ایجاد کاربر: {str(e)}'}

def delete_existing_user(user_id):
    """حذف کاربر"""
    conn = get_db_connection()
    
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'کاربر با موفقیت حذف شد!'}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': f'خطا در حذف کاربر: {str(e)}'}

def change_user_password(user_id, current_password, new_password):
    """تغییر رمز عبور کاربر"""
    conn = get_db_connection()
    
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user or not check_password_hash(user['password'], current_password):
            return {'success': False, 'error': 'پسورد فعلی اشتباه است!'}

        new_hashed = generate_password_hash(new_password)
        conn.execute(
            'UPDATE users SET password = ?, last_password_change = CURRENT_TIMESTAMP WHERE id = ?',
            (new_hashed, user_id)
        )
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'پسورد با موفقیت تغییر کرد!'}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': f'خطا در تغییر پسورد: {str(e)}'}