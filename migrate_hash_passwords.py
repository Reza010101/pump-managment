"""
Utility script to backfill plain-text passwords to hashed passwords using werkzeug.

Usage:
  - Make a backup copy of pump_management.db (script does it automatically).
  - Run: py migrate_hash_passwords.py

Note: This script will replace passwords that do not look like werkzeug PBKDF2 hashes.
Always review the backup before running in production.
"""
import shutil
import sqlite3
import time
from werkzeug.security import generate_password_hash

DB = 'pump_management.db'

def backup_db():
    ts = time.strftime('%Y%m%d_%H%M%S')
    dest = f'{DB}.bak.{ts}'
    shutil.copy2(DB, dest)
    print(f'Backup created: {dest}')
    return dest

def looks_hashed(pw: str) -> bool:
    if not pw:
        return False
    # werkzeug generate_password_hash default starts with 'pbkdf2:'
    return pw.startswith('pbkdf2:') or pw.startswith('$2b$') or pw.startswith('$2a$')

def main():
    backup_db()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute('SELECT id, password FROM users').fetchall()
    updated = 0
    for r in rows:
        pw = r['password']
        if pw and not looks_hashed(pw):
            new_pw = generate_password_hash(pw)
            cur.execute('UPDATE users SET password = ? WHERE id = ?', (new_pw, r['id']))
            updated += 1
            print(f'Hashed password for user id={r["id"]}')

    conn.commit()
    conn.close()
    print(f'Done. {updated} passwords updated.')

if __name__ == '__main__':
    main()
