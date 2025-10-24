"""
اسکریپت ایجاد دیتابیس کامل سیستم مدیریت پمپ‌ها
این فایل هم برای توسعه و هم برای تولید استفاده می‌شود
"""
import sqlite3
import os
from datetime import datetime

def create_tables(cursor):
    """ایجاد تمام جدول‌های سیستم"""
    
    # ۱. ایجاد جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_password_change DATETIME
        )
    ''')
    print("✅ جدول users ایجاد شد")
    
    # ۲. ایجاد جدول پمپ‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pumps (
            id INTEGER PRIMARY KEY,
            pump_number INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            status BOOLEAN DEFAULT 0,
            last_change DATETIME
        )
    ''')
    print("✅ جدول pumps ایجاد شد")
    
    # ۳. ایجاد جدول تاریخچه پمپ‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pump_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pump_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            event_time DATETIME NOT NULL,
            recorded_time DATETIME NOT NULL,
            reason TEXT NOT NULL,
            notes TEXT,
            manual_time BOOLEAN DEFAULT 0,
            FOREIGN KEY (pump_id) REFERENCES pumps(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✅ جدول pump_history ایجاد شد")
    
    # ۴. ایجاد جدول لاگ حذف (جدید)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deletion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deleted_record_id INTEGER,
            pump_id INTEGER,
            pump_number INTEGER,
            original_action TEXT,
            original_event_time DATETIME,
            original_reason TEXT,
            original_notes TEXT,
            original_user_id INTEGER,
            original_user_name TEXT,
            deleted_by_user_id INTEGER,
            deleted_by_user_name TEXT,
            deletion_reason TEXT NOT NULL,
            deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ جدول deletion_logs ایجاد شد")
    # ایجاد جدول‌های مدیریت چاه‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_number INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            total_depth TEXT,
            pump_installation_depth TEXT,
            well_diameter TEXT,
            current_pump_brand TEXT,
            current_pump_model TEXT,
            current_pump_power TEXT,
            current_pump_phase TEXT,
            current_pipe_material TEXT,
            current_pipe_specs TEXT,
            current_pipe_diameter TEXT,
            current_pipe_length_m REAL,
            main_cable_specs TEXT,
            well_cable_specs TEXT,
            current_panel_specs TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ جدول wells ایجاد شد")

    # جدول تاریخچه تغییرات چاه (برای audit)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wells_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER NOT NULL,
            changed_by_user_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            changed_fields TEXT,
            changed_values TEXT,
            full_snapshot TEXT,
            recorded_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            recorded_date DATE,
            reason TEXT,
            FOREIGN KEY (well_id) REFERENCES wells(id),
            FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
        )
    ''')
    print("✅ جدول wells_history ایجاد شد")
    # maintenance_operations table intentionally not created. Use wells_history for audit instead.

def insert_sample_data(cursor):
    """درج داده‌های نمونه"""
    
    # کاربران پیشفرض
    cursor.executemany('''
        INSERT INTO users (username, password, full_name, role) 
        VALUES (?, ?, ?, ?)
    ''', [
        ('admin', '1234', 'مدیر سیستم', 'admin'),
        ('user1', '1234', 'کاربر نمونه', 'user')
    ])
    print("✅ کاربران پیشفرض اضافه شدند")
    
    # پمپ‌ها
    pumps_data = []
    for i in range(1, 59):
        pumps_data.append((
            i, i, f'پمپ شماره {i}', f'سالن {((i-1)//10)+1}'
        ))
    
    cursor.executemany('''
        INSERT INTO pumps (id, pump_number, name, location) 
        VALUES (?, ?, ?, ?)
    ''', pumps_data)
    print("✅ ۵۸ پمپ اضافه شدند")

def main():
    """تابع اصلی ایجاد دیتابیس"""
    conn = sqlite3.connect('pump_management.db')
    conn.row_factory = sqlite3.Row
    
    try:
        print("🚀 در حال ایجاد دیتابیس کامل سیستم مدیریت پمپ‌ها...")
        print("=" * 50)
        
        # ایجاد جدول‌ها
        create_tables(conn)
        print("-" * 30)
        
        # درج داده‌های نمونه
        insert_sample_data(conn)
        print("-" * 30)
        
        conn.commit()
        
        # گزارش نهایی
        print("🎉 دیتابیس با موفقیت ایجاد شد!")
        print("📊 وضعیت نهایی:")
        for table in ['users', 'pumps', 'pump_history', 'deletion_logs']:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            print(f"   - {table}: {count} رکورد")
            
        print("\n👤 کاربران پیشفرض:")
        print("   - admin / 1234 (مدیر سیستم)")
        print("   - user1 / 1234 (کاربر معمولی)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ خطا در ایجاد دیتابیس: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()