import os
import sys
# ensure project root is on sys.path so 'database' package can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.wells_operations import create_maintenance_operation

op = {
    'well_id': 1,
    'recorded_by_user_id': 1,
    'operation_type': 'repair',
    'operation_date': '2025-10-24',
    'operation_time': '10:00',
    
    'performed_by': 'تیم تعمیرات',
    'notes': 'توضیحات تست',
    'well_updates': {
        'current_pipe_length_m': 123.45,
        'current_pipe_diameter': '50mm'
    }
}

res = create_maintenance_operation(op)
print(res)
