import sqlite3
from datetime import datetime

def get_db_connection():
    """ایجاد اتصال به دیتابیس"""
    conn = sqlite3.connect('pump_management.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_pump_by_id(pump_id):
    """دریافت اطلاعات یک پمپ بر اساس ID"""
    conn = get_db_connection()
    pump = conn.execute('SELECT * FROM pumps WHERE id = ?', (pump_id,)).fetchone()
    conn.close()
    return dict(pump) if pump else None

def get_all_pumps():
    """دریافت لیست تمام پمپ‌ها"""
    conn = get_db_connection()
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
    return pumps

def get_user_by_credentials(username, password):
    """احراز هویت کاربر"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?', 
        (username, password)
    ).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """دریافت اطلاعات کاربر بر اساس ID"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user