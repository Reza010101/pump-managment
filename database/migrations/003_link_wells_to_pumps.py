# database/migrations/003_link_wells_to_pumps.py
"""
میگریشن ایجاد رابطه بین چاه‌ها و پمپ‌های موجود
Version: 003
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """ایجاد رابطه بین چاه‌ها و پمپ‌های موجود"""
    
    # مسیر دیتابیس
    db_path = 'pump_management.db'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_full_path = os.path.join(project_root, db_path)
    
    print(f"🔍 جستجوی دیتابیس در: {db_full_path}")
    
    # بررسی وجود دیتابیس
    if not os.path.exists(db_full_path):
        print("❌ دیتابیس وجود ندارد. ابتدا create_database.py را اجرا کنید.")
        return
    
    conn = sqlite3.connect(db_full_path)
    conn.row_factory = sqlite3.Row
    
    try:
        print("🚀 در حال ایجاد رابطه بین چاه‌ها و پمپ‌ها...")
        print("=" * 50)
        
        # 1. اضافه کردن فیلد pump_id به جدول wells
        print("📝 در حال اضافه کردن فیلد pump_id به جدول wells...")
        try:
            conn.execute('ALTER TABLE wells ADD COLUMN pump_id INTEGER REFERENCES pumps(id)')
            print("✅ فیلد pump_id اضافه شد")
        except Exception as e:
            print(f"⚠️ فیلد pump_id احتمالاً از قبل وجود دارد: {e}")
        
        # 2. بررسی وجود چاه‌ها
        existing_wells = conn.execute('SELECT COUNT(*) as count FROM wells').fetchone()['count']
        print(f"🔍 تعداد چاه‌های موجود: {existing_wells}")
        
        # 3. اگر چاهی وجود ندارد، چاه‌ها را ایجاد کن
        if existing_wells == 0:
            print("🏗️ در حال ایجاد چاه‌ها برای پمپ‌های موجود...")
            
            # دریافت لیست پمپ‌ها
            pumps = conn.execute('SELECT id, pump_number, name, location FROM pumps ORDER BY pump_number').fetchall()
            
            wells_created = 0
            for pump in pumps:
                try:
                    # ایجاد چاه برای هر پمپ
                    conn.execute('''
                        INSERT INTO wells (
                            well_number, name, location, pump_id, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pump['pump_number'],  # well_number = pump_number
                        f'چاه شماره {pump["pump_number"]}',  # name
                        pump['location'],     # location
                        pump['id'],           # pump_id
                        'active',             # status
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    wells_created += 1
                    print(f"✅ چاه برای پمپ {pump['pump_number']} ایجاد شد")
                    
                except Exception as e:
                    print(f"❌ خطا در ایجاد چاه برای پمپ {pump['pump_number']}: {e}")
            
            print(f"🎯 {wells_created} چاه ایجاد شد")
        
        else:
            print("🔗 در حال برقراری رابطه بین چاه‌ها و پمپ‌های موجود...")
            
            # برای چاه‌های موجود، رابطه با پمپ‌ها برقرار کن
            wells = conn.execute('SELECT id, well_number FROM wells WHERE pump_id IS NULL').fetchall()
            
            linked_wells = 0
            for well in wells:
                try:
                    # پیدا کردن پمپ با شماره مشابه
                    pump = conn.execute(
                        'SELECT id FROM pumps WHERE pump_number = ?', 
                        (well['well_number'],)
                    ).fetchone()
                    
                    if pump:
                        conn.execute(
                            'UPDATE wells SET pump_id = ? WHERE id = ?',
                            (pump['id'], well['id'])
                        )
                        linked_wells += 1
                        print(f"✅ چاه {well['well_number']} به پمپ {well['well_number']} متصل شد")
                    else:
                        print(f"⚠️ پمپ با شماره {well['well_number']} یافت نشد")
                        
                except Exception as e:
                    print(f"❌ خطا در اتصال چاه {well['well_number']}: {e}")
            
            print(f"🔗 {linked_wells} چاه به پمپ متصل شد")
        
        # 4. ایجاد ایندکس برای عملکرد بهتر
        print("📊 در حال ایجاد ایندکس‌ها...")
        try:
            conn.execute('CREATE INDEX IF NOT EXISTS idx_wells_pump_id ON wells(pump_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_wells_number ON wells(well_number)')
            print("✅ ایندکس‌ها ایجاد شدند")
        except Exception as e:
            print(f"⚠️ خطا در ایجاد ایندکس: {e}")
        
        # 5. گزارش نهایی
        print("-" * 50)
        print("📊 گزارش نهایی:")
        
        # تعداد چاه‌ها
        total_wells = conn.execute('SELECT COUNT(*) as count FROM wells').fetchone()['count']
        print(f"   • تعداد کل چاه‌ها: {total_wells}")
        
        # چاه‌های متصل شده
        linked_wells = conn.execute('SELECT COUNT(*) as count FROM wells WHERE pump_id IS NOT NULL').fetchone()['count']
        print(f"   • چاه‌های متصل به پمپ: {linked_wells}")
        
        # چاه‌های بدون اتصال
        unlinked_wells = conn.execute('SELECT COUNT(*) as count FROM wells WHERE pump_id IS NULL').fetchone()['count']
        print(f"   • چاه‌های بدون اتصال: {unlinked_wells}")
        
        # تعداد پمپ‌ها
        total_pumps = conn.execute('SELECT COUNT(*) as count FROM pumps').fetchone()['count']
        print(f"   • تعداد کل پمپ‌ها: {total_pumps}")
        
        conn.commit()
        print("🎉 میگریشن با موفقیت انجام شد!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ خطا در میگریشن: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()