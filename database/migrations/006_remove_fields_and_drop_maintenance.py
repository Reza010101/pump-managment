"""
Migration 006: Remove unused wells columns, drop maintenance_operations, remove cost from wells_history

This migration performs the following safe steps for SQLite:
 - Creates backup of the database
 - Recreates `wells` without the columns: casing_type, current_cable_specs,
   well_installation_date, current_equipment_installation_date
 - Recreates `wells_history` without the `cost` column
 - Drops the `maintenance_operations` table

Note: This migration is destructive for the removed columns (their data is lost).
"""
import sqlite3
import os
import shutil
from datetime import datetime


def migrate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_path = os.path.join(project_root, 'pump_management.db')

    if not os.path.exists(db_path):
        print('Database not found at', db_path)
        return

    # backup
    bak_name = f"pump_management.db.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    bak_path = os.path.join(project_root, bak_name)
    shutil.copy2(db_path, bak_path)
    print('Backup created:', bak_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        print('Starting migration 006...')
        cur.execute('PRAGMA foreign_keys=OFF;')
        cur.execute('BEGIN TRANSACTION;')

        # 1) Recreate wells without the unused columns
        cur.execute('''
        CREATE TABLE IF NOT EXISTS wells_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_number INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            total_depth TEXT,
            pump_installation_depth TEXT,
            well_diameter TEXT,
            current_pump_brand TEXT,
            current_pump_model TEXT,
            current_pump_power TEXT,
            current_pump_phase TEXT,
            current_pipe_material TEXT,
            current_pipe_specs TEXT,
            current_pipe_diameter TEXT,
            current_pipe_length_m REAL,
            main_cable_specs TEXT,
            well_cable_specs TEXT,
            current_panel_specs TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # copy data (omit removed columns)
        cur.execute('''
        INSERT INTO wells_new (
            id, well_number, name, location, total_depth, pump_installation_depth,
            well_diameter, current_pump_brand, current_pump_model, current_pump_power,
            current_pump_phase, current_pipe_material, current_pipe_specs, current_pipe_diameter,
            current_pipe_length_m, main_cable_specs, well_cable_specs, current_panel_specs,
            status, notes, created_at, updated_at
        )
        SELECT
            id, well_number, name, location, total_depth, pump_installation_depth,
            well_diameter, current_pump_brand, current_pump_model, current_pump_power,
            current_pump_phase, current_pipe_material, current_pipe_specs, current_pipe_diameter,
            current_pipe_length_m, main_cable_specs, well_cable_specs, current_panel_specs,
            status, notes, created_at, updated_at
        FROM wells;
        ''')

        cur.execute('DROP TABLE IF EXISTS wells;')
        cur.execute('ALTER TABLE wells_new RENAME TO wells;')
        print('Recreated wells without unused columns')

        # 2) Recreate wells_history without cost column
        cur.execute('''
        CREATE TABLE IF NOT EXISTS wells_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id INTEGER NOT NULL,
            changed_by_user_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            changed_fields TEXT,
            description TEXT,
            parts_used TEXT,
            duration_minutes INTEGER,
            new_status TEXT,
            recorded_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (well_id) REFERENCES wells(id),
            FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
        );
        ''')

        cur.execute('''
        INSERT INTO wells_history_new (
            id, well_id, changed_by_user_id, change_type, changed_fields,
            description, parts_used, duration_minutes, new_status, recorded_time
        )
        SELECT id, well_id, changed_by_user_id, change_type, changed_fields,
               description, parts_used, duration_minutes, new_status, recorded_time
        FROM wells_history;
        ''')

        cur.execute('DROP TABLE IF EXISTS wells_history;')
        cur.execute('ALTER TABLE wells_history_new RENAME TO wells_history;')
        print('Recreated wells_history without cost column')

        # 3) Drop maintenance_operations table entirely
        cur.execute('DROP TABLE IF EXISTS maintenance_operations;')
        print('Dropped maintenance_operations table')

        cur.execute('COMMIT;')
        cur.execute('PRAGMA foreign_keys=ON;')
        print('Migration 006 completed successfully')

    except Exception as e:
        conn.rollback()
        print('Migration 006 failed:', e)
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
