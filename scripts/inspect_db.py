import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pump_management.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found at: {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print(f"Inspecting database: {DB_PATH}\n")

# list tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
tables = [r[0] for r in cursor.fetchall()]

if not tables:
    print("No tables found.")
    conn.close()
    raise SystemExit(0)

for t in tables:
    print(f"Table: {t}")
    # count rows
    try:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {t}")
        cnt = cursor.fetchone()['cnt']
    except Exception as e:
        cnt = f"error: {e}"
    print(f"  Rows: {cnt}")

    # schema
    try:
        cursor.execute(f"PRAGMA table_info({t})")
        cols = cursor.fetchall()
        print("  Columns:")
        for c in cols:
            print(f"    - {c['name']} ({c['type']}){' PRIMARY KEY' if c['pk'] else ''}{' NOT NULL' if c['notnull'] else ''}")
    except Exception as e:
        print(f"  Schema error: {e}")

    # sample rows
    try:
        cursor.execute(f"SELECT * FROM {t} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("  Sample rows:")
            for r in rows:
                print("    ", dict(r))
        else:
            print("  (no rows)")
    except Exception as e:
        print(f"  Sample error: {e}")

    print()

conn.close()
