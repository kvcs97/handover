from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Setting
from routers.auth import get_current_user, require_admin
from pydantic import BaseModel
from typing import List, Optional
import os, base64, tempfile, json

router = APIRouter()
_DEFAULT_ARCHIVE_DIR = os.path.join(os.path.expanduser("~"), ".handover", "archive")


class SignPdfRequest(BaseModel):
    attachments:   List[dict]
    sign_indices:  List[int]
    signature_png: str
    signer_name:   str
    referenz:      str
    carrier_name:  Optional[str] = ""
    truck_plate:   Optional[str] = ""

class OutlookLoginRequest(BaseModel):
    client_id:  str
    tenant_id:  str
    email:      str

class OutlookTokenRequest(BaseModel):
    client_id:  str
    tenant_id:  str
    flow_data:  str

class OutlookTestRequest(BaseModel):
    outlook_type:        str
    outlook_email:       str
    outlook_password:    str = ""
    outlook_tenant_id:   str = ""
    outlook_client_id:   str = ""
    outlook_server:      str = ""
    outlook_imap_server: str = ""


# ── OAuth2 Device Flow ────────────────────────

@router.post("/login/start")
def start_oauth_login(data: OutlookLoginRequest, user=Depends(get_current_user)):
    """Startet OAuth2 Device Flow — gibt Login-Code und URL zurück"""
    try:
        import msal
        authority = "https://login.microsoftonline.com/consumers"
        app = msal.PublicClientApplication(data.client_id, authority=authority)
        flow = app.initiate_device_flow(
            scopes=["https://outlook.office.com/IMAP.AccessAsUser.All"]
        )
        if "user_code" not in flow:
            error_detail = flow.get("error_description") or flow.get("error") or str(flow)
            raise HTTPException(status_code=500, detail=f"Device Flow Fehler: {error_detail}")

        return {
            "user_code":        flow["user_code"],
            "verification_url": flow["verification_uri"],
            "message":          flow["message"],
            "flow_data":        json.dumps(flow),
            "expires_in":       flow.get("expires_in", 900)
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="msal nicht installiert")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login/complete")
def complete_oauth_login(data: OutlookTokenRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Schliesst OAuth2 Login ab — speichert Token in DB"""
    try:
        import msal
        authority = "https://login.microsoftonline.com/consumers"
        app = msal.PublicClientApplication(data.client_id, authority=authority)
        flow = json.loads(data.flow_data)
        result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise HTTPException(status_code=400, detail=result.get("error_description", "Login fehlgeschlagen"))

        # Token in DB speichern
        def set_setting(key, value):
            s = db.query(Setting).filter(Setting.key == key).first()
            if s: s.value = value
            else: db.add(Setting(key=key, value=value))

        set_setting("outlook_access_token", result["access_token"])
        if "refresh_token" in result:
            set_setting("outlook_refresh_token", result["refresh_token"])
        db.commit()

        return {"status": "ok", "message": "Erfolgreich mit Microsoft angemeldet"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Verbindung testen ─────────────────────────

@router.post("/test")
def test_outlook_connection(data: OutlookTestRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        if data.outlook_type == "exchange":
            from exchangelib import Credentials, Account, DELEGATE, Configuration
            credentials = Credentials(data.outlook_email, data.outlook_password)
            cfg = Configuration(server=data.outlook_server, credentials=credentials)
            account = Account(primary_smtp_address=data.outlook_email, config=cfg, autodiscover=False, access_type=DELEGATE)
            _ = account.inbox.total_count
        else:
            # OAuth2 IMAP Test
            token_setting = db.query(Setting).filter(Setting.key == "outlook_access_token").first()
            if not token_setting or not token_setting.value:
                raise Exception("Kein OAuth2 Token — bitte zuerst 'Mit Microsoft anmelden' klicken")

            imap_server = data.outlook_imap_server or "outlook.office365.com"
            auth_bytes  = f"user={data.outlook_email}\x01auth=Bearer {token_setting.value}\x01\x01".encode()

            import imaplib
            mail = imaplib.IMAP4_SSL(imap_server, 993)
            mail.authenticate("XOAUTH2", lambda x: auth_bytes)
            mail.logout()

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E-Mails suchen ────────────────────────────

@router.get("/search/{referenz}")
def search_attachments(referenz: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        from services.outlook_service import search_emails_by_reference
        attachments = search_emails_by_reference(referenz, db)
        if not attachments:
            return {"found": False, "attachments": []}
        preview = [{"id": a["id"], "name": a["name"], "subject": a["subject"], "date": a["date"], "source": a["source"]} for a in attachments]
        return {"found": True, "attachments": preview}
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

    printer = db.query(Setting).filter(Setting.key == "printer_name").first()
    printer_name = printer.value if printer else ""
    archive_setting = db.query(Setting).filter(Setting.key == "archive_path").first()
    archive_dir = (archive_setting.value if (archive_setting and archive_setting.value) else _DEFAULT_ARCHIVE_DIR)
    results = []

    for i, att in enumerate(data.attachments):
        pdf_bytes = get_pdf_bytes(att)
        safe_name = att["name"].replace("/", "_").replace("\\", "_")
        if i in data.sign_indices:
            try:
                signed_path = embed_signature_in_pdf(
                    pdf_bytes=pdf_bytes, signature_png_base64=data.signature_png,
                    signer_name=data.signer_name, archive_dir=archive_dir,
                    filename=f"signed_{data.referenz}_{safe_name}",
                    carrier_name=data.carrier_name or "",
                    truck_plate=data.truck_plate or "",
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
