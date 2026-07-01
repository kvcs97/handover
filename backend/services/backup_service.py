import os
import sqlite3
from datetime import date

_HANDOVER_DIR     = os.path.join(os.path.expanduser("~"), ".handover")
_DB_PATH          = os.path.join(_HANDOVER_DIR, "handover.db")
_LAST_BACKUP_FILE = os.path.join(_HANDOVER_DIR, "last_backup.txt")
_MAX_BACKUPS      = 30


def get_last_backup_date() -> str | None:
    if not os.path.isfile(_LAST_BACKUP_FILE):
        return None
    with open(_LAST_BACKUP_FILE, "r") as f:
        return f.read().strip() or None


def backup_due() -> bool:
    return get_last_backup_date() != date.today().isoformat()


def do_backup(backup_dir: str) -> str:
    """Sichert handover.db via SQLite Online-Backup-API nach backup_dir/handover_YYYY-MM-DD.db.
    Gibt den Zielpfad zurück."""
    os.makedirs(backup_dir, exist_ok=True)
    dest = os.path.join(backup_dir, f"handover_{date.today().isoformat()}.db")

    src = sqlite3.connect(_DB_PATH)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    with open(_LAST_BACKUP_FILE, "w") as f:
        f.write(date.today().isoformat())

    _cleanup_old_backups(backup_dir)
    return dest


def _cleanup_old_backups(backup_dir: str) -> None:
    try:
        files = sorted(
            f for f in os.listdir(backup_dir)
            if f.startswith("handover_") and f.endswith(".db")
        )
        for old in files[:-_MAX_BACKUPS]:
            try:
                os.remove(os.path.join(backup_dir, old))
            except Exception:
                pass
    except Exception:
        pass
