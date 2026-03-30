from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from pydantic import BaseModel
from typing import List
import os, base64, tempfile

router = APIRouter()
ARCHIVE_DIR = os.path.join(os.path.expanduser("~"), ".handover", "archive")


class SignPdfRequest(BaseModel):
    attachments:  List[dict]
    sign_indices: List[int]
    signature_png: str
    signer_name:  str
    referenz:     str

class OutlookTestRequest(BaseModel):
    outlook_type:      str
    outlook_email:     str
    outlook_password:  str
    outlook_tenant_id: str = ""
    outlook_client_id: str = ""
    outlook_server:    str = ""


@router.get("/search/{referenz}")
def search_attachments(referenz: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        from services.outlook_service import search_emails_by_reference
        attachments = search_emails_by_reference(referenz, db)
        if not attachments:
            return {"found": False, "attachments": []}
        preview = [{"id": a["id"], "name": a["name"], "subject": a["subject"], "date": a["date"], "source": a["source"]} for a in attachments]
        return {"found": True, "attachments": preview}
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Outlook-Bibliothek nicht verfügbar: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attachment/{referenz}/{attachment_id}")
def get_attachment(referenz: str, attachment_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        from services.outlook_service import search_emails_by_reference
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
    try:
        from services.outlook_service import get_pdf_bytes
        from services.pdf_sign import embed_signature_in_pdf
        from services.printer import print_document
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Bibliothek nicht verfügbar: {e}")

    from database import Setting
    printer = db.query(Setting).filter(Setting.key == "printer_name").first()
    printer_name = printer.value if printer else ""
    results = []

    for i, att in enumerate(data.attachments):
        pdf_bytes = get_pdf_bytes(att)
        safe_name = att["name"].replace("/", "_").replace("\\", "_")
        if i in data.sign_indices:
            try:
                signed_path = embed_signature_in_pdf(
                    pdf_bytes=pdf_bytes,
                    signature_png_base64=data.signature_png,
                    signer_name=data.signer_name,
                    archive_dir=ARCHIVE_DIR,
                    filename=f"signed_{data.referenz}_{safe_name}"
                )
                if printer_name:
                    try: print_document(signed_path, printer_name=printer_name)
                    except Exception as e: print(f"[WARN] Druckfehler: {e}")
                results.append({"name": att["name"], "status": "signed", "path": signed_path})
            except Exception as e:
                results.append({"name": att["name"], "status": "error", "error": str(e)})
        else:
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(pdf_bytes); tmp = f.name
                if printer_name: print_document(tmp, printer_name=printer_name)
                os.unlink(tmp)
                results.append({"name": att["name"], "status": "printed"})
            except Exception as e:
                results.append({"name": att["name"], "status": "error", "error": str(e)})

    return {"results": results}


@router.post("/test")
def test_outlook_connection(data: OutlookTestRequest, user=Depends(get_current_user)):
    try:
        if data.outlook_type == "exchange":
            from exchangelib import Credentials, Account, DELEGATE, Configuration
            credentials = Credentials(data.outlook_email, data.outlook_password)
            cfg = Configuration(server=data.outlook_server, credentials=credentials)
            account = Account(primary_smtp_address=data.outlook_email, config=cfg, autodiscover=False, access_type=DELEGATE)
            _ = account.inbox.total_count
        else:
            import msal
            authority = f"https://login.microsoftonline.com/{data.outlook_tenant_id}"
            app = msal.PublicClientApplication(data.outlook_client_id, authority=authority)
            result = app.acquire_token_by_username_password(
                username=data.outlook_email, password=data.outlook_password,
                scopes=["https://graph.microsoft.com/Mail.Read"]
            )
            if "access_token" not in result:
                raise Exception(result.get("error_description", "Auth fehlgeschlagen"))
        return {"status": "ok"}
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Bibliothek nicht installiert: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OutlookTestRequestV2(BaseModel):
    outlook_type:        str
    outlook_email:       str
    outlook_password:    str
    outlook_tenant_id:   str = ""
    outlook_client_id:   str = ""
    outlook_server:      str = ""
    outlook_imap_server: str = ""

@router.post("/test")
def test_outlook_connection(data: OutlookTestRequestV2, user=Depends(get_current_user)):
    try:
        if data.outlook_type == "imap":
            import imaplib
            from services.outlook_service import _get_imap_server
            imap_server, imap_port = _get_imap_server(data.outlook_email, data.outlook_imap_server)
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(data.outlook_email, data.outlook_password)
            mail.logout()
        elif data.outlook_type == "exchange":
            from exchangelib import Credentials, Account, DELEGATE, Configuration
            credentials = Credentials(data.outlook_email, data.outlook_password)
            cfg = Configuration(server=data.outlook_server, credentials=credentials)
            account = Account(primary_smtp_address=data.outlook_email, config=cfg, autodiscover=False, access_type=DELEGATE)
            _ = account.inbox.total_count
        else:
            import msal
            authority = f"https://login.microsoftonline.com/{data.outlook_tenant_id}"
            app_msal = msal.PublicClientApplication(data.outlook_client_id, authority=authority)
            result = app_msal.acquire_token_by_username_password(
                username=data.outlook_email, password=data.outlook_password,
                scopes=["https://graph.microsoft.com/Mail.Read"]
            )
            if "access_token" not in result:
                raise Exception(result.get("error_description", "Auth fehlgeschlagen"))
        return {"status": "ok"}
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Bibliothek nicht installiert: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
