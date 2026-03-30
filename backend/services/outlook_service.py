"""
Outlook/E-Mail Service
Unterstützt:
- IMAP (Outlook.com, Gmail, Exchange) — keine Azure Registration nötig
- Microsoft Graph API (M365 mit Azure App)
- Exchange EWS (on-premise)
"""
import os
import imaplib
import email
import base64
from email.header import decode_header
from typing import Optional


def get_outlook_config(db) -> dict:
    from database import Setting
    keys = ["outlook_type", "outlook_email", "outlook_password",
            "outlook_tenant_id", "outlook_client_id", "outlook_server",
            "outlook_imap_server", "outlook_imap_port"]
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
    elif outlook_type == "graph":
        return _search_graph(referenz, config)
    else:
        return _search_imap(referenz, config)


def _get_imap_server(email_addr: str, custom_server: str = "") -> tuple[str, int]:
    """Bestimmt IMAP-Server anhand der E-Mail-Adresse"""
    if custom_server:
        return custom_server, 993
    domain = email_addr.split("@")[-1].lower()
    servers = {
        "outlook.com":  ("outlook.office365.com", 993),
        "hotmail.com":  ("outlook.office365.com", 993),
        "live.com":     ("outlook.office365.com", 993),
        "gmail.com":    ("imap.gmail.com", 993),
        "googlemail.com": ("imap.gmail.com", 993),
    }
    return servers.get(domain, (f"mail.{domain}", 993))


def _search_imap(referenz: str, config: dict) -> list[dict]:
    """E-Mails via IMAP suchen"""
    email_addr = config["outlook_email"]
    password   = config["outlook_password"]
    custom_srv = config.get("outlook_imap_server", "")

    imap_server, imap_port = _get_imap_server(email_addr, custom_srv)

    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_addr, password)
        mail.select("INBOX")

        # Nach Referenz im Betreff suchen
        _, msg_ids = mail.search(None, f'SUBJECT "{referenz}"')

        attachments = []
        for msg_id in msg_ids[0].split()[-5:]:  # Max 5 neueste
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = _decode_header_str(msg["Subject"])
            date    = msg["Date"]

            for part in msg.walk():
                if part.get_content_type() == "application/pdf":
                    filename = part.get_filename() or "dokument.pdf"
                    filename = _decode_header_str(filename)
                    content  = base64.b64encode(part.get_payload(decode=True)).decode()
                    attachments.append({
                        "id":        f"{msg_id.decode()}_{filename}",
                        "name":      filename,
                        "message_id": msg_id.decode(),
                        "subject":   subject,
                        "date":      date,
                        "content":   content,
                        "source":    "imap"
                    })

        mail.logout()
        return attachments

    except imaplib.IMAP4.error as e:
        raise Exception(f"IMAP Login fehlgeschlagen: {e}")
    except Exception as e:
        raise Exception(f"IMAP Fehler: {e}")


def _decode_header_str(value: str) -> str:
    if not value:
        return ""
    decoded = decode_header(value)
    result = ""
    for part, enc in decoded:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="replace")
        else:
            result += str(part)
    return result


def _search_graph(referenz: str, config: dict) -> list[dict]:
    try:
        import msal, requests
        tenant_id = config["outlook_tenant_id"]
        client_id = config["outlook_client_id"]
        email_addr = config["outlook_email"]
        password   = config["outlook_password"]

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.PublicClientApplication(client_id, authority=authority)
        result = app.acquire_token_by_username_password(
            username=email_addr, password=password,
            scopes=["https://graph.microsoft.com/Mail.Read"]
        )
        if "access_token" not in result:
            raise Exception(result.get("error_description", "Auth fehlgeschlagen"))

        token   = result["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(
            f"https://graph.microsoft.com/v1.0/me/messages"
            f"?$filter=contains(subject,'{referenz}')&$orderby=receivedDateTime desc&$top=5",
            headers=headers
        )
        messages = res.json().get("value", [])
        attachments = []
        for msg in messages:
            if not msg.get("hasAttachments"):
                continue
            att_res = requests.get(f"https://graph.microsoft.com/v1.0/me/messages/{msg['id']}/attachments", headers=headers)
            for att in att_res.json().get("value", []):
                if att.get("contentType") == "application/pdf":
                    attachments.append({
                        "id": att["id"], "name": att["name"],
                        "message_id": msg["id"], "subject": msg["subject"],
                        "date": msg["receivedDateTime"], "content": att.get("contentBytes", ""),
                        "source": "graph"
                    })
        return attachments
    except ImportError:
        raise Exception("msal nicht installiert")
    except Exception as e:
        raise Exception(f"Graph API Fehler: {e}")


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
    except ImportError:
        raise Exception("exchangelib nicht installiert")
    except Exception as e:
        raise Exception(f"Exchange Fehler: {e}")


def get_pdf_bytes(attachment: dict) -> bytes:
    return base64.b64decode(attachment["content"])
