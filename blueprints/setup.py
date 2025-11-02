from flask import Blueprint, render_template, request, session, redirect, flash, send_file
from utils.backup_utils import create_backup, list_backups, restore_backup, BACKUP_DIR, DB_PATH
from utils.import_utils import generate_template_bytes, save_upload_file, parse_and_validate, apply_rows_to_db
import sqlite3
from io import BytesIO
from pathlib import Path

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


@setup_bp.route('/admin/setup/download-template', methods=['GET'])
def admin_setup_download_template():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    try:
        data = generate_template_bytes()
        bio = BytesIO(data)
        bio.seek(0)
        return send_file(bio, download_name='wells_template.xlsx', as_attachment=True)
    except Exception as e:
        flash(f'Error generating template: {e}', 'error')
        return redirect('/admin/setup')


@setup_bp.route('/admin/setup/upload-preview', methods=['POST'])
def admin_setup_upload_preview():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    f = request.files.get('wells_file')
    if not f:
        flash('فایل ارسال نشد.', 'error')
        return redirect('/admin/setup')
    try:
        saved = save_upload_file(f)
        result = parse_and_validate(saved, max_wells=1000)
        # dry-run: compare with DB to estimate inserted/updated counts
        will_insert = 0
        will_update = 0
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            for r in result.get('rows_preview', []):
                wid = int(r['well_number'])
                cur.execute('SELECT id FROM wells WHERE id = ?', (wid,))
                if cur.fetchone():
                    will_update += 1
                else:
                    will_insert += 1
        except Exception:
            # ignore DB errors for preview; set counts to None
            will_insert = None
            will_update = None
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # pass preview, dry-run counts and saved path to template for apply
        return render_template('admin_setup_preview.html', preview=result, upload_path=saved, dry_run={'insert': will_insert, 'update': will_update})
    except Exception as e:
        flash(f'Error processing file: {e}', 'error')
        return redirect('/admin/setup')


@setup_bp.route('/admin/setup/apply-upload', methods=['POST'])
def admin_setup_apply_upload():
    if not _is_admin():
        flash('دسترسی غیر مجاز!', 'error')
        return redirect('/')
    upload_path = request.form.get('upload_path')
    policy = request.form.get('policy') or 'merge'
    # Only 'merge' is supported now
    if policy != 'merge':
        flash('Policy نامعتبر است یا پشتیبانی نمی‌شود (only merge).', 'error')
        return redirect('/admin/setup')
    if not upload_path or not Path(upload_path).exists():
        flash('فایل آپلود یافته یافت نشد.', 'error')
        return redirect('/admin/setup')
    # apply
    try:
        res = apply_rows_to_db(upload_path, policy=policy, max_wells=1000)
        if not res.get('ok'):
            flash('خطا در اعمال داده‌ها: ' + str(res.get('msg', 'unknown')), 'error')
            return redirect('/admin/setup')
        flash(f"اعمال شد: inserted={res.get('inserted',0)} updated={res.get('updated',0)}", 'success')
    except Exception as e:
        flash(f'Error applying upload: {e}', 'error')
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
        # restore_backup() already creates an emergency backup internally,
        # so call it directly and use its returned emergency path. This avoids
        # creating two backups for a single restore operation.
        emergency = restore_backup(backup_file)
        flash(f'Restored from {backup_file}. Emergency backup created: {emergency}', 'success')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'error')
    return redirect('/admin/setup')
