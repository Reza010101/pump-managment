#!/usr/bin/env python3
"""
ساخت دیتابیس برای ساختار جدید
"""
import sqlite3
import os
from datetime import datetime

def create_database():
    """ایجاد دیتابیس و جداول"""
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
            status BOOLEAN DEFAULT 0,
            last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول تاریخچه تغییرات پمپ‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pump_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pump_id INTEGER,
            user_id INTEGER,
            action TEXT NOT NULL,
            event_time TIMESTAMP,
            recorded_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            notes TEXT,
            manual_time BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (pump_id) REFERENCES pumps (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ایجاد کاربران پیشفرض
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

if __name__ == "__main__":
    if os.path.exists('pump_management.db'):
        response = input("🗑️ دیتابیس قدیمی وجود دارد. آیا می‌خواهید جایگزین شود؟ (y/n): ")
        if response.lower() != 'y':
            print("❌ عملیات لغو شد")
            exit()
    
    create_database()