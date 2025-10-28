"""
Migration 005: Create wells_history table
This adds the wells_history table used for auditing well changes during maintenance.
"""
import sqlite3
import os


def migrate():
    db_path = 'pump_management.db'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_full_path = os.path.join(project_root, db_path)

    print(f"🔍 Looking for DB at: {db_full_path}")

    if not os.path.exists(db_full_path):
        print("❌ Database not found. Run create_database.py first or ensure DB exists.")
        return

    conn = sqlite3.connect(db_full_path)
    cursor = conn.cursor()

    try:
        print("🚀 Running migration 005: creating wells_history...")

        stmt = '''
        CREATE TABLE IF NOT EXISTS wells_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER NOT NULL,
            changed_by_user_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            changed_fields TEXT,
            description TEXT,
            parts_used TEXT,
            duration_minutes INTEGER,
            cost REAL,
            new_status TEXT,
            recorded_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (well_id) REFERENCES wells(id),
            FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
        );
        '''

        cursor.execute(stmt)
        conn.commit()
        print("✅ wells_history table ensured")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
