"""IMAP-Abruf für das Kurier-Postfach.

Wiederverwendung der bestehenden OAuth-Engine (`services.outlook_service`):
- Gleicher Access-Token.
- Postfach-Adresse stammt aus Setting `courier_mailbox` (Fallback:
  `outlook_email` — also das Hauptkonto), damit Shared Mailboxes über
  den selben OAuth-Token erreichbar sind.

Zeitfenster: laut Adam **Vortag 14:30 bis Heute 14:30** (Lokal-Zeit).
Beim IMAP `SEARCH` filtern wir grob mit `SINCE` (Tag-Granularität) und
schneiden danach im Code exakt auf das gewünschte Fenster zu.
"""

from __future__ import annotations

import base64
import email
import imaplib
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

from services.outlook_service import (
    _decode_header_str,
    _refresh_access_token,
    get_outlook_config,
)


@dataclass
class CourierEmail:
    """Eine abgerufene Kurier-Mail mit ihren PDF-Anhängen."""
    message_id: str          # IMAP-Sequence-ID (lokal eindeutig im Postfach)
    subject: str
    email_date: datetime     # naive local time (im Cutoff-Fenster)
    attachments: list[dict]  # [{name, content (base64), source}]


# ── Zeitfenster ───────────────────────────────────────────

CUTOFF_HOUR = 14
CUTOFF_MINUTE = 30


def cutoff_window(process_date: date) -> tuple[datetime, datetime]:
    """(Start, Ende) für einen Stichtag — Vortag 14:30 bis Stichtag 14:30."""
    end = datetime.combine(process_date, time(CUTOFF_HOUR, CUTOFF_MINUTE))
    start = end - timedelta(days=1)
    return start, end


def _imap_since_token(start: datetime) -> str:
    """IMAP-SEARCH erwartet `DD-Mon-YYYY` ohne Uhrzeit. Wir setzen einen
    Tag früher, damit Mails am Cutoff-Beginn (14:30) sicher mitgeladen
    werden — die exakte Filterung passiert danach im Code."""
    safe = (start - timedelta(days=0)).date()
    return safe.strftime("%d-%b-%Y")


def _to_naive_local(dt: datetime) -> datetime:
    """tz-aware → naive lokale Zeit. tz-naive bleibt unverändert."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


# ── Settings-Helper ───────────────────────────────────────

def _get_setting(db, key: str) -> str:
    from database import Setting
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value else ""


def _get_courier_mailbox(db, fallback: str) -> str:
    val = _get_setting(db, "courier_mailbox")
    return val or fallback


# ── IMAP-Abruf ────────────────────────────────────────────

def fetch_courier_emails(process_date: date, db) -> list[CourierEmail]:
    """Holt alle Kurier-Mails im Cutoff-Fenster für den angegebenen Stichtag.

    Wirft Exception bei fehlendem OAuth-Token oder IMAP-Fehler.
    """
    config = get_outlook_config(db)
    if config.get("outlook_type") == "exchange":
        # Exchange-Pfad bewusst (noch) nicht unterstützt — Adam nutzt OAuth.
        raise Exception("Kurier-Modul erwartet OAuth/IMAP — Exchange-Pfad nicht implementiert")

    if not config.get("outlook_access_token"):
        raise Exception("Kein OAuth2 Token — bitte zuerst mit Microsoft anmelden")

    mailbox = _get_courier_mailbox(db, config.get("outlook_email", ""))
    if not mailbox:
        raise Exception("Kein Kurier-Postfach gesetzt (Settings → courier_mailbox)")

    imap_server = config.get("outlook_imap_server", "") or "outlook.office365.com"
    cutoff_start, cutoff_end = cutoff_window(process_date)
    since_token = _imap_since_token(cutoff_start)

    def _do_fetch(token: str) -> list[CourierEmail]:
        auth_bytes = f"user={mailbox}\x01auth=Bearer {token}\x01\x01".encode()
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        try:
            mail.authenticate("XOAUTH2", lambda x: auth_bytes)
            mail.select("INBOX")

            _, msg_ids = mail.search(None, f'(SINCE "{since_token}")')
            ids = msg_ids[0].split() if msg_ids and msg_ids[0] else []

            results: list[CourierEmail] = []
            for msg_id in ids:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])

                # Datum prüfen
                raw_date = msg.get("Date")
                if not raw_date:
                    continue
                try:
                    parsed = parsedate_to_datetime(raw_date)
                except (TypeError, ValueError):
                    continue
                local_dt = _to_naive_local(parsed)
                if not (cutoff_start <= local_dt < cutoff_end):
                    continue

                subject = _decode_header_str(msg.get("Subject"))
                attachments: list[dict] = []
                for part in msg.walk():
                    if part.get_content_type() != "application/pdf":
                        continue
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    filename = _decode_header_str(part.get_filename() or "dokument.pdf")
                    attachments.append({
                        "id": f"{msg_id.decode()}_{filename}",
                        "name": filename,
                        "content": base64.b64encode(payload).decode(),
                        "source": "courier_imap_oauth",
                    })

                results.append(CourierEmail(
                    message_id=msg_id.decode(),
                    subject=subject,
                    email_date=local_dt,
                    attachments=attachments,
                ))

            return results
        finally:
            try:
                mail.logout()
            except Exception:
                pass

    try:
        return _do_fetch(config["outlook_access_token"])
    except imaplib.IMAP4.error:
        new_token = _refresh_access_token(config, db)
        return _do_fetch(new_token)
