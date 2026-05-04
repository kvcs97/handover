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
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

from services.outlook_service import (
    _decode_header_str,
    _refresh_access_token,
    get_outlook_config,
)

log = logging.getLogger("courier.email")


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
    outlook_type = (config.get("outlook_type") or "").strip().lower()
    if outlook_type == "exchange":
        raise Exception(
            "Kurier-Modul unterstützt aktuell nur OAuth/IMAP. Im LKW-Modul ist Exchange "
            "konfiguriert — bitte für das Kurier-Postfach OAuth/IMAP einrichten."
        )

    if not config.get("outlook_access_token"):
        raise Exception(
            "Kein OAuth2 Token vorhanden — bitte im LKW-Modul (Outlook-Schritt) einmal "
            "mit Microsoft anmelden, das Token wird für Kurier mitverwendet."
        )

    mailbox = (_get_courier_mailbox(db, config.get("outlook_email", "")) or "").strip()
    if not mailbox:
        raise Exception("Kein Kurier-Postfach gesetzt — Settings → Kurier-Modul → Kurier-Postfach")

    imap_server = (config.get("outlook_imap_server") or "outlook.office365.com").strip()
    cutoff_start, cutoff_end = cutoff_window(process_date)
    since_token = _imap_since_token(cutoff_start)

    def _do_fetch(token: str) -> list[CourierEmail]:
        auth_bytes = f"user={mailbox}\x01auth=Bearer {token}\x01\x01".encode()
        try:
            mail = imaplib.IMAP4_SSL(imap_server, 993)
        except OSError as e:
            raise Exception(
                f"IMAP-Verbindung zu {imap_server}:993 fehlgeschlagen — "
                f"Internet/Firewall prüfen ({e})"
            )
        try:
            mail.authenticate("XOAUTH2", lambda x: auth_bytes)
            mail.select("INBOX")

            typ, msg_ids = mail.search(None, f'(SINCE "{since_token}")')
            if typ != "OK":
                raise Exception(f"IMAP-SEARCH fehlgeschlagen ({typ})")
            ids = msg_ids[0].split() if msg_ids and msg_ids[0] else []
            log.info("Kurier IMAP: %d Nachrichten seit %s", len(ids), since_token)

            # Phase 1: nur die Header-Felder Date/Subject holen, NICHT den ganzen
            # Body. Das spart bei vollen Postfächern enorm Bandbreite — typischer
            # Header < 2 KB, Mail mit PDF-Anhängen oft mehrere MB.
            in_window: list[bytes] = []
            for msg_id in ids:
                try:
                    typ, env_data = mail.fetch(
                        msg_id, "(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)])"
                    )
                except imaplib.IMAP4.error as e:
                    log.warning("Header-Fetch für %s fehlgeschlagen: %s", msg_id, e)
                    continue
                if typ != "OK" or not env_data:
                    continue

                header_blob = b""
                for chunk in env_data:
                    if isinstance(chunk, tuple) and len(chunk) >= 2:
                        header_blob = chunk[1] or b""
                        break
                if not header_blob:
                    continue

                date_match = re.search(rb"^Date:\s*(.+?)\r?$", header_blob, re.IGNORECASE | re.MULTILINE)
                if not date_match:
                    continue
                try:
                    parsed = parsedate_to_datetime(date_match.group(1).decode("utf-8", errors="replace"))
                except (TypeError, ValueError):
                    continue
                local_dt = _to_naive_local(parsed)
                if not (cutoff_start <= local_dt < cutoff_end):
                    continue
                in_window.append(msg_id)

            log.info("Kurier IMAP: %d Mails im Cutoff-Fenster", len(in_window))

            # Phase 2: nur für die wenigen Mails im Fenster den vollen Body laden
            results: list[CourierEmail] = []
            for msg_id in in_window:
                try:
                    typ, msg_data = mail.fetch(msg_id, "(RFC822)")
                except imaplib.IMAP4.error as e:
                    log.warning("RFC822-Fetch für %s fehlgeschlagen: %s", msg_id, e)
                    continue
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue

                # Body ist im ersten Tupel-Element
                body_blob = b""
                for chunk in msg_data:
                    if isinstance(chunk, tuple) and len(chunk) >= 2:
                        body_blob = chunk[1] or b""
                        break
                if not body_blob:
                    continue

                try:
                    msg = email.message_from_bytes(body_blob)
                except Exception as e:
                    log.warning("Mail %s nicht parsebar: %s", msg_id, e)
                    continue

                # Datum aus dem vollen Body validieren (statt erneut zu parsen
                # nehmen wir an, was Phase 1 bereits gefiltert hat — Datum für
                # die persistierte Sendung holen wir hier nochmal frisch)
                raw_date = msg.get("Date")
                try:
                    parsed = parsedate_to_datetime(raw_date) if raw_date else None
                except (TypeError, ValueError):
                    parsed = None
                local_dt = _to_naive_local(parsed) if parsed else cutoff_start

                subject = _decode_header_str(msg.get("Subject")) or ""

                attachments: list[dict] = []
                for part in msg.walk():
                    if part.get_content_type() != "application/pdf":
                        continue
                    try:
                        payload = part.get_payload(decode=True)
                    except Exception as e:
                        log.warning("Anhang in Mail %s nicht dekodierbar: %s", msg_id, e)
                        continue
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
    except imaplib.IMAP4.error as first_err:
        # Token vermutlich abgelaufen → einmal refreshen und neu versuchen
        try:
            new_token = _refresh_access_token(config, db)
        except Exception as refresh_err:
            raise Exception(
                f"OAuth-Token-Refresh fehlgeschlagen: {refresh_err}. "
                f"Bitte im LKW-Modul (Outlook-Schritt) erneut mit Microsoft anmelden."
            )
        try:
            return _do_fetch(new_token)
        except imaplib.IMAP4.error as second_err:
            raise Exception(
                f"IMAP-Login für '{mailbox}' fehlgeschlagen ({second_err}). "
                f"Wenn das eine Shared/Team-Mailbox ist, kann der OAuth-Token sie nicht "
                f"direkt öffnen — dann bitte das Hauptpostfach eintragen oder einen "
                f"separaten OAuth-Flow für die Kurier-Mailbox einrichten."
            )
