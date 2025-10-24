import sqlite3

conn = sqlite3.connect('pump_management.db')
cur = conn.cursor()
print('wells_history columns:')
for r in cur.execute("PRAGMA table_info(wells_history)"):
    print(r)
print('\nwells columns:')
for r in cur.execute("PRAGMA table_info(wells)"):
    print(r)
conn.close()
