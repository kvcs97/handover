"""
Outlook/E-Mail Service mit OAuth2 für Outlook.com
"""
import os
import imaplib
import email
import base64
from email.header import decode_header


def get_outlook_config(db) -> dict:
    from database import Setting
    keys = ["outlook_type", "outlook_email", "outlook_password",
            "outlook_tenant_id", "outlook_client_id", "outlook_server",
            "outlook_imap_server", "outlook_access_token"]
    result = {}
    for key in keys:
        s = db.query(Setting).filter(Setting.key == key).first()
        result[key] = s.value if s and s.value else ""
    return result


def search_emails_by_reference(referenz: str, db) -> list[dict]:
    config = get_outlook_config(db)
    outlook_type = config.get("outlook_type", "imap")
    if outlook_type == "exchange":
        return _search_exchange(referenz, config)
    else:
        return _search_imap_oauth(referenz, config)


def get_oauth_token(client_id: str, tenant_id: str, email_addr: str) -> str:
    """
    Holt OAuth2 Token via Device Flow.
    Gibt Token zurück oder wirft Exception mit Login-URL.
    """
    import msal
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)

    # Zuerst prüfen ob gespeichertes Token noch gültig
    accounts = app.get_accounts(username=email_addr)
    if accounts:
        result = app.acquire_token_silent(
            scopes=["https://outlook.office.com/IMAP.AccessAsUser.All"],
            account=accounts[0]
        )
        if result and "access_token" in result:
            return result["access_token"]

    # Device Flow starten
    flow = app.initiate_device_flow(
        scopes=["https://outlook.office.com/IMAP.AccessAsUser.All"]
    )
    if "user_code" not in flow:
        raise Exception("Device Flow konnte nicht gestartet werden")

    # Gibt Login-Info zurück als Exception damit Frontend sie anzeigen kann
    raise DeviceFlowRequired(
        user_code=flow["user_code"],
        verification_url=flow["verification_uri"],
        message=flow["message"],
        flow=flow,
        app=app
    )


class DeviceFlowRequired(Exception):
    """Wird geworfen wenn der Benutzer sich erst einloggen muss"""
    def __init__(self, user_code, verification_url, message, flow, app):
        self.user_code = user_code
        self.verification_url = verification_url
        self.message = message
        self.flow = flow
        self.app = app
        super().__init__(message)


def complete_device_flow(client_id: str, tenant_id: str, flow_data: dict) -> str:
    """Schliesst Device Flow ab und gibt Token zurück"""
    import msal
    import json
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)
    result = app.acquire_token_by_device_flow(json.loads(flow_data))
    if "access_token" not in result:
        raise Exception(result.get("error_description", "Login fehlgeschlagen"))
    return result["access_token"]


def _search_imap_oauth(referenz: str, config: dict) -> list[dict]:
    """E-Mails via IMAP mit OAuth2 suchen"""
    email_addr   = config["outlook_email"]
    access_token = config.get("outlook_access_token", "")
    imap_server  = config.get("outlook_imap_server", "") or "outlook.office365.com"

    if not access_token:
        raise Exception("Kein OAuth2 Token — bitte zuerst mit Microsoft anmelden")

    # OAuth2 IMAP Authentifizierung
    # imaplib.authenticate() base64-encodiert den Rückgabewert selbst — rohe Bytes zurückgeben
    auth_bytes = f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01".encode()

    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.authenticate("XOAUTH2", lambda x: auth_bytes)
        mail.select("INBOX")

        _, msg_ids = mail.search(None, f'SUBJECT "{referenz}"')
        attachments = []

        for msg_id in msg_ids[0].split()[-5:]:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = _decode_header_str(msg["Subject"])
            date    = msg["Date"]
            for part in msg.walk():
                if part.get_content_type() == "application/pdf":
                    filename = _decode_header_str(part.get_filename() or "dokument.pdf")
                    content  = base64.b64encode(part.get_payload(decode=True)).decode()
                    attachments.append({
                        "id": f"{msg_id.decode()}_{filename}",
                        "name": filename, "message_id": msg_id.decode(),
                        "subject": subject, "date": date,
                        "content": content, "source": "imap_oauth"
                    })

        mail.logout()
        return attachments

    except imaplib.IMAP4.error as e:
        raise Exception(f"IMAP OAuth2 Fehler: {e} — Token möglicherweise abgelaufen")


def _search_exchange(referenz: str, config: dict) -> list[dict]:
    try:
        from exchangelib import Credentials, Account, DELEGATE, Configuration
        credentials = Credentials(config["outlook_email"], config["outlook_password"])
        cfg = Configuration(server=config["outlook_server"], credentials=credentials)
        account = Account(primary_smtp_address=config["outlook_email"], config=cfg, autodiscover=False, access_type=DELEGATE)
        items = account.inbox.filter(subject__contains=referenz).order_by("-datetime_received")[:5]
        attachments = []
        for item in items:
            for att in item.attachments:
                if hasattr(att, "content") and att.name and att.name.lower().endswith(".pdf"):
                    attachments.append({
                        "id": f"{item.id}_{att.name}", "name": att.name,
                        "message_id": item.id, "subject": item.subject,
                        "date": str(item.datetime_received),
                        "content": base64.b64encode(att.content).decode(),
                        "source": "exchange"
                    })
        return attachments
    except Exception as e:
        raise Exception(f"Exchange Fehler: {e}")


def _decode_header_str(value: str) -> str:
    if not value: return ""
    decoded = decode_header(value)
    result = ""
    for part, enc in decoded:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="replace")
        else:
            result += str(part)
    return result


def get_pdf_bytes(attachment: dict) -> bytes:
    return base64.b64decode(attachment["content"])
