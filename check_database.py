import sqlite3

def check_database():
    conn = sqlite3.connect('pump_management.db')
    cursor = conn.cursor()
    
    try:
        print("🔍 بررسی کامل دیتابیس...")
        
        # لیست تمام جدول‌ها
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📁 جدول‌های موجود ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} رکورد")
            
        # بررسی وجود جدول‌های اصلی
        required_tables = ['pumps', 'pump_history', 'users']
        missing_tables = []
        
        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ جدول‌های گمشده: {', '.join(missing_tables)}")
        else:
            print("✅ تمام جدول‌های اصلی موجود هستند")
            
    except Exception as e:
        print(f"❌ خطا در بررسی دیتابیس: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()