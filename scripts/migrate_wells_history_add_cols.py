import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'pump_management.db'
BACKUP_DIR = ROOT / 'database_backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if not DB.exists():
    print('Database not found at', DB)
    raise SystemExit(1)

# create a timestamped backup
ts = datetime.now().strftime('%Y%m%d%H%M%S')
backup_path = BACKUP_DIR / f'pump_management.db.migrate_wells_history.bak_{ts}'
shutil.copy2(DB, backup_path)
print('Created DB backup at', backup_path)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

existing = [r['name'] for r in cur.execute("PRAGMA table_info(wells_history)").fetchall()]
print('Existing wells_history columns:', existing)

# columns we want to ensure exist
wanted = {
    'operation_type': 'TEXT',
    'operation_date': 'DATETIME',
    'performed_by': 'TEXT'
}

for col, coltype in wanted.items():
    if col not in existing:
        try:
            sql = f'ALTER TABLE wells_history ADD COLUMN {col} {coltype}'
            print('Adding column:', col)
            cur.execute(sql)
            conn.commit()
            print('Added', col)
        except Exception as e:
            print('Failed to add', col, e)
    else:
        print('Column exists:', col)

conn.close()
print('Migration finished. If your app was running, restart it.')
