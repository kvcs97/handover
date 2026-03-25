from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from services.outlook_service import search_emails_by_reference, get_pdf_bytes
from services.pdf_sign import embed_signature_in_pdf
from services.printer import print_document
from pydantic import BaseModel
from typing import List
import os, base64, tempfile

router = APIRouter()

ARCHIVE_DIR = os.path.join(os.path.expanduser("~"), ".handover", "archive")


class SignPdfRequest(BaseModel):
    attachments:      List[dict]   # Liste der Attachments mit content (Base64)
    sign_indices:     List[int]    # Welche sollen unterschrieben werden (Index)
    signature_png:    str          # Base64 PNG der Unterschrift
    signer_name:      str
    referenz:         str


@router.get("/search/{referenz}")
def search_attachments(referenz: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Sucht E-Mails mit Referenznummer und gibt PDF-Anhänge zurück"""
    try:
        attachments = search_emails_by_reference(referenz, db)
        if not attachments:
            return {"found": False, "attachments": []}

        # Content für Vorschau kürzen (nur Metadaten zurückgeben, kein vollständiger Base64)
        preview = []
        for att in attachments:
            preview.append({
                "id":       att["id"],
                "name":     att["name"],
                "subject":  att["subject"],
                "date":     att["date"],
                "source":   att["source"],
                # Content wird separat abgerufen
            })

        return {"found": True, "attachments": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attachment/{referenz}/{attachment_id}")
def get_attachment(referenz: str, attachment_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gibt vollständigen PDF-Inhalt als Base64 zurück"""
    try:
        attachments = search_emails_by_reference(referenz, db)
        att = next((a for a in attachments if a["id"] == attachment_id), None)
        if not att:
            raise HTTPException(status_code=404, detail="Anhang nicht gefunden")
        return {"content": att["content"], "name": att["name"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
def process_attachments(data: SignPdfRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Verarbeitet PDFs:
    - PDFs ohne Unterschrift → direkt drucken
    - PDFs mit Unterschrift → Unterschrift einbetten, archivieren, drucken
    """
    from database import Setting
    printer_setting = db.query(Setting).filter(Setting.key == "printer_name").first()
    printer_name = printer_setting.value if printer_setting else ""

    results = []

    for i, att in enumerate(data.attachments):
        pdf_bytes = get_pdf_bytes(att)
        needs_sig = i in data.sign_indices
        safe_name = att["name"].replace("/", "_").replace("\\", "_")

        if needs_sig:
            # Unterschrift einbetten
            out_filename = f"signed_{data.referenz}_{safe_name}"
            try:
                signed_path = embed_signature_in_pdf(
                    pdf_bytes=pdf_bytes,
                    signature_png_base64=data.signature_png,
                    signer_name=data.signer_name,
                    archive_dir=ARCHIVE_DIR,
                    filename=out_filename
                )
                # Unterschriebenes PDF drucken
                if printer_name:
                    try:
                        print_document(signed_path, printer_name=printer_name)
                    except Exception as e:
                        print(f"[WARN] Druckfehler: {e}")

                results.append({"name": att["name"], "status": "signed", "path": signed_path})
            except Exception as e:
                results.append({"name": att["name"], "status": "error", "error": str(e)})
        else:
            # Direkt drucken ohne Unterschrift
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(pdf_bytes)
                    tmp_path = f.name
                if printer_name:
                    print_document(tmp_path, printer_name=printer_name)
                os.unlink(tmp_path)
                results.append({"name": att["name"], "status": "printed"})
            except Exception as e:
                results.append({"name": att["name"], "status": "error", "error": str(e)})

    return {"results": results}


class OutlookTestRequest(BaseModel):
    outlook_type:      str
    outlook_email:     str
    outlook_password:  str
    outlook_tenant_id: str = ""
    outlook_client_id: str = ""
    outlook_server:    str = ""

@router.post("/test")
def test_outlook_connection(data: OutlookTestRequest, user=Depends(get_current_user)):
    """Testet die Outlook-Verbindung"""
    try:
        config = {
            "outlook_type":      data.outlook_type,
            "outlook_email":     data.outlook_email,
            "outlook_password":  data.outlook_password,
            "outlook_tenant_id": data.outlook_tenant_id,
            "outlook_client_id": data.outlook_client_id,
            "outlook_server":    data.outlook_server,
        }
        if data.outlook_type == "exchange":
            from exchangelib import Credentials, Account, DELEGATE, Configuration
            credentials = Credentials(data.outlook_email, data.outlook_password)
            cfg = Configuration(server=data.outlook_server, credentials=credentials)
            account = Account(
                primary_smtp_address=data.outlook_email,
                config=cfg, autodiscover=False, access_type=DELEGATE
            )
            # Verbindung testen
            _ = account.inbox.total_count
        else:
            import msal
            authority = f"https://login.microsoftonline.com/{data.outlook_tenant_id}"
            app = msal.PublicClientApplication(data.outlook_client_id, authority=authority)
            result = app.acquire_token_by_username_password(
                username=data.outlook_email,
                password=data.outlook_password,
                scopes=["https://graph.microsoft.com/Mail.Read"]
            )
            if "access_token" not in result:
                raise Exception(result.get("error_description", "Auth fehlgeschlagen"))

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
