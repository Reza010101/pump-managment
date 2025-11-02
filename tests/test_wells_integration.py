import os
import sys
import unittest
import sqlite3
from pathlib import Path

# Ensure project root is importable when running tests from workspace root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import import_utils as iu
import create_database as cd
from database.wells_operations import get_all_wells

# Safety guard: these integration tests intentionally clear or remove
# `pump_management.db` to get a clean slate. To avoid accidental data loss
# when running tests in a workspace with a real DB, require an explicit
# environment variable `ALLOW_TEST_DB_RESET=1` to allow the cleanup to run.
# This prevents `py -m unittest discover` from wiping a production DB by
# mistake.
import os
if os.path.exists('pump_management.db') and os.environ.get('ALLOW_TEST_DB_RESET') != '1':
    raise RuntimeError(
        "Integration tests would reset 'pump_management.db'. "
        "Set environment variable ALLOW_TEST_DB_RESET=1 to confirm or run tests against a copy."
    )

class WellsImportIntegrationTest(unittest.TestCase):
    SAMPLE_PATH = Path('tests/sample_for_test.xlsx')

    def setUp(self):
        # Prepare a small sample Excel file with 3 wells
        import pandas as pd
        rows = [
            {'well_number': 1, 'well_name': '', 'well_location': 'loc1'},
            {'well_number': 2, 'well_name': 'چاه دوم', 'well_location': 'loc2'},
            {'well_number': 3, 'well_name': None, 'well_location': 'loc3'},
        ]
        df = pd.DataFrame(rows)
        self.SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(self.SAMPLE_PATH, index=False)

        # Ensure clean DB: if DB exists, try to clear relevant tables (avoid deleting file which may be locked)
        if os.path.exists('pump_management.db'):
            import time
            cleaned = False
            for _ in range(5):
                try:
                    conn = sqlite3.connect('pump_management.db')
                    cur = conn.cursor()
                    # best-effort cleanup of previous test artifacts
                    try:
                        cur.execute('DELETE FROM pump_history')
                        cur.execute('DELETE FROM pumps')
                        cur.execute('DELETE FROM wells_history')
                        cur.execute('DELETE FROM wells')
                        conn.commit()
                        cleaned = True
                    except Exception:
                        conn.rollback()
                    conn.close()
                    if cleaned:
                        break
                except Exception:
                    time.sleep(0.2)
            if not cleaned:
                # fallback: try to remove the file (may fail if locked)
                try:
                    os.remove('pump_management.db')
                    cleaned = True
                except Exception:
                    pass

        # Create fresh DB schema (idempotent)
        cd.main()

    def tearDown(self):
        # cleanup sample file and DB
        try:
            if self.SAMPLE_PATH.exists():
                self.SAMPLE_PATH.unlink()
        except Exception:
            pass
        try:
            if os.path.exists('pump_management.db'):
                os.remove('pump_management.db')
        except Exception:
            pass

    def test_import_creates_wells_and_pumps_with_matching_ids(self):
        # Apply import (merge)
        res = iu.apply_rows_to_db(str(self.SAMPLE_PATH), policy='merge')
        self.assertTrue(res.get('ok'), msg=f"apply_rows_to_db failed: {res}")
        self.assertEqual(res.get('inserted'), 3)

        wells = get_all_wells()
        # get_all_wells returns sqlite3.Row objects; check length
        self.assertEqual(len(wells), 3, msg=f"expected 3 wells, got {len(wells)}")

        # Verify pump_id matches well id and pumps table has matching rows
        conn = sqlite3.connect('pump_management.db')
        cur = conn.cursor()
        pumps_count = cur.execute('SELECT COUNT(*) FROM pumps').fetchone()[0]
        self.assertEqual(pumps_count, 3, msg=f"expected 3 pumps, got {pumps_count}")

        for w in wells:
            wid = w['id']
            # ensure pump_id exists and equals id
            self.assertIn('pump_id', w.keys())
            self.assertEqual(w['pump_id'], wid)
            # ensure a pump row exists with same id
            pump = cur.execute('SELECT id, pump_number FROM pumps WHERE id = ?', (wid,)).fetchone()
            self.assertIsNotNone(pump, msg=f"pump for well {wid} not found")
            self.assertEqual(pump[0], wid)
            self.assertEqual(int(pump[1]), wid)
        conn.close()

if __name__ == '__main__':
    unittest.main()
