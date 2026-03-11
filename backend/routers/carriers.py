from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Carrier
from routers.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class CarrierCreate(BaseModel):
    company_name: str

@router.get("/")
def list_carriers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Alle Spediteure – zuletzt benutzte zuerst (für Dropdown)"""
    return db.query(Carrier).order_by(Carrier.last_used.desc()).all()

@router.post("/")
def create_carrier(data: CarrierCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Neuer Spediteur – wird automatisch beim ersten Eintippen angelegt"""
    existing = db.query(Carrier).filter(Carrier.company_name == data.company_name).first()
    if existing:
        return existing
    carrier = Carrier(company_name=data.company_name)
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    return carrier

@router.get("/search")
def search_carriers(q: str = "", db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Live-Suche für Autovervollständigung im Dropdown"""
    return db.query(Carrier).filter(
        Carrier.company_name.ilike(f"%{q}%")
    ).order_by(Carrier.last_used.desc()).limit(10).all()
