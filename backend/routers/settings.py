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
    set_setting(db, "data_source_key",  data.data_source_key or "")

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


SAFE_KEYS = [
    "company_name", "company_address", "company_logo_b64",
    "printer_name",
    "data_source_type", "data_source_path", "data_source_url", "data_source_key",
    "outlook_type", "outlook_email", "outlook_tenant_id",
    "outlook_client_id", "outlook_server", "outlook_imap_server",
    "archive_path",
    # Kurier-Modul
    "courier_mailbox", "courier_archive_path", "courier_default_mode",
    # PKL Übersicht Integration
    "pkl_bin_id", "pkl_api_key",
    # Datensicherung
    "backup_path",
]


@router.get("/global")
def get_global_settings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Globale Einstellungen — für alle angemeldeten Benutzer lesbar"""
    settings_dict = {s.key: s.value for s in db.query(Setting).all()}
    result = {key: settings_dict.get(key, "") for key in SAFE_KEYS}
    result["outlook_logged_in"] = bool(settings_dict.get("outlook_access_token"))
    return result


@router.get("/all")
def get_all_settings(db: Session = Depends(get_db), user=Depends(require_admin)):
    """Alle Settings für die Einstellungsseite (nur Admin)"""
    settings_dict = {s.key: s.value for s in db.query(Setting).all()}
    result = {key: settings_dict.get(key, "") for key in SAFE_KEYS}
    # Token nicht zurückgeben — nur ob vorhanden
    result["outlook_logged_in"] = bool(settings_dict.get("outlook_access_token"))
    return result


@router.get("/printers")
def list_printers(user=Depends(get_current_user)):
    """Alle auf Windows installierten Drucker zurückgeben (identisch zu Windows-Einstellungen)"""
    import subprocess, json
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Printer | Select-Object Name, PortName, Type | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=10
        )
        raw = json.loads(result.stdout or "[]")
        if isinstance(raw, dict):
            raw = [raw]
        printers = []
        for p in raw:
            port = p.get("PortName") or ""
            # Type 0 = lokal, Type 1 = Netzwerk-Verbindung
            p_type = p.get("Type", 0)
            printers.append({
                "name": p.get("Name", ""),
                "port": port,
                "type": "local" if p_type == 0 else "network",
            })
        return printers
    except Exception:
        return []


@router.post("/test-print")
def test_print(data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Druckt eine Testseite auf dem angegebenen Drucker."""
    from fastapi import HTTPException
    import tempfile, os
    printer_name = (data.get("printer_name") or "").strip()
    if not printer_name:
        raise HTTPException(status_code=400, detail="Kein Drucker angegeben")

    # Einfache Test-PDF mit ReportLab erstellen
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        c = rl_canvas.Canvas(tmp.name, pagesize=A4)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(A4[0] / 2, A4[1] / 2 + 20, "HandOver – Testdruck")
        c.setFont("Helvetica", 14)
        c.drawCentredString(A4[0] / 2, A4[1] / 2 - 20, f"Drucker: {printer_name}")
        c.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test-PDF konnte nicht erstellt werden: {e}")

    try:
        from services.printer import print_document
        print_document(tmp.name, printer_name=printer_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    return {"status": "ok"}


@router.put("/{key}")
def update_setting(key: str, value: str, db: Session = Depends(get_db), user=Depends(require_admin)):
    """Einzelne Einstellung aktualisieren (nur Admin)"""
    set_setting(db, key, value)
    db.commit()
    return {"status": "updated"}
