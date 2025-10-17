# فایل تست برای عملیات چاه‌ها
# test_wells_operations.py

from database.wells_operations import *

# تست دریافت تمام چاه‌ها
wells = get_all_wells()
print(f"تعداد چاه‌ها: {len(wells)}")

# تست دریافت یک چاه خاص
if wells:
    well = get_well_by_id(wells[0]['id'])
    print(f"چاه اول: {well['name']}")

# تست آمار چاه
if wells:
    stats = get_well_statistics(wells[0]['id'])
    print(f"آمار چاه: {stats}")