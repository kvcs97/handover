from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Setting, User
from routers.auth import get_current_user, require_admin, hash_password
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SetupData(BaseModel):
    # Schritt 1: Firmendaten
    company_name:      str
    company_address:   Optional[str] = None
    company_logo_b64:  Optional[str] = None  # Base64 Logo
    # Schritt 2: Drucker
    printer_name:      str
    # Schritt 3: Datenquelle
    data_source_type:  str   # "csv" | "api" | "manual"
    data_source_path:  Optional[str] = None
    data_source_url:   Optional[str] = None
    data_source_key:   Optional[str] = None
    # Schritt 4: Admin-Account
    admin_name:        str
    admin_email:       str
    admin_password:    str


def get_setting(db: Session, key: str) -> Optional[str]:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else None

def set_setting(db: Session, key: str, value: str):
    s = db.query(Setting).filter(Setting.key == key).first()
    if s:
        s.value = value
    else:
        db.add(Setting(key=key, value=value))


@router.get("/is-setup-done")
def is_setup_done(db: Session = Depends(get_db)):
    """Wird beim App-Start geprüft — kein Login nötig"""
    val = get_setting(db, "setup_done")
    return {"setup_done": val == "true"}


@router.post("/setup")
def run_setup(data: SetupData, db: Session = Depends(get_db)):
    """Setup Wizard — nur einmalig, kein Auth nötig"""
    if get_setting(db, "setup_done") == "true":
        return {"error": "Setup bereits abgeschlossen"}

    # Firmendaten speichern
    set_setting(db, "company_name",     data.company_name)
    set_setting(db, "company_address",  data.company_address or "")
    set_setting(db, "company_logo_b64", data.company_logo_b64 or "")

    # Drucker
    set_setting(db, "printer_name",     data.printer_name)

    # Datenquelle
    set_setting(db, "data_source_type", data.data_source_type)
    set_setting(db, "data_source_path", data.data_source_path or "")
    set_setting(db, "data_source_url",  data.data_source_url or "")

    # Admin-Account anlegen
    admin = User(
        name=data.admin_name,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        role="admin"
    )
    db.add(admin)

    # Setup abgeschlossen
    set_setting(db, "setup_done", "true")
    db.commit()

    return {"status": "setup_complete"}


@router.get("/all")
def get_all_settings(db: Session = Depends(get_db), user=Depends(require_admin)):
    """Alle Settings für die Einstellungsseite (nur Admin)"""
    settings = db.query(Setting).all()
    # Passwörter / Keys nicht zurückgeben
    safe_keys = ["company_name", "company_address", "printer_name", "data_source_type"]
    return {s.key: s.value for s in settings if s.key in safe_keys}


@router.put("/{key}")
def update_setting(key: str, value: str, db: Session = Depends(get_db), user=Depends(require_admin)):
    """Einzelne Einstellung aktualisieren (nur Admin)"""
    set_setting(db, key, value)
    db.commit()
    return {"status": "updated"}
