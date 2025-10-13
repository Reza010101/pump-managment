"""
اسکریپت ارتقاء دیتابیس برای افزودن قابلیت حذف رکوردها
"""
import sqlite3

def migrate_database():
    conn = sqlite3.connect('pump_management.db')
    cursor = conn.cursor()
    
    try:
        print("🔍 بررسی وجود جدول deletion_logs...")
        
        # بررسی آیا جدول از قبل وجود دارد
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='deletion_logs'
        """)
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("✅ جدول deletion_logs از قبل وجود دارد")
        else:
            # ایجاد جدول جدید برای لاگ حذف
            cursor.execute('''
                CREATE TABLE deletion_logs (
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
        
        # گزارش وضعیت داده‌ها
        cursor.execute("SELECT COUNT(*) FROM pump_history")
        history_count = cursor.fetchone()[0]
        print(f"✅ {history_count} رکورد در pump_history موجود است")
        
        cursor.execute("SELECT COUNT(*) FROM pumps") 
        pumps_count = cursor.fetchone()[0]
        print(f"✅ {pumps_count} پمپ در سیستم موجود است")
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM deletion_logs")
            logs_count = cursor.fetchone()[0]
            print(f"✅ {logs_count} لاگ حذف در سیستم موجود است")
        
        conn.commit()
        print("🎉 ارتقاء دیتابیس با موفقیت انجام شد")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ خطا در ارتقاء دیتابیس: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()