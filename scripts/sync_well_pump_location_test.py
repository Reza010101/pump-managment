import os, sys
# ensure project root is on sys.path so `database` package imports work when script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.wells_operations import get_all_wells, get_well_by_id, record_well_event
from database.models import get_db_connection
from datetime import datetime

def find_allowed_user(conn):
    row = conn.execute("SELECT id, role FROM users WHERE role IN ('admin','maintenance','technician') LIMIT 1").fetchone()
    return row['id'] if row else None

def main():
    conn = get_db_connection()
    try:
        # find a well that has a linked pump
        well = conn.execute('SELECT * FROM wells WHERE pump_id IS NOT NULL LIMIT 1').fetchone()
        if not well:
            print('No well with linked pump found. Exiting.')
            return

        well_id = well['id']
        pump_id = well['pump_id']

        print(f"Found well id={well_id}, pump_id={pump_id}")
        before_well_loc = well['location']
        pump = conn.execute('SELECT * FROM pumps WHERE id = ?', (pump_id,)).fetchone()
        before_pump_loc = pump['location'] if pump else None
        print('Before: well.location=', before_well_loc, 'pump.location=', before_pump_loc)

        user_id = find_allowed_user(conn)
        if not user_id:
            print('No allowed user found to record event. Exiting.')
            return

        # set new location and new name values
        new_location = (before_well_loc or '') + ' [sync-test]'
        before_well_name = well['name']
        new_name = (before_well_name or '') + ' [sync-name]'

        event = {
            'well_id': well_id,
            'recorded_by_user_id': user_id,
            'operation_type': 'update',
            'operation_date': datetime.now().strftime('%Y-%m-%d'),
            'well_updates': {'location': new_location, 'name': new_name},
            'performed_by': 'automated-test',
            'notes': 'sync test'
        }

        result = record_well_event(event)
        print('record_well_event result:', result)

        # re-query after update
        updated_well = conn.execute('SELECT name, location FROM wells WHERE id = ?', (well_id,)).fetchone()
        updated_pump = conn.execute('SELECT name, location FROM pumps WHERE id = ?', (pump_id,)).fetchone()
        print('After: well.name=', updated_well['name'] if updated_well else None, 'well.location=', updated_well['location'] if updated_well else None)
        print('After: pump.name=', updated_pump['name'] if updated_pump else None, 'pump.location=', updated_pump['location'] if updated_pump else None)

    finally:
        conn.close()

if __name__ == '__main__':
    main()
