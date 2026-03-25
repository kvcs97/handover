from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Setting
from routers.auth import get_current_user, require_admin
from services.license_service import validate_license, check_license_from_db
from pydantic import BaseModel

router = APIRouter()


class LicenseSubmit(BaseModel):
    license_key: str


@router.get("/status")
def get_license_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gibt aktuellen Lizenzstatus zurück"""
    return check_license_from_db(db)


@router.post("/activate")
def activate_license(data: LicenseSubmit, db: Session = Depends(get_db), user=Depends(require_admin)):
    """Aktiviert einen Lizenzschlüssel"""
    result = validate_license(data.license_key)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Ungültiger Schlüssel"))

    # In DB speichern
    s = db.query(Setting).filter(Setting.key == "license_key").first()
    if s:
        s.value = data.license_key.upper()
    else:
        db.add(Setting(key="license_key", value=data.license_key.upper()))
    db.commit()

    return {"status": "activated", **result}


@router.get("/check")
def check_license(db: Session = Depends(get_db)):
    """
    Schnellprüfung ohne Auth — wird beim App-Start aufgerufen.
    Gibt nur valid: true/false zurück.
    """
    result = check_license_from_db(db)
    return {
        "valid":    result.get("valid", False),
        "plan":     result.get("plan", ""),
        "expires":  result.get("expires", ""),
        "days_left": result.get("days_left", 0),
    }
