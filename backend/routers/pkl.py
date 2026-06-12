from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from services.pkl_service import lookup_pkl

router = APIRouter()


@router.get("/lookup/{referenz}")
def pkl_lookup(referenz: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gibt Lagerorte für eine LS-Nummer aus PKL Übersicht zurück."""
    locations = lookup_pkl(db, referenz)
    return {"locations": locations}
