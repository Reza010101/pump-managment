import sqlite3
import os
from datetime import datetime

def create_database():
    # اتصال به دیتابیس - اگر نبود ساخته میشه
    conn = sqlite3.connect('pump_management.db')
    cursor = conn.cursor()
    
    print("📦 در حال ساخت دیتابیس و جداول...")
    
    # جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_password_change TIMESTAMP  
        )
    ''')
    
    # جدول پمپ‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pumps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pump_number INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            status BOOLEAN DEFAULT 0,  -- 0: خاموش, 1: روشن
            last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول تاریخچه تغییرات پمپ‌ها - نسخه آپدیت شده با دو فیلد زمان
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pump_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pump_id INTEGER,
            user_id INTEGER,
            action TEXT NOT NULL,  -- 'ON' یا 'OFF'
            event_time TIMESTAMP,  -- زمان واقعی رویداد (جدید)
            recorded_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- زمان ثبت در سیستم (جدید)
            reason TEXT,           -- علت تغییر وضعیت
            notes TEXT,            -- توضیحات اضافی
            manual_time BOOLEAN DEFAULT FALSE,  -- آیا زمان دستی وارد شده؟
            FOREIGN KEY (pump_id) REFERENCES pumps (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ایجاد کاربر پیشفرض
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, full_name, role) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', '1234', 'مدیر سیستم', 'admin'))
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, full_name, role) 
        VALUES (?, ?, ?, ?)
    ''', ('user1', '1234', 'کاربر نمونه', 'user'))
    
    # ایجاد ۵۸ الکتروپمپ
    for i in range(1, 59):
        cursor.execute('''
            INSERT OR IGNORE INTO pumps (pump_number, name, location) 
            VALUES (?, ?, ?)
        ''', (i, f'الکتروپمپ {i}', f'موقعیت {i}'))
    
    conn.commit()
    conn.close()
    print("✅ دیتابیس و جداول با موفقیت ساخته شدند!")
    print("👤 کاربران پیشفرض:")
    print("   - admin / 1234 (مدیر)")
    print("   - user1 / 1234 (کاربر معمولی)")
    print("🆕 فیلدهای جدید اضافه شد:")
    print("   - event_time (زمان واقعی رویداد)")
    print("   - recorded_time (زمان ثبت در سیستم)")

def test_database():
    """تست اتصال به دیتابیس"""
    try:
        conn = sqlite3.connect('pump_management.db')
        cursor = conn.cursor()
        
        # تست تعداد پمپ‌ها
        cursor.execute('SELECT COUNT(*) FROM pumps')
        pump_count = cursor.fetchone()[0]
        
        # تست کاربران
        cursor.execute('SELECT username, role FROM users')
        users = cursor.fetchall()
        
        # تست ساختار جدول pump_history
        cursor.execute("PRAGMA table_info(pump_history)")
        columns = cursor.fetchall()
        print("📋 ستون‌های جدول pump_history:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        
        print(f"✅ تست دیتابیس موفق:")
        print(f"   تعداد پمپ‌ها: {pump_count}")
        print(f"   کاربران: {users}")
        
    except Exception as e:
        print(f"❌ خطا در تست دیتابیس: {e}")

def migrate_old_data_if_exists():
    """اگر داده قدیمی دارید، این تابع رو اجرا کنید (اختیاری)"""
    try:
        conn = sqlite3.connect('pump_management.db')
        cursor = conn.cursor()
        
        # بررسی آیا جدول pump_history قدیمی وجود دارد
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pump_history_old'")
        old_table_exists = cursor.fetchone()
        
        if old_table_exists:
            print("🔄 در حال مهاجرت داده‌های قدیمی...")
            
            # کپی داده‌ها از جدول قدیمی
            cursor.execute('''
                INSERT INTO pump_history 
                (pump_id, user_id, action, event_time, recorded_time, reason, notes, manual_time)
                SELECT pump_id, user_id, action, action_time, action_time, reason, notes, manual_time
                FROM pump_history_old
            ''')
            
            conn.commit()
            print(f"✅ {cursor.rowcount} رکورد قدیمی مهاجرت داده شد")
        else:
            print("ℹ️ داده قدیمی برای مهاجرت پیدا نشد")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ خطا در مهاجرت داده‌ها: {e}")

if __name__ == "__main__":
    # اگر دیتابیس قدیمی وجود دارد، پاکش کن
    if os.path.exists('pump_management.db'):
        choice = input("🗑️ دیتابیس قدیمی وجود دارد. آیا می‌خواهید پاک شود؟ (y/n): ")
        if choice.lower() == 'y':
            os.remove('pump_management.db')
            print("🗑️ دیتابیس قدیمی حذف شد")
        else:
            print("❌ عملیات لغو شد")
            exit()
    
    create_database()
    test_database()
    
    # اگر می‌خواهید داده‌های قدیمی رو مهاجرت بدید، این خط رو آنکامنت کنید
    # migrate_old_data_if_exists()