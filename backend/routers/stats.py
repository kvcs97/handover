from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Handover, Carrier, CourierShipment, CourierCarrier
from routers.auth import get_current_user
from datetime import date, datetime
from calendar import monthrange

router = APIRouter()


@router.get("")
def get_stats(
    year:  int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    today      = date.today()
    sel_year   = year  or today.year
    sel_month  = month or today.month

    year_start  = datetime(sel_year, 1, 1)
    today_str   = today.isoformat()
    year_str    = str(sel_year)

    last_day    = monthrange(sel_year, sel_month)[1]
    month_start = datetime(sel_year, sel_month, 1)
    month_end   = datetime(sel_year, sel_month, last_day, 23, 59, 59)
    month_start_str = month_start.strftime('%Y-%m-%d')
    month_end_str   = month_end.strftime('%Y-%m-%d')

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
    lkw_carriers   = db.query(func.count(Carrier.id)).scalar() or 0
    lkw_this_month = db.query(func.count(Handover.id)).filter(
        Handover.created_at >= month_start,
        Handover.created_at <= month_end,
    ).scalar() or 0

    lkw_by_carrier = [
        {"name": row[0], "count": row[1]}
        for row in (
            db.query(Carrier.company_name, func.count(Handover.id))
            .join(Handover, Handover.carrier_id == Carrier.id)
            .filter(Handover.created_at >= month_start, Handover.created_at <= month_end)
            .group_by(Carrier.id, Carrier.company_name)
            .order_by(func.count(Handover.id).desc())
            .all()
        )
    ]

    # ── Kurier ───────────────────────────────────────────────
    courier_total      = db.query(func.count(CourierShipment.id)).scalar() or 0
    courier_this_year  = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.process_date.like(f"{year_str}-%")
    ).scalar() or 0
    courier_today      = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.process_date == today_str
    ).scalar() or 0
    courier_archived   = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.status == "archived"
    ).scalar() or 0
    courier_carriers   = db.query(func.count(CourierCarrier.id)).filter(
        CourierCarrier.is_active == True
    ).scalar() or 0
    courier_this_month = db.query(func.count(CourierShipment.id)).filter(
        CourierShipment.process_date >= month_start_str,
        CourierShipment.process_date <= month_end_str,
    ).scalar() or 0

    courier_by_carrier = [
        {"name": row[0], "count": row[1]}
        for row in (
            db.query(CourierCarrier.display_name, func.count(CourierShipment.id))
            .join(CourierShipment, CourierShipment.carrier_id == CourierCarrier.id)
            .filter(
                CourierShipment.process_date >= month_start_str,
                CourierShipment.process_date <= month_end_str,
            )
            .group_by(CourierCarrier.id, CourierCarrier.display_name)
            .order_by(func.count(CourierShipment.id).desc())
            .all()
        )
    ]

    return {
        "selected_year":  sel_year,
        "selected_month": sel_month,
        "lkw": {
            "total":      lkw_total,
            "this_year":  lkw_this_year,
            "today":      lkw_today,
            "archived":   lkw_archived,
            "carriers":   lkw_carriers,
            "this_month": lkw_this_month,
            "by_carrier": lkw_by_carrier,
        },
        "courier": {
            "total":      courier_total,
            "this_year":  courier_this_year,
            "today":      courier_today,
            "archived":   courier_archived,
            "carriers":   courier_carriers,
            "this_month": courier_this_month,
            "by_carrier": courier_by_carrier,
        },
    }
