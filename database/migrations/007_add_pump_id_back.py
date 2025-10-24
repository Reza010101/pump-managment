"""
Migration 007: Re-add pump_id to wells and populate from pump_number where possible

This migration will:
 - Add a `pump_id` column to `wells` if it does not exist
 - Populate `pump_id` by matching `wells.well_number` to `pumps.pump_number`
 - Create an index on `wells(pump_id)`
"""
import sqlite3
import os


def migrate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_path = os.path.join(project_root, 'pump_management.db')

    if not os.path.exists(db_path):
        print('Database not found at', db_path)
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        print('Running migration 007: ensure pump_id on wells')
        # add column if missing (SQLite will raise if exists)
        try:
            cur.execute('ALTER TABLE wells ADD COLUMN pump_id INTEGER REFERENCES pumps(id)')
            print('Added pump_id column to wells')
        except Exception as e:
            print('pump_id column may already exist:', e)

        # populate pump_id by matching well_number -> pumps.pump_number
        cur.execute('''
            UPDATE wells
            SET pump_id = (
                SELECT id FROM pumps WHERE pumps.pump_number = wells.well_number
            )
            WHERE pump_id IS NULL;
        ''')
        conn.commit()

        # create index
        cur.execute('CREATE INDEX IF NOT EXISTS idx_wells_pump_id ON wells(pump_id)')
        conn.commit()
        print('Populated pump_id and created index')

    except Exception as e:
        conn.rollback()
        print('Migration 007 failed:', e)
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
