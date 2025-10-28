import sqlite3
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'pump_management.db')

print('Checking DB at:', db_path)
if not os.path.exists(db_path):
    print('Database not found')
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wells_history'")
row = cur.fetchone()
if row:
    print('FOUND wells_history table')
else:
    print('wells_history table NOT FOUND')
conn.close()
