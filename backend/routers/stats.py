from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Handover, Carrier, CourierShipment, CourierCarrier
from routers.auth import get_current_user
from datetime import date, datetime

router = APIRouter()


@router.get("")
def get_stats(db: Session = Depends(get_db), user=Depends(get_current_user)):
    today      = date.today()
    year_start = datetime(today.year, 1, 1)
    today_str  = today.isoformat()
    year_str   = str(today.year)

    # ── LKW ──────────────────────────────────────────────────
    lkw_total      = db.query(func.count(Handover.id)).scalar() or 0
    lkw_this_year  = db.query(func.count(Handover.id)).filter(
        Handover.created_at >= year_start
    ).scalar() or 0
    lkw_today      = db.query(func.count(Handover.id)).filter(
        func.date(Handover.created_at) == today_str
    ).scalar() or 0
    lkw_archived   = db.query(func.count(Handover.id)).filter(
        Handover.status == "archived"
    ).scalar() or 0
    lkw_carriers   = db.query(func.count(Carrier.id)).filter(
        Carrier.active == True
    ).scalar() or 0

    # ── Kurier ───────────────────────────────────────────────
    courier_total     = db.query(func.count(CourierShipment.id)).scalar() or 0
    courier_this_year = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.process_date.like(f"{year_str}-%")
    ).scalar() or 0
    courier_today     = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.process_date == today_str
    ).scalar() or 0
    courier_archived  = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.status == "archived"
    ).scalar() or 0
    courier_carriers  = db.query(func.count(CourierCarrier.id)).filter(
        CourierCarrier.is_active == True
    ).scalar() or 0

    return {
        "lkw": {
            "total":      lkw_total,
            "this_year":  lkw_this_year,
            "today":      lkw_today,
            "archived":   lkw_archived,
            "carriers":   lkw_carriers,
        },
        "courier": {
            "total":      courier_total,
            "this_year":  courier_this_year,
            "today":      courier_today,
            "archived":   courier_archived,
            "carriers":   courier_carriers,
        },
    }
