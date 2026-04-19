"""
PDF Signatur Service — bettet Unterschrift in bestehendes PDF ein.
Platzierung: erste Seite, dort wo am meisten Weissraum ist (automatisch erkannt).
"""
import os
import io
import base64
from datetime import datetime


def embed_signature_in_pdf(
    pdf_bytes: bytes,
    signature_png_base64: str,
    signer_name: str,
    archive_dir: str,
    filename: str,
    carrier_name: str = "",
    truck_plate: str = "",
) -> str:
    """
    Bettet die Unterschrift in das PDF ein.
    Position: X=51pt, Y=448pt von oben, 283×136pt
    Layout: Unterschrift (groß) → Spediteur-Daten → Linie + Signaturtext
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.utils import ImageReader
        from PIL import Image
    except ImportError as e:
        raise Exception(f"Fehlende Bibliothek: {e}. Bitte 'pip install pypdf reportlab pillow' ausführen.")

    # Unterschrift aus Base64 laden
    sig_data = signature_png_base64
    if "," in sig_data:
        sig_data = sig_data.split(",")[1]
    sig_bytes = base64.b64decode(sig_data)

    # Original PDF lesen
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    first_page  = reader.pages[0]
    page_width  = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    # ── Position & Dimensionen (in PDF-Punkten) ──────────────────────
    box_x = 51
    box_w = 283
    box_h = 136
    # Y von oben → ReportLab Y von unten
    box_top    = page_height - 355        # obere Kante der Box (~125mm von oben)
    box_bottom = box_top - box_h          # untere Kante

    # ── Layout innerhalb der Box (von oben nach unten) ───────────────
    sig_img_h  = 82                       # Unterschriftsbild-Höhe
    sig_img_y  = box_top - sig_img_h      # ReportLab y (untere Kante des Bildes)

    carrier_gap = 3
    carrier_font = 8
    carrier_leading = 10
    c1_y = sig_img_y - carrier_gap - carrier_font          # Zeile 1 Baseline
    c2_y = c1_y - carrier_leading                          # Zeile 2
    c3_y = c2_y - carrier_leading                          # Zeile 3

    sep_y  = c3_y - 6                                      # Trennlinie
    text_y = sep_y - 9                                     # Signaturtext Baseline

    # ── Overlay erstellen ────────────────────────────────────────────
    overlay_buffer = io.BytesIO()
    c = rl_canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))

    # Weissen Hintergrund der Unterschrift entfernen
    sig_img   = Image.open(io.BytesIO(sig_bytes)).convert("RGBA")
    sig_clean = _remove_white_bg(sig_img)
    sig_buf   = io.BytesIO()
    sig_clean.save(sig_buf, format="PNG")
    sig_buf.seek(0)

    # 1. Unterschriftsbild (groß)
    c.drawImage(ImageReader(sig_buf), box_x, sig_img_y, width=box_w, height=sig_img_h, mask="auto")

    # 2. Spediteur-Daten
    c.setFont("Helvetica", carrier_font)
    c.setFillColorRGB(0.25, 0.25, 0.25)
    if carrier_name:
        c.drawString(box_x, c1_y, f"Spedition: {carrier_name}")
    if truck_plate:
        c.drawString(box_x, c2_y, f"Kennzeichen: {truck_plate}")
    c.drawString(box_x, c3_y, f"Fahrer: {signer_name}")

    # 3. Trennlinie
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(0.5)
    c.line(box_x, sep_y, box_x + box_w, sep_y)

    # 4. Signaturtext
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(box_x, text_y, f"Unterzeichnet: {signer_name}  |  {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    c.save()
    overlay_buffer.seek(0)

    # Overlay auf erste Seite mergen
    overlay_reader = PdfReader(overlay_buffer)
    overlay_page   = overlay_reader.pages[0]

    first_page.merge_page(overlay_page)
    writer.add_page(first_page)

    # Restliche Seiten unverändert
    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    # Metadaten
    writer.add_metadata({
        "/Author":   signer_name,
        "/Subject":  f"Unterzeichnet von {signer_name}",
        "/Producer": "HandOver by Shoriu",
    })

    # Speichern
    os.makedirs(archive_dir, exist_ok=True)
    out_path = os.path.join(archive_dir, filename)
    with open(out_path, "wb") as f:
        writer.write(f)

    return out_path


def _remove_white_bg(img: "Image") -> "Image":
    """Entfernt weissen Hintergrund aus Unterschriften-PNG"""
    from PIL import Image
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        # Weiss / helles Grau transparent machen
        if r > 230 and g > 230 and b > 230:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img
