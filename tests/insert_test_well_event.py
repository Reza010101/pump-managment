# Quick non-UI test: insert a test maintenance event and show effects
from database.models import get_db_connection
from database.wells_operations import record_well_event, ALLOWED_MAINTENANCE_ROLES
from datetime import datetime
import json

def main():
    conn = get_db_connection()
    try:
        # pick a well
        well = conn.execute('SELECT id, notes FROM wells LIMIT 1').fetchone()
        if not well:
            print('ERROR: No wells found in DB')
            return
        well_id = well['id']
        notes_before = well['notes']

        # pick a user with an allowed role
        roles_tuple = tuple(ALLOWED_MAINTENANCE_ROLES)
        # build SQL IN list
        placeholders = ','.join('?' for _ in roles_tuple)
        user = conn.execute(f"SELECT id, role FROM users WHERE role IN ({placeholders}) LIMIT 1", roles_tuple).fetchone()
        if not user:
            print('ERROR: No user with maintenance role found. Roles looked for:', ALLOWED_MAINTENANCE_ROLES)
            return
        user_id = user['id']

        event_data = {
            'well_id': well_id,
            'recorded_by_user_id': user_id,
            'operation_type': 'تست-اتومات',
            'operation_date': datetime.now().strftime('%Y-%m-%d'),
            'performed_by': 'automated-test',
            'notes': 'AUTOMATED TEST NOTE - should NOT persist to wells table',
            'well_updates': {
                # no well updates so wells table should remain same except updated_at if code sets it
            }
        }

        print('Well id:', well_id)
        print('notes before (wells.notes):', repr(notes_before))

        result = record_well_event(event_data)
        print('record_well_event result:', result)

        # re-query wells.notes
        updated_well = conn.execute('SELECT notes FROM wells WHERE id = ?', (well_id,)).fetchone()
        notes_after = updated_well['notes'] if updated_well else None
        print('notes after (wells.notes):', repr(notes_after))

        # query last wells_history row for this well
        hist = conn.execute('SELECT id, reason, operation_type, operation_date FROM wells_history WHERE well_id = ? ORDER BY id DESC LIMIT 1', (well_id,)).fetchone()
        print('last wells_history row:', dict(hist) if hist else None)

    finally:
        conn.close()

if __name__ == '__main__':
    main()
