"""FastAPI-Routen für das Kurier-Modul.

Phase 2 deckt zwei Hauptendpunkte ab:
- `POST /fetch-emails`     → nur abrufen (Preview, ohne Persist)
- `POST /process-emails`   → kompletter Ablauf inkl. SQLite-Persistierung
                              und gruppierter Antwort

Daneben:
- `GET  /carriers`         → konfigurierte Carrier (für Frontend-Dropdown)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from datetime import date, datetime
from typing import Optional

log_courier = logging.getLogger("courier.router")

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import (
    CourierArchive,
    CourierCarrier,
    CourierDocument,
    CourierShipment,
    CourierSignature,
    Setting,
    get_db,
)
from models.courier import (
    ArchiveListItem,
    CarrierCreate,
    CarrierGroup,
    CarrierOut,
    CarrierUpdate,
    DocumentOut,
    DocumentPrintToggle,
    PrintSetRules,
    ProcessEmailsResponse,
    ShipmentOut,
    SignatureCreate,
)
from routers.auth import get_current_user, require_admin
from services.carrier_detection import detect_carrier
from services.courier_email import CourierEmail, fetch_courier_emails
from services.courier_parser import parse_subject_ls_numbers
from services.shipment_grouping import (
    AttachmentDraft,
    ShipmentDraft,
    compute_print_set,
    group_into_shipments,
)


router = APIRouter()

_COURIER_ATTACHMENT_ROOT = os.path.join(
    os.path.expanduser("~"), ".handover", "courier_attachments"
)
_FILENAME_SAFE_RE = re.compile(r'[\\/:"*?<>|]+')


# ── Request-Schemas ───────────────────────────────────────

class ProcessEmailsRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD; default = heute


# ── Helpers ───────────────────────────────────────────────

def _parse_process_date(raw: Optional[str]) -> date:
    if not raw:
        return date.today()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiges Datum (erwartet YYYY-MM-DD)")


def _safe_filename(name: str) -> str:
    return _FILENAME_SAFE_RE.sub("_", name).strip().lstrip(".") or "dokument.pdf"


def _save_attachment(content_b64: str, filename: str, process_date: date, email_id: str) -> str:
    folder = os.path.join(_COURIER_ATTACHMENT_ROOT, process_date.isoformat(), _safe_filename(email_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, _safe_filename(filename))
    # Wenn die Datei schon existiert (idempotenter Re-Run), nicht erneut schreiben
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(base64.b64decode(content_b64))
    return path


def _carrier_to_out(c: CourierCarrier) -> CarrierOut:
    try:
        keywords = json.loads(c.detection_keywords or "[]")
    except (json.JSONDecodeError, TypeError):
        keywords = []
    try:
        rules_raw = json.loads(c.print_set_rules or "{}")
        rules = PrintSetRules(
            default=rules_raw.get("default", []),
            overrides=rules_raw.get("overrides", {}),
        )
    except (json.JSONDecodeError, TypeError):
        rules = PrintSetRules(default=[], overrides={})

    return CarrierOut(
        id=c.id,
        name=c.name,
        display_name=c.display_name,
        detection_keywords=keywords,
        print_set_rules=rules,
        is_active=c.is_active,
        created_at=c.created_at,
    )


def _shipment_to_out(s: CourierShipment) -> ShipmentOut:
    try:
        ls_numbers = json.loads(s.delivery_note_numbers or "[]")
    except (json.JSONDecodeError, TypeError):
        ls_numbers = []
    return ShipmentOut(
        id=s.id,
        delivery_note_numbers=ls_numbers,
        carrier_id=s.carrier_id,
        email_id=s.email_id,
        email_subject=s.email_subject,
        email_date=s.email_date,
        process_date=s.process_date,
        status=s.status,
        created_at=s.created_at,
        documents=[DocumentOut.model_validate(d) for d in s.documents],
    )


# ── Routen ────────────────────────────────────────────────

@router.get("/carriers")
def list_carriers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(CourierCarrier)
    if not include_inactive:
        q = q.filter(CourierCarrier.is_active.is_(True))
    carriers = q.order_by(CourierCarrier.created_at).all()
    return [_carrier_to_out(c) for c in carriers]


@router.post("/carriers", response_model=CarrierOut, status_code=201)
def create_carrier(
    payload: CarrierCreate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    _validate_carrier_input(payload.name, payload.detection_keywords, payload.print_set_rules)

    if db.query(CourierCarrier).filter(CourierCarrier.name == payload.name).first():
        raise HTTPException(status_code=409, detail=f"Carrier mit Name '{payload.name}' existiert bereits")

    carrier = CourierCarrier(
        name=payload.name,
        display_name=payload.display_name,
        detection_keywords=json.dumps([k.strip().lower() for k in payload.detection_keywords]),
        print_set_rules=json.dumps(payload.print_set_rules.model_dump()),
        is_active=payload.is_active,
    )
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    return _carrier_to_out(carrier)


@router.put("/carriers/{carrier_id}", response_model=CarrierOut)
def update_carrier(
    carrier_id: int,
    payload: CarrierUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    carrier = db.query(CourierCarrier).filter(CourierCarrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier nicht gefunden")

    if payload.detection_keywords is not None or payload.print_set_rules is not None:
        _validate_carrier_input(
            carrier.name,
            payload.detection_keywords if payload.detection_keywords is not None else json.loads(carrier.detection_keywords),
            payload.print_set_rules if payload.print_set_rules is not None else PrintSetRules(**json.loads(carrier.print_set_rules)),
        )

    if payload.display_name is not None:
        carrier.display_name = payload.display_name
    if payload.detection_keywords is not None:
        carrier.detection_keywords = json.dumps([k.strip().lower() for k in payload.detection_keywords])
    if payload.print_set_rules is not None:
        carrier.print_set_rules = json.dumps(payload.print_set_rules.model_dump())
    if payload.is_active is not None:
        carrier.is_active = payload.is_active

    db.commit()
    db.refresh(carrier)
    return _carrier_to_out(carrier)


@router.delete("/carriers/{carrier_id}", status_code=204)
def delete_carrier(
    carrier_id: int,
    hard: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Soft-Delete (deaktivieren) per Default — historische Sendungen bleiben
    referenziert. `?hard=true` löscht physisch, schlägt aber fehl, sobald
    Sendungen oder Signaturen den Carrier referenzieren.
    """
    carrier = db.query(CourierCarrier).filter(CourierCarrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier nicht gefunden")

    if hard:
        ship_count = db.query(CourierShipment).filter(CourierShipment.carrier_id == carrier_id).count()
        sig_count  = db.query(CourierSignature).filter(CourierSignature.carrier_id == carrier_id).count()
        if ship_count or sig_count:
            raise HTTPException(
                status_code=409,
                detail=f"Carrier hat {ship_count} Sendung(en) und {sig_count} Unterschrift(en) — bitte deaktivieren statt löschen",
            )
        db.delete(carrier)
    else:
        carrier.is_active = False

    db.commit()
    return None


def _validate_carrier_input(name: str, keywords, rules) -> None:
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Name darf nicht leer sein")

    kw_list = list(keywords or [])
    if not kw_list:
        raise HTTPException(status_code=400, detail="Mindestens ein Detection-Keyword erforderlich")
    for k in kw_list:
        if not isinstance(k, str) or not k.strip():
            raise HTTPException(status_code=400, detail="Keywords dürfen nicht leer sein")

    if isinstance(rules, PrintSetRules):
        default = rules.default
        overrides = rules.overrides or {}
    elif isinstance(rules, dict):
        default = rules.get("default") or []
        overrides = rules.get("overrides") or {}
    else:
        raise HTTPException(status_code=400, detail="Ungültige print_set_rules")

    if not default:
        raise HTTPException(status_code=400, detail="Default-Druckset darf nicht leer sein")
    valid_types = {"label", "rechnung", "lieferschein", "pkl", "edec", "to", "other"}
    for d in default:
        if d not in valid_types:
            raise HTTPException(status_code=400, detail=f"Unbekannter Dokumenttyp: {d}")
    for ov_key, ov_list in overrides.items():
        if ov_key.strip().lower() not in [k.strip().lower() for k in kw_list]:
            raise HTTPException(
                status_code=400,
                detail=f"Override-Key '{ov_key}' muss eines der Keywords sein",
            )
        for d in ov_list or []:
            if d not in valid_types:
                raise HTTPException(status_code=400, detail=f"Unbekannter Dokumenttyp im Override: {d}")


@router.get("/shipments", response_model=ProcessEmailsResponse)
def get_shipments(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Persistierte Sendungen eines Tages — ohne IMAP-Abruf.

    Für den initialen Dashboard-Load: schon einmal verarbeitete Mails werden
    direkt aus SQLite gelesen, der User entscheidet dann, ob er via
    `/process-emails` neu pollen will.
    """
    process_date = _parse_process_date(date)
    process_date_str = process_date.isoformat()
    carriers = db.query(CourierCarrier).filter(CourierCarrier.is_active.is_(True)).all()

    total = (
        db.query(CourierShipment)
        .filter(CourierShipment.process_date == process_date_str)
        .count()
    )
    return _build_grouped_response(db, process_date_str, 0, total, carriers)


@router.patch("/documents/{doc_id}/print", response_model=DocumentOut)
def toggle_document_print(
    doc_id: int,
    payload: DocumentPrintToggle,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Druckvorauswahl pro Dokument umschalten."""
    doc = db.query(CourierDocument).filter(CourierDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    doc.should_print = payload.should_print
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/fetch-emails")
def fetch_emails(
    data: ProcessEmailsRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Holt Mails ohne Persistierung — Preview/Debug.

    Antwort enthält pro Mail Betreff, Datum, erkannte LS-Nummern und
    Anhang-Dateinamen + Doc-Type, damit das Frontend ohne weitere
    Verarbeitung anzeigen kann was eingegangen ist.
    """
    process_date = _parse_process_date(data.date)
    try:
        emails = fetch_courier_emails(process_date, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e) or "E-Mail-Abruf fehlgeschlagen")

    out = []
    for em in emails:
        out.append({
            "message_id": em.message_id,
            "subject": em.subject,
            "email_date": em.email_date.isoformat(),
            "ls_numbers": parse_subject_ls_numbers(em.subject),
            "attachments": [{"name": a["name"]} for a in em.attachments],
        })
    return {
        "process_date": process_date.isoformat(),
        "total_emails": len(emails),
        "emails": out,
    }


@router.post("/process-emails", response_model=ProcessEmailsResponse)
def process_emails(
    data: ProcessEmailsRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Kompletter Verarbeitungs-Ablauf:
    1. IMAP-Abruf vom Kurier-Postfach (Vortag 14:30 → Stichtag 14:30)
    2. Pro Mail: Betreff parsen, Carrier erkennen, in Sendungen splitten,
       Anhänge zuordnen, Doc-Type & Druckset setzen
    3. SQLite-Persistierung (idempotent über `email_id` + `process_date`)
    4. Antwort: gruppiert nach Carrier + ungematchte Sendungen separat
    """
    process_date = _parse_process_date(data.date)

    try:
        emails: list[CourierEmail] = fetch_courier_emails(process_date, db)
    except HTTPException:
        raise
    except Exception as e:
        # 502 = Upstream-Problem (IMAP/OAuth/Netz) statt 500 (Server-Bug)
        raise HTTPException(status_code=502, detail=str(e) or "E-Mail-Abruf fehlgeschlagen")

    carriers = db.query(CourierCarrier).filter(CourierCarrier.is_active.is_(True)).all()

    process_date_str = process_date.isoformat()
    total_shipments = 0
    failed_emails: list[dict] = []

    for em in emails:
        # Pro Mail eigene Transaktion: ein Crash bei Mail N darf
        # die bereits committeten Mails 1..N-1 nicht zurückrollen.
        try:
            ls_numbers = parse_subject_ls_numbers(em.subject)
            match = detect_carrier(
                em.subject,
                [a.get("name", "") for a in em.attachments],
                carriers,
            )
            carrier_obj = match.carrier if match else None
            override_key = match.override_key if match else None

            drafts: list[ShipmentDraft] = group_into_shipments(ls_numbers, em.attachments)

            for draft in drafts:
                compute_print_set(draft, carrier_obj, override_key)
                saved = _persist_shipment(
                    db=db,
                    draft=draft,
                    email=em,
                    carrier=carrier_obj,
                    process_date_str=process_date_str,
                )
                if saved:
                    total_shipments += 1
            db.commit()
        except Exception as e:
            db.rollback()
            log_courier.exception("Mail %s konnte nicht verarbeitet werden", em.message_id)
            failed_emails.append({
                "message_id": em.message_id,
                "subject":    em.subject,
                "error":      str(e),
            })
            continue

    # Antwort zusammenbauen — neu laden, damit IDs/Timestamps gefüllt sind
    if failed_emails:
        log_courier.warning("Process-Emails: %d Mails mit Fehler übersprungen", len(failed_emails))
    return _build_grouped_response(db, process_date_str, len(emails), total_shipments, carriers)


def _persist_shipment(
    *,
    db: Session,
    draft: ShipmentDraft,
    email: CourierEmail,
    carrier: Optional[CourierCarrier],
    process_date_str: str,
) -> bool:
    """Legt Shipment + Documents an. Idempotent: existiert bereits eine
    Sendung mit (email_id, process_date, gleiche LS-Nummern) — überspringen.

    Anhänge werden lokal gespeichert (für späteren Druck/Burn-In).
    """
    ls_json = json.dumps(draft.delivery_note_numbers)

    existing = (
        db.query(CourierShipment)
        .filter(
            CourierShipment.email_id == email.message_id,
            CourierShipment.process_date == process_date_str,
            CourierShipment.delivery_note_numbers == ls_json,
        )
        .first()
    )
    if existing is not None:
        return False

    shipment = CourierShipment(
        delivery_note_numbers=ls_json,
        carrier_id=carrier.id if carrier else None,
        email_id=email.message_id,
        email_subject=email.subject,
        email_date=email.email_date,
        process_date=process_date_str,
        status="open",
    )
    db.add(shipment)
    db.flush()  # ID befüllen

    process_date_obj = datetime.strptime(process_date_str, "%Y-%m-%d").date()
    for att in draft.attachments:
        local_path: Optional[str] = None
        if att.content_b64:
            try:
                local_path = _save_attachment(
                    att.content_b64, att.filename, process_date_obj, email.message_id,
                )
            except OSError:
                local_path = None

        db.add(CourierDocument(
            shipment_id=shipment.id,
            filename=att.filename,
            delivery_note_number=att.delivery_note_number,
            document_type=att.document_type,
            local_path=local_path,
            should_print=att.should_print,
            was_printed=False,
        ))
    return True


def _build_grouped_response(
    db: Session,
    process_date_str: str,
    total_emails: int,
    total_shipments: int,
    carriers: list[CourierCarrier],
) -> ProcessEmailsResponse:
    shipments = (
        db.query(CourierShipment)
        .filter(CourierShipment.process_date == process_date_str)
        .order_by(CourierShipment.created_at)
        .all()
    )

    by_carrier: dict[int, list[ShipmentOut]] = {}
    unmatched: list[ShipmentOut] = []
    for s in shipments:
        out = _shipment_to_out(s)
        if s.carrier_id is None:
            unmatched.append(out)
        else:
            by_carrier.setdefault(s.carrier_id, []).append(out)

    # Signatur-Status pro Carrier+Tag aus DB lesen
    sigs = (
        db.query(CourierSignature)
        .filter(CourierSignature.process_date == process_date_str)
        .all()
    )
    signature_by_carrier: dict[int, CourierSignature] = {s.carrier_id: s for s in sigs}

    carrier_groups: list[CarrierGroup] = []
    for c in carriers:
        if c.id in by_carrier:
            sig = signature_by_carrier.get(c.id)
            carrier_groups.append(CarrierGroup(
                carrier=_carrier_to_out(c),
                shipments=by_carrier[c.id],
                signature_status="signed" if sig else "pending",
                signed_at=sig.signed_at if sig else None,
            ))

    return ProcessEmailsResponse(
        process_date=process_date_str,
        total_emails=total_emails,
        total_shipments=total_shipments,
        carrier_groups=carrier_groups,
        unmatched_shipments=unmatched,
    )


# ── Drucken (Phase 4) ─────────────────────────────────────

class PrintResult(BaseModel):
    shipment_id: int
    printed_documents: list[int] = []
    skipped_documents: list[dict] = []   # [{doc_id, filename, reason}]
    status: str                          # neuer Sendungs-Status
    shipment: ShipmentOut


class PrintBatchResult(BaseModel):
    carrier_id: int
    process_date: str
    total_shipments: int
    printed_count: int       # Sendungen mit ≥ 1 erfolgreich gedrucktem Doc
    error_count: int         # Sendungen mit ausschließlich Fehlern
    results: list[PrintResult]


def _get_printer(db: Session) -> str:
    s = db.query(Setting).filter(Setting.key == "printer_name").first()
    val = s.value.strip() if s and s.value else ""
    if not val:
        raise HTTPException(
            status_code=400,
            detail="Kein Drucker konfiguriert — bitte in den Einstellungen setzen",
        )
    return val


def _print_one_shipment(shipment: CourierShipment, printer_name: str) -> PrintResult:
    """Druckt alle Dokumente einer Sendung mit `should_print=True` und gefülltem
    `local_path`. Pro Doc Try/Catch, damit ein Fehler nicht alles abbricht.
    """
    from services.printer import print_document

    printed: list[int] = []
    skipped: list[dict] = []

    for doc in shipment.documents:
        if not doc.should_print:
            continue
        if not doc.local_path:
            skipped.append({"doc_id": doc.id, "filename": doc.filename, "reason": "kein lokaler Pfad"})
            continue
        if not os.path.exists(doc.local_path):
            skipped.append({"doc_id": doc.id, "filename": doc.filename, "reason": "Datei nicht gefunden"})
            continue
        try:
            print_document(doc.local_path, printer_name=printer_name)
            doc.was_printed = True
            printed.append(doc.id)
        except Exception as e:
            skipped.append({"doc_id": doc.id, "filename": doc.filename, "reason": str(e)})

    if printed and shipment.status == "open":
        shipment.status = "printed"

    return PrintResult(
        shipment_id=shipment.id,
        printed_documents=printed,
        skipped_documents=skipped,
        status=shipment.status,
        shipment=_shipment_to_out(shipment),
    )


@router.post("/shipments/{shipment_id}/print", response_model=PrintResult)
def print_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    shipment = db.query(CourierShipment).filter(CourierShipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Sendung nicht gefunden")

    if not any(d.should_print for d in shipment.documents):
        raise HTTPException(status_code=400, detail="Keine Dokumente zum Drucken ausgewählt")

    printer = _get_printer(db)
    result = _print_one_shipment(shipment, printer)
    db.commit()
    db.refresh(shipment)
    result.shipment = _shipment_to_out(shipment)
    return result


@router.post("/carriers/{carrier_id}/print-all", response_model=PrintBatchResult)
def print_all_for_carrier(
    carrier_id: int,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    process_date = _parse_process_date(date)
    process_date_str = process_date.isoformat()

    carrier = db.query(CourierCarrier).filter(CourierCarrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier nicht gefunden")

    # Sendungen, die noch nicht archiviert/unterschrieben sind
    shipments = (
        db.query(CourierShipment)
        .filter(
            CourierShipment.carrier_id == carrier_id,
            CourierShipment.process_date == process_date_str,
            CourierShipment.status.in_(["open", "printed"]),
        )
        .order_by(CourierShipment.created_at)
        .all()
    )

    if not shipments:
        raise HTTPException(status_code=400, detail="Keine druckbaren Sendungen für diesen Carrier")

    printer = _get_printer(db)
    results: list[PrintResult] = []
    printed_count = 0
    error_count = 0

    for sh in shipments:
        if not any(d.should_print for d in sh.documents):
            results.append(PrintResult(
                shipment_id=sh.id,
                printed_documents=[],
                skipped_documents=[{"doc_id": -1, "filename": "", "reason": "keine Auswahl"}],
                status=sh.status,
                shipment=_shipment_to_out(sh),
            ))
            error_count += 1
            continue

        r = _print_one_shipment(sh, printer)
        results.append(r)
        if r.printed_documents:
            printed_count += 1
        else:
            error_count += 1

    db.commit()

    # Frische ShipmentOuts mit aktuellem Status
    refreshed: list[PrintResult] = []
    for r in results:
        sh = db.query(CourierShipment).filter(CourierShipment.id == r.shipment_id).first()
        if sh:
            r.shipment = _shipment_to_out(sh)
            r.status = sh.status
        refreshed.append(r)

    return PrintBatchResult(
        carrier_id=carrier_id,
        process_date=process_date_str,
        total_shipments=len(shipments),
        printed_count=printed_count,
        error_count=error_count,
        results=refreshed,
    )


@router.get("/documents/{doc_id}/file")
def get_document_file(
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Liefert die PDF-Datei eines Dokuments inline (für Vorschau im Modal)."""
    doc = db.query(CourierDocument).filter(CourierDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    if not doc.local_path or not os.path.exists(doc.local_path):
        raise HTTPException(status_code=404, detail="PDF lokal nicht verfügbar")
    return FileResponse(
        doc.local_path,
        media_type="application/pdf",
        filename=doc.filename,
    )


# ── Unterschrift & Archivierung (Phase 5) ─────────────────

_DEFAULT_COURIER_ARCHIVE = os.path.join(os.path.expanduser("~"), ".handover", "courier_archive")


class SignArchiveError(BaseModel):
    shipment_id: int
    delivery_note_numbers: list[str] = []
    reason: str


class SignCarrierResult(BaseModel):
    signature_id: int
    carrier_id: int
    process_date: str
    archived_count: int                     # Sendungen mit erfolgreichem Burn-In
    error_count: int                        # Sendungen mit Fehler
    errors: list[SignArchiveError] = []
    shipments: list[ShipmentOut] = []       # aktualisierte Sendungen (Status=archived)


def _get_courier_archive_path(db: Session) -> str:
    s = db.query(Setting).filter(Setting.key == "courier_archive_path").first()
    val = s.value.strip() if s and s.value else ""
    return val or _DEFAULT_COURIER_ARCHIVE


def _select_burn_target(shipment: CourierShipment) -> Optional[CourierDocument]:
    """Welches Doc bekommt die Unterschrift?

    Priorität (laut Spec): PKL > Lieferschein > erstes Doc mit lokalem Pfad.
    """
    docs = [d for d in shipment.documents if d.local_path and os.path.exists(d.local_path)]
    if not docs:
        return None
    by_type: dict[str, CourierDocument] = {}
    for d in docs:
        by_type.setdefault(d.document_type, d)
    return by_type.get("pkl") or by_type.get("lieferschein") or docs[0]


def _safe_segment(value: str) -> str:
    return _FILENAME_SAFE_RE.sub("_", value).strip().lstrip(".") or "_"


def _archive_signed_pdf(
    *,
    target_doc: CourierDocument,
    signature_b64: str,
    signer_name: str,
    carrier: CourierCarrier,
    archive_root: str,
    process_date_str: str,
    shipment: CourierShipment,
) -> str:
    """Brennt die Unterschrift in das Ziel-PDF und legt es im Kurier-Archiv ab."""
    from services.pdf_sign import embed_signature_in_pdf

    with open(target_doc.local_path, "rb") as f:
        pdf_bytes = f.read()

    archive_dir = os.path.join(
        archive_root,
        _safe_segment(process_date_str),
        _safe_segment(carrier.name),
    )
    safe_original = _safe_segment(target_doc.filename) or "dokument.pdf"
    out_filename = f"signed_{safe_original}"
    if not out_filename.lower().endswith(".pdf"):
        out_filename += ".pdf"

    return embed_signature_in_pdf(
        pdf_bytes=pdf_bytes,
        signature_png_base64=signature_b64,
        signer_name=signer_name or "",
        archive_dir=archive_dir,
        filename=out_filename,
        carrier_name=carrier.display_name or "",
        truck_plate="",
        employee_name=signer_name or "",
        sign_date=datetime.now().strftime("%d.%m.%Y"),
    )


@router.post("/carriers/{carrier_id}/sign", response_model=SignCarrierResult)
def sign_carrier_group(
    carrier_id: int,
    payload: SignatureCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Erfasst eine Sammel-Unterschrift für einen Carrier an einem Tag.

    Brennt die Unterschrift auf PKL/Lieferschein jeder Sendung der Gruppe,
    legt das signierte PDF im Kurier-Archiv ab, persistiert
    `CourierSignature` + `CourierArchive`-Einträge und setzt den
    Sendungs-Status auf `archived`.

    Idempotenz: existiert für (carrier_id, process_date) bereits eine
    Signatur, wird 409 zurückgegeben — User muss bestehende erst löschen
    (manuell, oder später via UI).
    """
    process_date_str = payload.process_date
    try:
        datetime.strptime(process_date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiges Datum (YYYY-MM-DD)")

    carrier = db.query(CourierCarrier).filter(CourierCarrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier nicht gefunden")

    existing_sig = (
        db.query(CourierSignature)
        .filter(
            CourierSignature.carrier_id == carrier_id,
            CourierSignature.process_date == process_date_str,
        )
        .first()
    )
    if existing_sig:
        raise HTTPException(
            status_code=409,
            detail="Für diesen Carrier und Tag existiert bereits eine Unterschrift",
        )

    shipments = (
        db.query(CourierShipment)
        .filter(
            CourierShipment.carrier_id == carrier_id,
            CourierShipment.process_date == process_date_str,
            CourierShipment.status != "archived",
        )
        .order_by(CourierShipment.created_at)
        .all()
    )
    if not shipments:
        raise HTTPException(
            status_code=400,
            detail="Keine archivierbaren Sendungen für diesen Carrier",
        )

    if not payload.signature_data or not payload.signature_data.strip():
        raise HTTPException(status_code=400, detail="Unterschrift fehlt")

    archive_root = _get_courier_archive_path(db)
    os.makedirs(archive_root, exist_ok=True)

    signed_at = datetime.utcnow()
    sig = CourierSignature(
        carrier_id=carrier_id,
        process_date=process_date_str,
        signature_data=payload.signature_data,
        signer_name=payload.signer_name,
        signed_at=signed_at,
    )
    db.add(sig)
    db.flush()

    archived_count = 0
    errors: list[SignArchiveError] = []

    for shipment in shipments:
        ls_numbers = []
        try:
            ls_numbers = json.loads(shipment.delivery_note_numbers) or []
        except (json.JSONDecodeError, TypeError):
            ls_numbers = []

        target = _select_burn_target(shipment)
        if not target:
            errors.append(SignArchiveError(
                shipment_id=shipment.id,
                delivery_note_numbers=ls_numbers,
                reason="Kein druckbares Dokument mit lokalem Pfad",
            ))
            continue

        try:
            archived_path = _archive_signed_pdf(
                target_doc=target,
                signature_b64=payload.signature_data,
                signer_name=payload.signer_name or "",
                carrier=carrier,
                archive_root=archive_root,
                process_date_str=process_date_str,
                shipment=shipment,
            )
        except Exception as e:
            errors.append(SignArchiveError(
                shipment_id=shipment.id,
                delivery_note_numbers=ls_numbers,
                reason=str(e),
            ))
            continue

        db.add(CourierArchive(
            shipment_id=shipment.id,
            signature_id=sig.id,
            signed_document_path=archived_path,
            archive_path=archived_path,
        ))
        shipment.status = "archived"
        archived_count += 1

    # Wenn nichts archiviert wurde → Signature-Eintrag wieder rausnehmen, sonst hängt sie nutzlos rum
    if archived_count == 0:
        db.rollback()
        return SignCarrierResult(
            signature_id=0,
            carrier_id=carrier_id,
            process_date=process_date_str,
            archived_count=0,
            error_count=len(errors),
            errors=errors,
            shipments=[],
        )

    db.commit()
    db.refresh(sig)

    refreshed = (
        db.query(CourierShipment)
        .filter(
            CourierShipment.carrier_id == carrier_id,
            CourierShipment.process_date == process_date_str,
        )
        .all()
    )

    return SignCarrierResult(
        signature_id=sig.id,
        carrier_id=carrier_id,
        process_date=process_date_str,
        archived_count=archived_count,
        error_count=len(errors),
        errors=errors,
        shipments=[_shipment_to_out(s) for s in refreshed],
    )


# ── Archiv-Übersicht (Kurier-Archiv-Page) ─────────────────

@router.get("/archive", response_model=list[ArchiveListItem])
def list_archive(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    carrier_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Archivierte Kurier-Sendungen durchsuchen.

    Filter:
    - ``date_from`` / ``date_to``: Verarbeitungstag (YYYY-MM-DD), beide optional.
      Default: alle Einträge — die UI sollte typischerweise einen 30-Tage-Default
      setzen.
    - ``carrier_id``: optional einschränken.
    """
    q = (
        db.query(CourierArchive, CourierShipment, CourierCarrier, CourierSignature)
        .join(CourierShipment, CourierArchive.shipment_id == CourierShipment.id)
        .join(CourierCarrier, CourierShipment.carrier_id == CourierCarrier.id)
        .join(CourierSignature, CourierArchive.signature_id == CourierSignature.id)
        .order_by(CourierArchive.archived_at.desc())
    )

    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from muss YYYY-MM-DD sein")
        q = q.filter(CourierShipment.process_date >= date_from)
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to muss YYYY-MM-DD sein")
        q = q.filter(CourierShipment.process_date <= date_to)
    if carrier_id is not None:
        q = q.filter(CourierShipment.carrier_id == carrier_id)

    items: list[ArchiveListItem] = []
    for arch, ship, carrier, sig in q.all():
        try:
            ls = json.loads(ship.delivery_note_numbers) or []
        except (json.JSONDecodeError, TypeError):
            ls = []
        items.append(ArchiveListItem(
            archive_id=arch.id,
            archived_at=arch.archived_at,
            process_date=ship.process_date,
            signed_document_path=arch.signed_document_path,
            delivery_note_numbers=ls,
            email_subject=ship.email_subject,
            email_date=ship.email_date,
            carrier_id=carrier.id,
            carrier_name=carrier.name,
            carrier_display_name=carrier.display_name,
            signer_name=sig.signer_name,
            signed_at=sig.signed_at,
        ))
    return items


@router.get("/archive/{archive_id}/file")
def get_archive_file(
    archive_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    arch = db.query(CourierArchive).filter(CourierArchive.id == archive_id).first()
    if not arch:
        raise HTTPException(status_code=404, detail="Archiv-Eintrag nicht gefunden")
    if not arch.signed_document_path or not os.path.exists(arch.signed_document_path):
        raise HTTPException(status_code=404, detail="Signiertes PDF nicht mehr vorhanden")
    return FileResponse(
        arch.signed_document_path,
        media_type="application/pdf",
        filename=os.path.basename(arch.signed_document_path),
    )
