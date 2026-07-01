from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import require_admin
from routers.settings import get_setting
from services.backup_service import do_backup, get_last_backup_date

router = APIRouter()


@router.post("/now")
def backup_now(db: Session = Depends(get_db), admin=Depends(require_admin)):
    backup_path = get_setting(db, "backup_path")
    if not backup_path:
        raise HTTPException(status_code=400, detail="Kein Backup-Pfad konfiguriert")
    try:
        dest = do_backup(backup_path)
        return {"status": "ok", "path": dest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup fehlgeschlagen: {e}")


@router.get("/status")
def backup_status(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return {
        "backup_path": get_setting(db, "backup_path") or "",
        "last_backup": get_last_backup_date(),
    }
