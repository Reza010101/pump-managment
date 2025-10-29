import shutil
from datetime import datetime
from pathlib import Path

# Adjust paths relative to project root
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "pump_management.db"
BACKUP_DIR = ROOT / "database_backups"


def create_backup():
    """Create a timestamped copy of the SQLite database and return its path."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    dst = BACKUP_DIR / f"pump_management.db.bak_{ts}"
    shutil.copy2(DB_PATH, dst)
    return str(dst)


def list_backups():
    """Return a sorted list of backup file paths (newest first)."""
    if not BACKUP_DIR.exists():
        return []
    files = sorted(BACKUP_DIR.glob("pump_management.db.bak_*"), reverse=True)
    return [str(p) for p in files]


def restore_backup(backup_path):
    """Restore a backup. Before restoring, create an emergency backup and return its path.

    Note: it's caller's responsibility to ensure the app is in a safe state for restore.
    """
    # create emergency backup
    emergency = create_backup()
    shutil.copy2(backup_path, DB_PATH)
    return str(emergency)
