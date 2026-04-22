"""
PDF-Generierung für HandOver Übergabeprotokoll.
Nutzt ReportLab (Windows-zuverlässig, keine GTK-Abhängigkeiten).
Bettet Unterschrift direkt als Bild ein — kein HTML-Rendering nötig.
"""
import os
import io
import base64
from datetime import datetime
from sqlalchemy.orm import Session
from database import Handover, Setting

_DEFAULT_ARCHIVE_DIR = os.path.join(os.path.expanduser("~"), ".handover", "archive")


def get_setting(db: Session, key: str) -> str:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value else ""


def _get_archive_dir(db: Session) -> str:
    configured = get_setting(db, "archive_path")
    archive_dir = configured or _DEFAULT_ARCHIVE_DIR
    os.makedirs(archive_dir, exist_ok=True)
    return archive_dir


def _decode_signature(signature: str) -> bytes:
    """Entfernt Data-URL-Präfix und dekodiert Base64."""
    data = signature
    if "," in data:
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def _remove_white_bg(img):
    from PIL import Image
    img = img.convert("RGBA")
    pixels = img.getdata()
    new_pixels = []
    for r, g, b, a in pixels:
        if r > 230 and g > 230 and b > 230:
            new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append((r, g, b, a))
    img.putdata(new_pixels)
    return img


def generate_pdf(
    handover: Handover,
    db: Session,
    signature: str = None,
    employee_name: str = None,
    sign_date: str = None,
) -> str:
    """
    Erzeugt das Übergabeprotokoll-PDF. Wenn `signature` (PNG Base64) übergeben wird,
    wird die Unterschrift im Empfangsbestätigungs-Bereich eingebrannt.
    Wirft Exception bei Fehler — der Caller entscheidet, ob er sie ignorieren will.
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    company_name    = get_setting(db, "company_name")
    company_address = get_setting(db, "company_address")
    company_logo_b64 = get_setting(db, "company_logo_b64")

    carrier_name = handover.carrier.company_name if handover.carrier else "—"
    truck_plate  = handover.truck_plate or "—"
    driver_name  = handover.driver_name or "—"
    referenz     = handover.referenz
    datum        = handover.created_at.strftime("%d.%m.%Y  %H:%M Uhr")

    archive_dir = _get_archive_dir(db)
    filename    = f"handover_{handover.id}_{referenz}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path    = os.path.join(archive_dir, filename)

    page_w, page_h = A4
    c = rl_canvas.Canvas(pdf_path, pagesize=A4)
    left   = 40
    right  = page_w - 40
    cursor = page_h - 50

    # ── Header ──────────────────────────────────────────────
    if company_logo_b64:
        try:
            logo_bytes = base64.b64decode(company_logo_b64)
            logo_img   = Image.open(io.BytesIO(logo_bytes))
            logo_buf   = io.BytesIO()
            logo_img.save(logo_buf, format="PNG")
            logo_buf.seek(0)
            c.drawImage(ImageReader(logo_buf), left, cursor - 40,
                        width=140, height=40, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.11, 0.11, 0.12)
    c.drawString(left, cursor - 62, company_name or "")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.43, 0.43, 0.45)
    c.drawString(left, cursor - 78, company_address or "")

    # Rechte Seite — Titel + Referenz
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.11, 0.11, 0.12)
    c.drawRightString(right, cursor, "Übergabeprotokoll")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.75, 0.33, 0.42)
    c.drawRightString(right, cursor - 20, referenz)

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.43, 0.43, 0.45)
    c.drawRightString(right, cursor - 36, datum)

    # Trennlinie
    c.setStrokeColorRGB(0.11, 0.11, 0.12)
    c.setLineWidth(1.2)
    c.line(left, cursor - 95, right, cursor - 95)
    cursor -= 125

    # ── Sektion: Spediteur ──────────────────────────────────
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.43, 0.43, 0.45)
    c.drawString(left, cursor, "SPEDITEUR & FAHRZEUG")
    c.setStrokeColorRGB(0.91, 0.91, 0.93)
    c.setLineWidth(0.5)
    c.line(left, cursor - 6, right, cursor - 6)
    cursor -= 28

    col_w = (right - left) / 3.0
    fields = [
        ("SPEDITION",       carrier_name),
        ("LKW-KENNZEICHEN", truck_plate),
        ("FAHRER",          driver_name),
    ]
    for i, (label, value) in enumerate(fields):
        x = left + i * col_w
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.60, 0.60, 0.62)
        c.drawString(x, cursor + 12, label)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.11, 0.11, 0.12)
        c.drawString(x, cursor - 4, str(value))
    cursor -= 45

    # ── Sektion: Empfangsbestätigung ─────────────────────────
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.43, 0.43, 0.45)
    c.drawString(left, cursor, "EMPFANGSBESTÄTIGUNG")
    c.setStrokeColorRGB(0.91, 0.91, 0.93)
    c.line(left, cursor - 6, right, cursor - 6)
    cursor -= 30

    if signature:
        # Unterschrift-Bild aufbereiten
        try:
            sig_bytes = _decode_signature(signature)
            sig_img   = Image.open(io.BytesIO(sig_bytes))
            sig_clean = _remove_white_bg(sig_img)
            sig_buf   = io.BytesIO()
            sig_clean.save(sig_buf, format="PNG")
            sig_buf.seek(0)

            sig_box_w = 260
            sig_box_h = 90
            sig_box_x = left
            sig_box_y = cursor - sig_box_h

            # Unterschriftsfeld (Hintergrund)
            c.setFillColorRGB(0.98, 0.98, 0.98)
            c.setStrokeColorRGB(0.91, 0.91, 0.93)
            c.roundRect(sig_box_x, sig_box_y, sig_box_w, sig_box_h, 6, stroke=1, fill=1)

            # Signatur zeichnen (mit Rand)
            c.drawImage(
                ImageReader(sig_buf),
                sig_box_x + 8, sig_box_y + 8,
                width=sig_box_w - 16, height=sig_box_h - 16,
                preserveAspectRatio=True, mask="auto",
            )

            # Meta rechts neben der Unterschrift
            meta_x = sig_box_x + sig_box_w + 20

            display_name = employee_name or driver_name
            display_date = sign_date or datetime.now().strftime("%d.%m.%Y")
            signed_at    = datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC")

            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.60, 0.60, 0.62)
            c.drawString(meta_x, sig_box_y + sig_box_h - 12, "UNTERZEICHNET VON")

            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(0.11, 0.11, 0.12)
            c.drawString(meta_x, sig_box_y + sig_box_h - 28, display_name)

            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.60, 0.60, 0.62)
            c.drawString(meta_x, sig_box_y + sig_box_h - 48, "DATUM")
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.11, 0.11, 0.12)
            c.drawString(meta_x, sig_box_y + sig_box_h - 62, display_date)

            c.setFont("Helvetica-Oblique", 7)
            c.setFillColorRGB(0.60, 0.60, 0.62)
            c.drawString(meta_x, sig_box_y + 4, f"Zeitstempel: {signed_at}")

            cursor = sig_box_y - 14

            # Signatur-Label unterhalb
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.43, 0.43, 0.45)
            c.drawString(left, cursor, f"Unterzeichnet: {display_name}  –  {display_date}")
            cursor -= 18

            # Status-Stempel
            c.setStrokeColorRGB(0.16, 0.75, 0.25)
            c.setFillColorRGB(0.16, 0.75, 0.25)
            c.setLineWidth(1.5)
            c.roundRect(left, cursor - 16, 90, 18, 3, stroke=1, fill=0)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(left + 8, cursor - 10, "✓ ARCHIVIERT")
            cursor -= 30
        except Exception as e:
            raise Exception(f"Unterschrift konnte nicht eingebettet werden: {e}")
    else:
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.75, 0.56, 0.00)
        c.drawString(left, cursor, "⚠ Noch nicht unterzeichnet")
        cursor -= 20

    # ── Footer ──────────────────────────────────────────────
    c.setStrokeColorRGB(0.91, 0.91, 0.93)
    c.line(left, 55, right, 55)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.60, 0.60, 0.62)
    c.drawString(left, 40, "Erstellt mit HandOver · shoriu.com/handover")
    c.drawCentredString(page_w / 2, 40, f"{company_name or ''} · {datum}")
    c.drawRightString(right, 40, f"Referenz: {referenz}")

    c.showPage()
    c.save()

    return pdf_path
