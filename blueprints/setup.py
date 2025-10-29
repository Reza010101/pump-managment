from flask import Blueprint, render_template, request, session, redirect, flash
from utils.backup_utils import create_backup, list_backups, restore_backup

setup_bp = Blueprint('setup', __name__)


def _is_admin():
    return 'user_id' in session and session.get('role') == 'admin'


@setup_bp.route('/admin/setup', methods=['GET'])
def admin_setup_get():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    backups = list_backups()
    return render_template('admin_setup.html', backups=backups)


@setup_bp.route('/admin/setup/backup', methods=['POST'])
def admin_setup_backup():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    try:
        path = create_backup()
        flash(f'Backup created: {path}', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    return redirect('/admin/setup')


@setup_bp.route('/admin/setup/restore', methods=['POST'])
def admin_setup_restore():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    backup_file = request.form.get('backup_file')
    confirm = request.form.get('confirm')
    if not backup_file:
        flash('بکاپ نامعتبر است.', 'error')
        return redirect('/admin/setup')
    if confirm != 'true':
        flash('لطفاً بازگردانی را تأیید کنید.', 'warning')
        return redirect('/admin/setup')
    try:
        emergency = create_backup()
        restore_backup(backup_file)
        flash(f'Restored from {backup_file}. Emergency backup created: {emergency}', 'success')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'error')
    return redirect('/admin/setup')
