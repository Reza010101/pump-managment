#!/usr/bin/env python3
"""
بررسی وضعیت دیتابیس
"""
import sqlite3
import os

def check_database():
    if not os.path.exists('pump_management.db'):
        print("❌ فایل دیتابیس وجود ندارد")
        return False
    
    try:
        conn = sqlite3.connect('pump_management.db')
        cursor = conn.cursor()
        
        # بررسی تعداد پمپ‌ها
        cursor.execute('SELECT COUNT(*) FROM pumps')
        pump_count = cursor.fetchone()[0]
        
        # بررسی کاربران
        cursor.execute('SELECT username, role FROM users')
        users = cursor.fetchall()
        
        # بررسی تاریخچه
        cursor.execute('SELECT COUNT(*) FROM pump_history')
        history_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ دیتابیس موجود است")
        print(f"📊 تعداد پمپ‌ها: {pump_count}")
        print(f"👤 کاربران: {[f'{u[0]}({u[1]})' for u in users]}")
        print(f"📈 تعداد رویدادهای تاریخچه: {history_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطا در بررسی دیتابیس: {e}")
        return False

if __name__ == "__main__":
    check_database()