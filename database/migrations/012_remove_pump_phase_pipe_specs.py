
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
    Migrates the 'wells' table to remove 'current_pump_phase' and 'current_pipe_specs' columns.
    This is done by creating a new table, copying the data, dropping the old table,
    and renaming the new one.
    """
    print("Starting migration to remove 'current_pump_phase' and 'current_pipe_specs' from 'wells' table...")

    if not backup_database():
        print("Migration aborted due to backup failure.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Create the new table without the specified columns
        print("Step 1: Creating the new 'wells_new' table...")
        cursor.execute("""
        CREATE TABLE wells_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            total_depth REAL,
            pump_installation_depth REAL,
            well_diameter REAL,
            current_pump_brand TEXT,
            current_pump_model TEXT,
            current_pump_power TEXT,
            current_pipe_material TEXT,
            current_pipe_diameter TEXT,
            current_pipe_length_m REAL,
            main_cable_specs TEXT,
            well_cable_specs TEXT,
            current_panel_specs TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pump_id INTEGER,
            FOREIGN KEY (pump_id) REFERENCES pumps(id)
        )
        """)
        print("New table 'wells_new' created successfully.")

        # 2. Get the list of columns from the old table to ensure correct mapping
        cursor.execute("PRAGMA table_info(wells)")
        old_columns = [row[1] for row in cursor.fetchall()]
        
        # Define columns to keep and copy
        columns_to_copy = [
            'id', 'well_number', 'name', 'location', 'total_depth', 'pump_installation_depth', 
            'well_diameter', 'current_pump_brand', 'current_pump_model', 'current_pump_power', 
            'current_pipe_material', 'current_pipe_diameter', 'current_pipe_length_m', 
            'main_cable_specs', 'well_cable_specs', 'current_panel_specs', 'status', 'notes', 
            'created_at', 'updated_at', 'pump_id'
        ]
        
        # Filter columns that actually exist in the old table
        final_columns = [col for col in columns_to_copy if col in old_columns]
        columns_str = ", ".join(final_columns)

        # 3. Copy data from the old table to the new table
        print(f"Step 2: Copying data from 'wells' to 'wells_new' for columns: {columns_str}...")
        cursor.execute(f"INSERT INTO wells_new ({columns_str}) SELECT {columns_str} FROM wells")
        print(f"{cursor.rowcount} rows copied successfully.")

        # 4. Drop the old table
        print("Step 3: Dropping the old 'wells' table...")
        cursor.execute("DROP TABLE wells")
        print("Old 'wells' table dropped.")

        # 5. Rename the new table to the original name
        print("Step 4: Renaming 'wells_new' to 'wells'...")
        cursor.execute("ALTER TABLE wells_new RENAME TO wells")
        print("Table renamed successfully.")

        # Commit the changes
        conn.commit()
        print("\nMigration completed successfully!")
        print("Columns 'current_pump_phase' and 'current_pipe_specs' have been removed from the 'wells' table.")

    except sqlite3.Error as e:
        print(f"An error occurred during migration: {e}")
        if conn:
            conn.rollback()
            print("Changes have been rolled back.")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This allows the script to be run directly
    migrate()
