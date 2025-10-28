"""
Migration 009: Remove description, parts_used, duration_minutes and new_status from wells_history
This migration will:
 - create a backup of the DB file
 - recreate wells_history without the removed columns
 - copy existing relevant columns into the new table
 - drop the old table and rename the new one

Note: SQLite doesn't support DROP COLUMN directly, so we recreate the table.
"""
import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'pump_management.db')
# the relative path above resolves to project root; adjust if needed
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'pump_management.db'))

backup_path = f"{DB_PATH}.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"

print(f"🔍 Looking for DB at: {DB_PATH}")
if not os.path.exists(DB_PATH):
    print("❌ Database file not found, aborting migration 009")
    raise SystemExit(1)

print(f"📦 Creating DB backup: {backup_path}")
shutil.copy2(DB_PATH, backup_path)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    print("🚧 Running migration 009: remove maintenance text fields from wells_history...")
    c.execute('PRAGMA foreign_keys = OFF;')
    c.execute('BEGIN;')

    # Create new wells_history without description/parts_used/duration_minutes/new_status
    c.execute('''
        CREATE TABLE IF NOT EXISTS wells_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER NOT NULL,
            changed_by_user_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            changed_fields TEXT,
            changed_values TEXT,
            full_snapshot TEXT,
            recorded_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            recorded_date DATE,
            reason TEXT,
            FOREIGN KEY (well_id) REFERENCES wells(id),
            FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
        );
    ''')

    # Copy existing data (omit removed columns)
    c.execute('''
        INSERT INTO wells_history_new (id, well_id, changed_by_user_id, change_type, changed_fields, changed_values, full_snapshot, recorded_time, recorded_date, reason)
        SELECT id, well_id, changed_by_user_id, change_type, changed_fields, changed_values, full_snapshot, recorded_time, recorded_date, reason
        FROM wells_history;
    ''')

    # Drop old table and rename new
    c.execute('DROP TABLE wells_history;')
    c.execute('ALTER TABLE wells_history_new RENAME TO wells_history;')

    c.execute('COMMIT;')
    c.execute('PRAGMA foreign_keys = ON;')
    print('✅ Migration 009 applied: removed description/parts_used/duration_minutes/new_status from wells_history')

except Exception as e:
    print(f"❌ Migration 009 failed: {e}")
    try:
        c.execute('ROLLBACK;')
    except:
        pass
    raise
finally:
    conn.close()
