import sqlite3
import os

def check_database_schema():
    """
    Provides a comprehensive overview of the database schema, including tables,
    record counts, column details, and existence checks for required tables.
    """
    db_path = 'pump_management.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Error: Database file not found at '{os.path.abspath(db_path)}'")
        return

    print(f"🔍 Connecting to database: {db_path}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- 1. Database Overview ---
        print("="*60)
        print("📊 DATABASE OVERVIEW")
        print("="*60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("❌ No user-defined tables found in the database.")
            return

        print(f"📁 Found {len(tables)} tables:")
        for table_name in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        print("\n" + "-"*60 + "\n")

        # --- 2. Check for required tables ---
        print("✅ CHECKING FOR REQUIRED TABLES")
        required_tables = [
            'users', 'wells', 'pumps', 'maintenance_operations', 
            'wells_history', 'pump_history', 'deletion_logs'
        ]
        missing_tables = [tbl for tbl in required_tables if tbl not in tables]
        
        if missing_tables:
            print(f"  - ❌ Missing required tables: {', '.join(missing_tables)}")
        else:
            print("  - ✅ All required tables are present.")
        
        print("\n" + "="*60)
        print("🏛️ DETAILED TABLE SCHEMAS")
        print("="*60)

        # --- 3. Detailed Schema for Each Table ---
        for table_name in sorted(tables):
            print(f"\n📜 Table: {table_name}")
            print("-" * (len(table_name) + 8))
            
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()
            
            # Header
            print(f"{'ID':<4}{'Name':<30}{'Type':<15}{'Not Null':<10}{'PK':<5}")
            print(f"{'-'*3:<4}{'-'*29:<30}{'-'*14:<15}{'-'*9:<10}{'-'*4:<5}")

            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                print(f"{str(col_id):<4}{name:<30}{col_type:<15}{'YES' if not_null else 'NO':<10}{'YES' if pk else 'NO':<5}")
        
        print("\n" + "="*60)
        print("✨ Database check complete.")
        print("="*60)

    except sqlite3.Error as e:
        print(f"❌ An SQLite error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("\n🔌 Database connection closed.")

if __name__ == "__main__":
    check_database_schema()