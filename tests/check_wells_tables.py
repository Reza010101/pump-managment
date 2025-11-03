import sqlite3

def check_tables():
    conn = sqlite3.connect('pump_management.db')
    cursor = conn.cursor()
    
    try:
        print("🔍 بررسی جدول‌های ایجاد شده...")
        
        # بررسی وجود جدول‌ها
        tables = ['wells']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            result = cursor.fetchone()
            if result:
                print(f"✅ جدول {table} وجود دارد")
                
                # تعداد رکوردها
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - تعداد رکوردها: {count}")
            else:
                print(f"❌ جدول {table} وجود ندارد")
        
        # بررسی ساختار جدول wells
        print("\n📋 ساختار جدول wells:")
        cursor.execute("PRAGMA table_info(wells)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ خطا در بررسی: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()
