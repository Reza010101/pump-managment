"""
Migration برای ایجاد سیستم مدیریت چاه‌ها
Version: 002
"""

import sqlite3
import os

def migrate():
    """اضافه کردن جدول‌های wells و maintenance_operations"""
    
    # 🎯 **اصلاح مسیر دیتابیس - استفاده از مسیر نسبی صحیح**
    db_path = 'pump_management.db'  # در پوشه اصلی پروژه
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_full_path = os.path.join(project_root, db_path)
    
    print(f"🔍 جستجوی دیتابیس در: {db_full_path}")
    
    # بررسی وجود دیتابیس
    if not os.path.exists(db_full_path):
        print("❌ دیتابیس وجود ندارد. ابتدا create_database.py را اجرا کنید.")
        print("💡 دستور: python create_database.py")
        return
    
    conn = sqlite3.connect(db_full_path)
    
    try:
        print("🚀 در حال ایجاد جدول‌های مدیریت چاه‌ها...")
        
        # ۱. ایجاد جدول wells
        conn.execute('''
            CREATE TABLE IF NOT EXISTS wells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                well_number INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                
                -- مشخصات فنی چاه
                total_depth TEXT,
                pump_installation_depth TEXT,
                well_diameter TEXT,
                casing_type TEXT,
                
                -- مشخصات پمپ فعلی
                current_pump_brand TEXT,
                current_pump_model TEXT,
                current_pump_power TEXT,
                current_pump_phase TEXT,
                
                -- مشخصات کابل
                current_cable_specs TEXT,
                
                -- مشخصات لوله
                current_pipe_material TEXT,
                current_pipe_specs TEXT,
                
                -- مشخصات تابلو
                current_panel_specs TEXT,
                
                -- تاریخ‌ها
                well_installation_date DATE,
                current_equipment_installation_date DATE,
                
                -- وضعیت
                status TEXT DEFAULT 'active',
                
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ جدول wells ایجاد شد")
        
        # ۲. ایجاد جدول maintenance_operations
        conn.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                well_id INTEGER NOT NULL,
                recorded_by_user_id INTEGER NOT NULL,
                
                -- نوع و تاریخ عملیات
                operation_type TEXT NOT NULL,
                operation_date DATE NOT NULL,
                operation_time TIME,
                
                -- توضیحات
                description TEXT NOT NULL,
                parts_used TEXT,
                
                -- اطلاعات اجرایی
                duration_minutes INTEGER,
                performed_by TEXT,
                
                -- وضعیت
                status TEXT DEFAULT 'completed',
                
                notes TEXT,
                
                FOREIGN KEY (well_id) REFERENCES wells(id),
                FOREIGN KEY (recorded_by_user_id) REFERENCES users(id)
            )
        ''')
        print("✅ جدول maintenance_operations ایجاد شد")
        
        # ۳. ایجاد ایندکس برای عملکرد بهتر
        conn.execute('CREATE INDEX IF NOT EXISTS idx_wells_number ON wells(well_number)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_well_id ON maintenance_operations(well_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance_operations(operation_date)')
        print("✅ ایندکس‌ها ایجاد شدند")
        
        conn.commit()
        print("🎯 میگریشن جدول‌های مدیریت چاه‌ها با موفقیت انجام شد")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ خطا در میگریشن: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()