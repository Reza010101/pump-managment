"""
Migration 004: Add additional well fields
Adds columns to `wells` table:
 - current_pipe_diameter TEXT
 - current_pipe_length_m REAL
 - main_cable_specs TEXT
 - well_cable_specs TEXT

This script is safe to run multiple times (it will ignore existing columns).
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
        print("🚀 Running migration 004: adding well fields...")

        statements = [
            "ALTER TABLE wells ADD COLUMN current_pipe_diameter TEXT",
            "ALTER TABLE wells ADD COLUMN current_pipe_length_m REAL",
            "ALTER TABLE wells ADD COLUMN main_cable_specs TEXT",
            "ALTER TABLE wells ADD COLUMN well_cable_specs TEXT",
        ]

        for stmt in statements:
            try:
                print(f"  -> executing: {stmt}")
                cursor.execute(stmt)
                conn.commit()
                print("     ✅ OK")
            except Exception as e:
                # likely column already exists — just report and continue
                print(f"     ⚠️ skipped (maybe exists): {e}")

        print("🎉 Migration 004 finished")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
