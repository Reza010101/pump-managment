
import sqlite3
import os
import shutil
from datetime import datetime

# Define the path to the database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'pump_management.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'database_backups')

def backup_database():
    """Creates a backup of the database file."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file_name = f'pump_management.db.bak_{timestamp}'
    backup_path = os.path.join(BACKUP_DIR, backup_file_name)
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"Successfully created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def migrate():
    """
    Upgrades the 'wells_history' table to include operation details and removes redundant columns.
    - Adds: operation_type, operation_date, performed_by
    - Removes: recorded_date
    """
    print("Starting migration to upgrade 'wells_history' table...")

    if not backup_database():
        print("Migration aborted due to backup failure.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Create the new table with the desired schema
        print("Step 1: Creating the new 'wells_history_new' table...")
        cursor.execute("""
        CREATE TABLE wells_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER NOT NULL,
            changed_by_user_id INTEGER NOT NULL,
            
            -- New columns for operation details
            operation_type TEXT,
            operation_date DATE,
            performed_by TEXT,

            -- Existing columns for tracking changes
            change_type TEXT,
            changed_fields TEXT,
            changed_values TEXT,
            description TEXT,
            parts_used TEXT,
            duration_minutes INTEGER,
            new_status TEXT,
            reason TEXT,
            full_snapshot TEXT,
            
            -- System timestamp (replaces recorded_date and recorded_time)
            recorded_time DATETIME,

            FOREIGN KEY (well_id) REFERENCES wells(id),
            FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
        )
        """)
        print("New table 'wells_history_new' created successfully.")

        # 2. Get the list of columns from the old table to map data
        cursor.execute("PRAGMA table_info(wells_history)")
        old_columns = [row[1] for row in cursor.fetchall()]
        
        # Define columns to copy from the old table to the new one
        # We are excluding 'recorded_date'
        columns_to_copy = [col for col in old_columns if col != 'recorded_date']
        columns_str = ", ".join(columns_to_copy)

        # 3. Copy data from the old table to the new table
        print(f"Step 2: Copying data from 'wells_history' to 'wells_history_new'...")
        print(f"   - Columns being copied: {columns_str}")
        cursor.execute(f"INSERT INTO wells_history_new ({columns_str}) SELECT {columns_str} FROM wells_history")
        print(f"   - {cursor.rowcount} rows copied successfully.")

        # 4. Drop the old table
        print("Step 3: Dropping the old 'wells_history' table...")
        cursor.execute("DROP TABLE wells_history")
        print("   - Old 'wells_history' table dropped.")

        # 5. Rename the new table to the original name
        print("Step 4: Renaming 'wells_history_new' to 'wells_history'...")
        cursor.execute("ALTER TABLE wells_history_new RENAME TO wells_history")
        print("   - Table renamed successfully.")

        # Commit the changes
        conn.commit()
        print("\nMigration completed successfully!")
        print("Table 'wells_history' has been upgraded.")

    except sqlite3.Error as e:
        print(f"An error occurred during migration: {e}")
        if conn:
            conn.rollback()
            print("Changes have been rolled back.")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate()
