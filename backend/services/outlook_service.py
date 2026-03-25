"""
Outlook Service — unterstützt Microsoft 365 (Graph API) und Exchange on-premise (EWS)
"""
import os
import re
from typing import Optional


def get_outlook_config(db) -> dict:
    """Liest Outlook-Konfiguration aus der Datenbank"""
    from database import Setting
    keys = ["outlook_type", "outlook_email", "outlook_password",
            "outlook_tenant_id", "outlook_client_id", "outlook_server"]
    result = {}
    for key in keys:
        s = db.query(Setting).filter(Setting.key == key).first()
        result[key] = s.value if s and s.value else ""
    return result


def search_emails_by_reference(referenz: str, db) -> list[dict]:
    """
    Sucht E-Mails mit der Referenznummer im Betreff.
    Gibt Liste von Anhängen (PDFs) zurück.
    """
    config = get_outlook_config(db)
    outlook_type = config.get("outlook_type", "graph")

    if outlook_type == "exchange":
        return _search_exchange(referenz, config)
    else:
        return _search_graph(referenz, config)


def _search_graph(referenz: str, config: dict) -> list[dict]:
    """Microsoft 365 via Graph API"""
    try:
        import msal
        import requests

        tenant_id = config["outlook_tenant_id"]
        client_id = config["outlook_client_id"]
        email     = config["outlook_email"]
        password  = config["outlook_password"]

        # Token holen
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.PublicClientApplication(client_id, authority=authority)
        result = app.acquire_token_by_username_password(
            username=email,
            password=password,
            scopes=["https://graph.microsoft.com/Mail.Read"]
        )

        if "access_token" not in result:
            raise Exception(f"Auth fehlgeschlagen: {result.get('error_description', 'Unbekannt')}")

        token = result["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # E-Mails suchen
        search_url = (
            f"https://graph.microsoft.com/v1.0/me/messages"
            f"?$filter=contains(subject,'{referenz}')"
            f"&$select=id,subject,receivedDateTime,hasAttachments"
            f"&$orderby=receivedDateTime desc"
            f"&$top=5"
        )
        res = requests.get(search_url, headers=headers)
        messages = res.json().get("value", [])

        attachments = []
        for msg in messages:
            if not msg.get("hasAttachments"):
                continue

            att_url = f"https://graph.microsoft.com/v1.0/me/messages/{msg['id']}/attachments"
            att_res = requests.get(att_url, headers=headers)
            for att in att_res.json().get("value", []):
                if att.get("contentType") == "application/pdf":
                    attachments.append({
                        "id":        att["id"],
                        "name":      att["name"],
                        "message_id": msg["id"],
                        "subject":   msg["subject"],
                        "date":      msg["receivedDateTime"],
                        "content":   att.get("contentBytes", ""),  # Base64
                        "source":    "graph"
                    })

        return attachments

    except ImportError:
        raise Exception("msal nicht installiert. Bitte 'pip install msal' ausführen.")
    except Exception as e:
        raise Exception(f"Graph API Fehler: {str(e)}")


def _search_exchange(referenz: str, config: dict) -> list[dict]:
    """Exchange on-premise via EWS"""
    try:
        from exchangelib import Credentials, Account, DELEGATE, Configuration
        from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

        email    = config["outlook_email"]
        password = config["outlook_password"]
        server   = config["outlook_server"]

        credentials = Credentials(email, password)
        ews_config = Configuration(
            server=server,
            credentials=credentials
        )
        account = Account(
            primary_smtp_address=email,
            config=ews_config,
            autodiscover=False,
            access_type=DELEGATE
        )

        # E-Mails suchen
        from exchangelib import Q
        items = account.inbox.filter(subject__contains=referenz).order_by("-datetime_received")[:5]

        attachments = []
        for item in items:
            for att in item.attachments:
                if hasattr(att, "content") and att.name and att.name.lower().endswith(".pdf"):
                    import base64
                    attachments.append({
                        "id":        f"{item.id}_{att.name}",
                        "name":      att.name,
                        "message_id": item.id,
                        "subject":   item.subject,
                        "date":      str(item.datetime_received),
                        "content":   base64.b64encode(att.content).decode(),
                        "source":    "exchange"
                    })

        return attachments

    except ImportError:
        raise Exception("exchangelib nicht installiert. Bitte 'pip install exchangelib' ausführen.")
    except Exception as e:
        raise Exception(f"Exchange Fehler: {str(e)}")


def get_pdf_bytes(attachment: dict) -> bytes:
    """Gibt PDF-Bytes aus einem Attachment zurück"""
    import base64
    return base64.b64decode(attachment["content"])
