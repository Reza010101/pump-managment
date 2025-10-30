import os
import sys
import pandas as pd
# Ensure project root is on sys.path when running this script from tools/ so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import import_utils as iu
import create_database as cd
import sqlite3

# prepare sample excel
rows = [
    {'well_number': 1, 'well_name': '', 'well_location': 'loc1'},
    {'well_number': 2, 'well_name': 'چاه دوم', 'well_location': 'loc2'},
    {'well_number': 3, 'well_name': None, 'well_location': 'loc3'},
]
df = pd.DataFrame(rows)
path = 'tools/sample_import.xlsx'
df.to_excel(path, index=False)
print('Wrote sample to', path)

# recreate DB
if os.path.exists('pump_management.db'):
    os.remove('pump_management.db')
    print('Removed existing pump_management.db')
cd.main()

# apply import
res = iu.apply_rows_to_db(path, policy='merge')
print('Apply result:', res)

# inspect DB
con = sqlite3.connect('pump_management.db')
cur = con.cursor()
print('Wells:')
for row in cur.execute('SELECT id, well_number, name, location FROM wells ORDER BY id'):
    print(row)
print('Pumps:')
for row in cur.execute('SELECT id, pump_number, name, location FROM pumps ORDER BY id'):
    print(row)
con.close()
print('Done')
