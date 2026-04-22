from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from sqlalchemy.orm import Session
from database import Handover, Setting
from datetime import datetime
import os, base64

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
ARCHIVE_DIR  = os.path.join(os.path.expanduser("~"), ".handover", "archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def get_setting(db: Session, key: str) -> str:
    from database import Setting
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else ""


def generate_pdf(handover: Handover, db: Session, signature: str = None, employee_name: str = None, sign_date: str = None) -> str:
    """
    Generiert ein PDF aus dem HTML-Template.
    Wenn signature übergeben wird → finales Archiv-PDF mit Unterschrift.
    """
    company_name    = get_setting(db, "company_name")
    company_address = get_setting(db, "company_address")
    company_logo    = get_setting(db, "company_logo_b64")

    carrier_name = handover.carrier.company_name if handover.carrier else "—"

    template_data = {
        "company_name":    company_name,
        "company_address": company_address,
        "company_logo":    company_logo,
        "referenz":        handover.referenz,
        "datum":           handover.created_at.strftime("%d.%m.%Y  %H:%M Uhr"),
        "carrier_name":    carrier_name,
        "truck_plate":     handover.truck_plate or "—",
        "driver_name":     handover.driver_name or "—",
        "signature_png":   signature,
        "signed_at":       datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S UTC") if signature else None,
        "employee_name":   employee_name or "",
        "sign_date":       sign_date or datetime.utcnow().strftime("%d.%m.%Y"),
    }

    template = jinja_env.get_template("handover.html")
    html_content = template.render(**template_data)

    filename = f"handover_{handover.id}_{handover.referenz}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(ARCHIVE_DIR, filename)

    HTML(string=html_content).write_pdf(pdf_path)
    return pdf_path
