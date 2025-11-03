import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import get_db_connection

def main():
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT id, pump_number, location FROM pumps WHERE id = 1').fetchone()
        print(dict(row) if row else 'pump not found')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
