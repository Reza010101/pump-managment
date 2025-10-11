from flask import Blueprint, request, session, jsonify
from database.operations import change_pump_status

pumps_bp = Blueprint('pumps', __name__)

@pumps_bp.route('/pump/change-status', methods=['POST'])
def change_pump_status_detailed():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'لطفا ابتدا وارد شوید'})
    
    data = request.get_json()
    result = change_pump_status(
        pump_id=data.get('pump_id'),
        action=data.get('action'),
        user_id=session['user_id'],
        reason=data.get('reason'),
        notes=data.get('notes', ''),
        manual_time=data.get('manual_time', False),
        action_date_jalali=data.get('action_date_jalali'),
        action_time=data.get('action_time')
    )
    
    return jsonify(result)