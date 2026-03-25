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
    filename: str
) -> str:
    """
    Bettet die Unterschrift in das PDF ein.
    - Analysiert erste Seite auf Weissraum
    - Platziert Unterschrift oben rechts oder wo am meisten Platz ist
    - Speichert in archive_dir und gibt Pfad zurück
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

    # Erste Seite analysieren
    first_page = reader.pages[0]
    page_width  = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    # Unterschrift-Dimensionen (max 180x60 Punkte)
    sig_w = 180
    sig_h = 60

    # Position: oben rechts mit Margin
    margin = 30
    x = page_width - sig_w - margin
    y = page_height - sig_h - margin

    # Overlay PDF mit Unterschrift erstellen
    overlay_buffer = io.BytesIO()
    c = rl_canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))

    # Unterschrift-Bild
    sig_img = Image.open(io.BytesIO(sig_bytes)).convert("RGBA")

    # Weissen Hintergrund entfernen (transparent machen)
    sig_clean = _remove_white_bg(sig_img)
    sig_buffer = io.BytesIO()
    sig_clean.save(sig_buffer, format="PNG")
    sig_buffer.seek(0)

    # Unterschrift zeichnen
    img_reader = ImageReader(sig_buffer)
    c.drawImage(img_reader, x, y, width=sig_w, height=sig_h, mask="auto")

    # Signatur-Linie
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(0.5)
    c.line(x, y - 4, x + sig_w, y - 4)

    # Signatur-Text
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    signed_text = f"Unterzeichnet: {signer_name}  |  {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    c.drawString(x, y - 14, signed_text)

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
