"""
Migration 008
Extend `wells_history` to store recorded_date, reason, changed_values and full_snapshot.
This migration is non-destructive: it adds new nullable columns to the existing table.
"""
import sqlite3
import os
from datetime import datetime


def run(db_path: str):
    print(f"🔍 Looking for DB at: {db_path}")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB not found at {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        print("🚀 Running migration 008: extend wells_history with metadata...")

        # Add columns if they don't already exist
        existing = [r[1] for r in cur.execute("PRAGMA table_info(wells_history)").fetchall()]

        to_add = []
        if 'recorded_date' not in existing:
            to_add.append("ALTER TABLE wells_history ADD COLUMN recorded_date DATE")
        if 'reason' not in existing:
            to_add.append("ALTER TABLE wells_history ADD COLUMN reason TEXT")
        if 'changed_values' not in existing:
            to_add.append("ALTER TABLE wells_history ADD COLUMN changed_values TEXT")
        if 'full_snapshot' not in existing:
            to_add.append("ALTER TABLE wells_history ADD COLUMN full_snapshot TEXT")

        for stmt in to_add:
            print(f"-> executing: {stmt}")
            cur.execute(stmt)

        conn.commit()
        print("✅ Migration 008 applied: wells_history extended")

    finally:
        conn.close()


if __name__ == '__main__':
    # run against local DB file
    db_file = os.path.join(os.path.dirname(__file__), '..', '..', 'pump_management.db')
    db_file = os.path.normpath(db_file)
    run(db_file)
