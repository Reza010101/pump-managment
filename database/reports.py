from datetime import datetime
from .models import get_db_connection
from .operations import get_last_event_before, get_pump_events_in_range
from utils.date_utils import jalali_to_gregorian, gregorian_to_jalali

def calculate_daily_operating_hours(pump_id, target_date_jalali):
    """محاسبه ساعات کارکرد روزانه پمپ"""
    try:
        start_of_day_str = jalali_to_gregorian(f"{target_date_jalali} 00:00:00")
        end_of_day_str = jalali_to_gregorian(f"{target_date_jalali} 23:59:59")
        
        start_of_day = datetime.strptime(start_of_day_str, '%Y-%m-%d %H:%M:%S')
        end_of_day = datetime.strptime(end_of_day_str, '%Y-%m-%d %H:%M:%S')
        
        last_event_before = get_last_event_before(pump_id, start_of_day)
        days_events = get_pump_events_in_range(pump_id, start_of_day, end_of_day)
        
        if last_event_before:
            current_status = last_event_before['action']
        else:
            current_status = 'OFF'
        
        if not days_events:
            return 24.0 if current_status == 'ON' else 0.0
        
        total_seconds = 0
        current_time = start_of_day
        
        all_events = days_events + [{'event_time': end_of_day, 'action': 'END'}]
        
        for event in all_events:
            if current_status == 'ON':
                time_diff = (event['event_time'] - current_time).total_seconds()
                total_seconds += time_diff
            
            if event['action'] != 'END':
                current_status = event['action']
                current_time = event['event_time']
        
        hours = total_seconds / 3600
        return round(hours, 2)
        
    except Exception as e:
        return 0.0

def calculate_monthly_operating_hours(pump_id, target_month_jalali):
    """محاسبه ساعات کارکرد ماهانه پمپ"""
    try:
        year, month = map(int, target_month_jalali.split('/'))
        total_hours = 0
        
        for day in range(1, 32):
            try:
                date_jalali = f"{year}/{month:02d}/{day:02d}"
                daily_hours = calculate_daily_operating_hours(pump_id, date_jalali)
                total_hours += daily_hours
            except Exception:
                continue
        
        return round(total_hours, 2)
        
    except Exception as e:
        return 0.0

def get_operating_hours_report(date_jalali, month_jalali, report_type):
    """گزارش ساعات کارکرد"""
    results = []
    
    if report_type == 'daily' and date_jalali:
        for pump_id in range(1, 59):
            pump_hours = calculate_daily_operating_hours(pump_id, date_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'operating_hours': pump_hours
                })
                
    elif report_type == 'monthly' and month_jalali:
        for pump_id in range(1, 59):
            pump_hours = calculate_monthly_operating_hours(pump_id, month_jalali)
            
            conn = get_db_connection()
            pump = conn.execute(
                'SELECT pump_number, name FROM pumps WHERE id = ?', (pump_id,)
            ).fetchone()
            conn.close()
            
            if pump:
                results.append({
                    'pump_number': pump['pump_number'],
                    'operating_hours': pump_hours
                })
    
    results.sort(key=lambda x: x['pump_number'])
    return results

def get_status_at_time_report(date_jalali, time, display_type):
    """گزارش وضعیت در زمان خاص"""
    target_datetime_jalali = f"{date_jalali} {time}:00"
    target_datetime_gregorian = jalali_to_gregorian(target_datetime_jalali)

    conn = get_db_connection()
    results = []

    for pump_id in range(1, 59):
        last_event = conn.execute('''
            SELECT ph.action, ph.event_time, ph.reason, ph.notes, p.pump_number, p.name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            WHERE ph.pump_id = ? AND ph.event_time <= ?
            ORDER BY ph.event_time DESC 
            LIMIT 1
        ''', (pump_id, target_datetime_gregorian)).fetchone()
        
        if last_event:
            status = 'ON' if last_event['action'].upper() == 'ON' else 'OFF'
            last_change_jalali = gregorian_to_jalali(last_event['event_time'])
            
            if display_type == 'all' or (display_type == 'on' and status == 'ON') or (display_type == 'off' and status == 'OFF'):
                results.append({
                    'pump_number': last_event['pump_number'],
                    'name': last_event['name'],
                    'status': status,
                    'last_change': last_change_jalali,
                    'reason': last_event['reason'],
                    'notes': last_event['notes']
                })

    conn.close()
    return results

def get_full_history_report(from_date_jalali, to_date_jalali, pump_id):
    """گزارش تاریخچه کامل"""
    if not from_date_jalali or not to_date_jalali:
        return []
    
    start_date = jalali_to_gregorian(f"{from_date_jalali} 00:00:00")
    end_date = jalali_to_gregorian(f"{to_date_jalali} 23:59:59")
    
    conn = get_db_connection()
    
    if pump_id == 'all':
        query = '''
            SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                   ph.reason, ph.notes, u.full_name as user_name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            WHERE ph.event_time BETWEEN ? AND ?
            ORDER BY ph.event_time DESC
        '''
        params = (start_date, end_date)
    else:
        query = '''
            SELECT p.pump_number, p.name, ph.action, ph.event_time, 
                   ph.reason, ph.notes, u.full_name as user_name
            FROM pump_history ph
            JOIN pumps p ON ph.pump_id = p.id
            JOIN users u ON ph.user_id = u.id
            WHERE p.pump_number = ? AND ph.event_time BETWEEN ? AND ?
            ORDER BY ph.event_time DESC
        '''
        params = (pump_id, start_date, end_date)
    
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    formatted_results = []
    for row in results:
        row_dict = dict(row)
        
        jalali_datetime = gregorian_to_jalali(row['event_time'])
        jalali_parts = jalali_datetime.split(' ')
        row_dict['action_date'] = jalali_parts[0]
        row_dict['action_time'] = jalali_parts[1][:5] if len(jalali_parts) > 1 else '00:00'
        row_dict['action_persian'] = 'روشن' if row['action'].upper() == 'ON' else 'خاموش'
        
        formatted_results.append(row_dict)
    
    return formatted_results