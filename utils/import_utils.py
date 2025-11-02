import pandas as pd
from io import BytesIO
from pathlib import Path
from datetime import datetime
import sqlite3
import uuid
from .backup_utils import BACKUP_DIR, DB_PATH


TEMPLATE_COLUMNS = [
    'well_number',
    'well_name',
    'well_location',
    'total_depth',
    'pump_installation_depth',
    'well_diameter',
    'current_pump_brand',
    'current_pump_model',
    'current_pump_power',
    'current_pipe_material',
    'current_pipe_diameter',
    'current_pipe_length_m',
    'main_cable_specs',
    'well_cable_specs',
    'current_panel_specs',
    'status',
    # notes and pump_id removed per admin request; only well_number is required
]


def generate_template_bytes():
    """Return an in-memory xlsx bytes for the template."""
    df = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='wells')
    bio.seek(0)
    return bio.getvalue()


def save_upload_file(file_storage):
    """Save uploaded file to BACKUP_DIR/imports with a uuid name and return path."""
    imports_dir = Path(BACKUP_DIR) / 'imports'
    imports_dir.mkdir(parents=True, exist_ok=True)
    fname = f"upload_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}.xlsx"
    dst = imports_dir / fname
    file_storage.save(str(dst))
    return str(dst)


def parse_and_validate(file_path, max_wells=1000, preview_limit=200):
    """Parse uploaded excel and return summary and preview rows.

    Returns dict: { total_rows, errors: [{row, msg}], rows: [dict,...], summary }
    """
    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
    # normalize columns
    cols = {c.lower().strip(): c for c in df.columns}
    mapping = {}
    for expected in TEMPLATE_COLUMNS:
        if expected in cols:
            mapping[expected] = cols[expected]
    rows = []
    errors = []
    for idx, r in df.iterrows():
        rn = int(idx) + 2  # excel row (header=1)
        try:
            well_number = None
            if 'well_number' in mapping:
                val = r[mapping['well_number']]
                if pd.isna(val):
                    raise ValueError('well_number is required')
                well_number = int(val)
            else:
                raise ValueError('well_number column missing')

            if not (1 <= well_number <= max_wells):
                raise ValueError(f'well_number {well_number} out of range 1..{max_wells}')

            # well name: optional now — default to 'چاه شماره {well_number}' when missing
            name = ''
            if 'well_name' in mapping:
                name = r[mapping['well_name']]
            if pd.isna(name) or str(name).strip() == '':
                name = f'چاه شماره {well_number}'

            # fields (optional)
            well_location = str(r[mapping['well_location']]) if 'well_location' in mapping and not pd.isna(r[mapping['well_location']]) else ''
            total_depth = str(r[mapping['total_depth']]) if 'total_depth' in mapping and not pd.isna(r[mapping['total_depth']]) else ''
            pump_installation_depth = str(r[mapping['pump_installation_depth']]) if 'pump_installation_depth' in mapping and not pd.isna(r[mapping['pump_installation_depth']]) else ''
            well_diameter = str(r[mapping['well_diameter']]) if 'well_diameter' in mapping and not pd.isna(r[mapping['well_diameter']]) else ''
            current_pump_brand = str(r[mapping['current_pump_brand']]) if 'current_pump_brand' in mapping and not pd.isna(r[mapping['current_pump_brand']]) else ''
            current_pump_model = str(r[mapping['current_pump_model']]) if 'current_pump_model' in mapping and not pd.isna(r[mapping['current_pump_model']]) else ''
            current_pump_power = str(r[mapping['current_pump_power']]) if 'current_pump_power' in mapping and not pd.isna(r[mapping['current_pump_power']]) else ''
            current_pipe_material = str(r[mapping['current_pipe_material']]) if 'current_pipe_material' in mapping and not pd.isna(r[mapping['current_pipe_material']]) else ''
            current_pipe_diameter = str(r[mapping['current_pipe_diameter']]) if 'current_pipe_diameter' in mapping and not pd.isna(r[mapping['current_pipe_diameter']]) else ''
            current_pipe_length_m = r[mapping['current_pipe_length_m']] if 'current_pipe_length_m' in mapping and not pd.isna(r[mapping['current_pipe_length_m']]) else ''
            main_cable_specs = str(r[mapping['main_cable_specs']]) if 'main_cable_specs' in mapping and not pd.isna(r[mapping['main_cable_specs']]) else ''
            well_cable_specs = str(r[mapping['well_cable_specs']]) if 'well_cable_specs' in mapping and not pd.isna(r[mapping['well_cable_specs']]) else ''
            current_panel_specs = str(r[mapping['current_panel_specs']]) if 'current_panel_specs' in mapping and not pd.isna(r[mapping['current_panel_specs']]) else ''
            status = str(r[mapping['status']]) if 'status' in mapping and not pd.isna(r[mapping['status']]) else 'active'
            notes = str(r[mapping['notes']]) if 'notes' in mapping and not pd.isna(r[mapping['notes']]) else ''

            # pump_number defaults to well_number to preserve invariant pump_id==pump_number==well.id
            pump_number = well_number

            row = {
                'well_number': well_number,
                'well_name': str(name),
                'well_location': well_location,
                'total_depth': total_depth,
                'pump_installation_depth': pump_installation_depth,
                'well_diameter': well_diameter,
                'current_pump_brand': current_pump_brand,
                'current_pump_model': current_pump_model,
                'current_pump_power': current_pump_power,
                'current_pipe_material': current_pipe_material,
                'current_pipe_diameter': current_pipe_diameter,
                'current_pipe_length_m': current_pipe_length_m,
                'main_cable_specs': main_cable_specs,
                'well_cable_specs': well_cable_specs,
                'current_panel_specs': current_panel_specs,
                'status': status,
                'pump_number': pump_number
            }
            rows.append(row)
        except Exception as e:
            errors.append({'row': rn, 'msg': str(e)})

    summary = {
        'total_rows': len(df),
        'valid_rows': len(rows),
        'error_count': len(errors)
    }
    return {
        'summary': summary,
        'errors': errors,
        'rows_preview': rows[:preview_limit],
        'all_rows_count': len(rows)
    }


def _set_sqlite_sequence(conn, table_name, seq_val):
    # ensure sqlite_sequence exists and is updated so AUTOINCREMENT doesn't conflict
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO sqlite_sequence(name, seq) VALUES (?, ?)", (table_name, seq_val))
        conn.commit()
    except Exception:
        conn.rollback()


def apply_rows_to_db(file_path, policy='merge', max_wells=1000):
    """Apply parsed rows to the DB. Only 'merge' policy is supported.

    Returns dict with result counts and messages.
    """
    parsed = parse_and_validate(file_path, max_wells=max_wells, preview_limit=1000000)
    if parsed['summary']['error_count'] > 0:
        return {'ok': False, 'msg': 'Validation errors present', 'errors': parsed['errors']}

    # Only merge mode is supported now. Reject any explicit overwrite requests.
    if policy != 'merge':
        return {'ok': False, 'msg': "Policy 'overwrite' is not supported. Use 'merge' instead."}

    rows = parsed['rows_preview'] if parsed['all_rows_count'] == len(parsed['rows_preview']) else parsed['rows_preview']
    # open DB
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # ensure wells table has pump_id column (older DBs may not)
        try:
            cur.execute("SELECT pump_id FROM wells LIMIT 1")
        except Exception:
            # add the column if it doesn't exist
            try:
                cur.execute('ALTER TABLE wells ADD COLUMN pump_id INTEGER')
                conn.commit()
                # populate pump_id for existing rows to match id
                cur.execute('UPDATE wells SET pump_id = id WHERE pump_id IS NULL')
                conn.commit()
            except Exception:
                conn.rollback()

        # apply rows
        inserted = 0
        updated = 0
        for r in rows:
            wid = int(r['well_number'])
            pnum = int(r['pump_number'])
            # pump name: if provided use it, otherwise default to 'پمپ شماره {pnum}'
            pname = r.get('pump_name') if isinstance(r, dict) and r.get('pump_name') else f'پمپ شماره {pnum}'
            # wells: id is AUTOINCREMENT but we explicitly set id to well_number to preserve invariant
            cur.execute('SELECT id FROM wells WHERE id = ?', (wid,))
            existing_well = cur.fetchone()
            if existing_well:
                # update
                cur.execute('''UPDATE wells SET
                    well_number = ?, name = ?, location = ?, total_depth = ?, pump_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?''', (wid, r['well_name'], r['well_location'], r['total_depth'], pnum, wid))
                updated += 1
            else:
                cur.execute('''INSERT INTO wells (id, well_number, name, location, total_depth, pump_id)
                    VALUES (?, ?, ?, ?, ?, ?)''', (wid, wid, r['well_name'], r['well_location'], r['total_depth'], pnum))
                inserted += 1

            # pumps (id == pump_number)
            cur.execute('SELECT id FROM pumps WHERE id = ?', (pnum,))
            existing_pump = cur.fetchone()
            if existing_pump:
                cur.execute('''UPDATE pumps SET pump_number = ?, name = ?, location = ? WHERE id = ?''', (pnum, pname, r['well_location'], pnum))
            else:
                cur.execute('''INSERT INTO pumps (id, pump_number, name, location) VALUES (?, ?, ?, ?)''', (pnum, pnum, pname, r['well_location']))

        conn.commit()

        # set sqlite_sequence for wells and pumps to avoid future conflicts
        cur.execute('SELECT MAX(id) as m FROM wells')
        max_w = cur.fetchone()['m'] or 0
        cur.execute('SELECT MAX(id) as m FROM pumps')
        max_p = cur.fetchone()['m'] or 0
        _set_sqlite_sequence(conn, 'wells', max_w)
        _set_sqlite_sequence(conn, 'pumps', max_p)

        return {'ok': True, 'inserted': inserted, 'updated': updated, 'total': inserted + updated}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'msg': str(e)}
    finally:
        conn.close()
