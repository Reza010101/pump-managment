import sqlite3

DB = 'pump_management.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()
rows = cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()
print('TABLES:')
for name, sql in rows:
    print('-', name)

conn.close()
