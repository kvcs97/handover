from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, Handover, Signature, Carrier, AuditLog
from routers.auth import get_current_user
from services.pdf_gen import generate_pdf
from services.printer import print_document
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────

class HandoverCreate(BaseModel):
    referenz:     str
    carrier_id:   Optional[int] = None
    truck_plate:  Optional[str] = None
    driver_name:  Optional[str] = None

class SignatureSubmit(BaseModel):
    handover_id:  int
    png_data:     str   # Base64 PNG von signature_pad.js
    signer_name:  str


# ── Endpoints ─────────────────────────────────────────────

@router.post("/create")
def create_handover(data: HandoverCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    handover = Handover(
        referenz=data.referenz,
        carrier_id=data.carrier_id,
        truck_plate=data.truck_plate,
        driver_name=data.driver_name,
        created_by=user.id,
        status="pending"
    )
    db.add(handover)

    if data.carrier_id:
        carrier = db.query(Carrier).filter(Carrier.id == data.carrier_id).first()
        if carrier:
            carrier.last_used = datetime.utcnow()

    db.add(AuditLog(user_id=user.id, action="handover_created", detail=data.referenz))
    db.commit()
    db.refresh(handover)

    # Drucken — Fehler blockiert Workflow nicht
    try:
        pdf_path = generate_pdf(handover, db)
        print_document(pdf_path)
        handover.status = "printed"
        db.commit()
    except Exception as e:
        print(f"[WARN] Druckfehler (nicht kritisch): {e}")

    return {"id": handover.id, "status": handover.status}


@router.post("/sign")
def sign_handover(data: SignatureSubmit, db: Session = Depends(get_db), user=Depends(get_current_user)):
    handover = db.query(Handover).filter(Handover.id == data.handover_id).first()
    if not handover:
        raise HTTPException(status_code=404, detail="Übergabe nicht gefunden")

    # Unterschrift speichern
    signature = Signature(
        handover_id=data.handover_id,
        png_data=data.png_data,
        signer_name=data.signer_name,
    )
    db.add(signature)
    handover.signed_at = datetime.utcnow()
    handover.status = "signed"
    db.commit()

    # PDF generieren — Fehler blockiert Workflow nicht
    pdf_path = None
    try:
        pdf_path = generate_pdf(handover, db, signature=data.png_data)
        handover.pdf_path = pdf_path
        handover.status = "archived"
        db.commit()
    except Exception as e:
        print(f"[WARN] PDF-Fehler (nicht kritisch): {e}")

    db.add(AuditLog(user_id=user.id, handover_id=handover.id, action="signed", detail=data.signer_name))
    db.commit()

    # Workflow geht immer weiter, auch ohne PDF
    return {"status": handover.status, "pdf_path": pdf_path}


@router.get("/list")
def list_handovers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    handovers = db.query(Handover).order_by(Handover.created_at.desc()).limit(100).all()
    return handovers


@router.get("/{handover_id}/pdf")
def get_pdf(handover_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    handover = db.query(Handover).filter(Handover.id == handover_id).first()
    if not handover or not handover.pdf_path or not os.path.exists(handover.pdf_path):
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    return FileResponse(handover.pdf_path, media_type="application/pdf")
