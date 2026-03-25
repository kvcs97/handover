"""
Lizenzschlüssel System für HandOver
Ansatz: Key = HMAC-Signatur, Lizenzdaten werden separat in JSON-Datei gespeichert
"""
import hmac
import hashlib
import base64
import json
import os
from datetime import datetime, timedelta

LICENSE_SECRET  = "SHORIU_HANDOVER_2026_SECRET_KEY_PRODUCTION"
LICENSE_DB_PATH = os.path.join(os.path.expanduser("~"), ".handover", "licenses.json")


def _load_license_db() -> dict:
    """Lädt alle ausgestellten Lizenzen"""
    if not os.path.exists(LICENSE_DB_PATH):
        return {}
    try:
        with open(LICENSE_DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_license_db(db: dict):
    os.makedirs(os.path.dirname(LICENSE_DB_PATH), exist_ok=True)
    with open(LICENSE_DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def _make_key(payload: dict) -> str:
    """Erstellt einen 25-Zeichen Schlüssel aus dem Payload"""
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(
        LICENSE_SECRET.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).digest()
    # Base32, Grossbuchstaben, 25 Zeichen
    raw = base64.b32encode(sig).decode().upper().replace("=", "")[:25]
    return "-".join([raw[i:i+5] for i in range(0, 25, 5)])


def generate_license(
    customer_name: str,
    customer_email: str,
    plan: str = "essential",
    valid_days: int = 365,
    max_users: int = 5,
) -> str:
    """Generiert einen neuen Lizenzschlüssel und speichert die Daten"""
    payload = {
        "customer": customer_name,
        "email":    customer_email,
        "plan":     plan,
        "users":    max_users,
        "issued":   datetime.utcnow().strftime("%Y-%m-%d"),
        "expires":  (datetime.utcnow() + timedelta(days=valid_days)).strftime("%Y-%m-%d"),
    }

    key = _make_key(payload)

    # In lokaler Lizenzdatenbank speichern
    db = _load_license_db()
    db[key.replace("-", "")] = payload
    _save_license_db(db)

    return key


def validate_license(license_key: str) -> dict:
    """Prüft einen Lizenzschlüssel gegen die lokale Lizenzdatenbank"""
    try:
        clean = license_key.replace("-", "").upper().strip()

        if len(clean) != 25:
            return {"valid": False, "error": "Ungültiges Schlüsselformat (muss 25 Zeichen haben)"}

        # In Lizenzdatenbank nachschlagen
        db = _load_license_db()
        payload = db.get(clean)

        if not payload:
            return {"valid": False, "error": "Schlüssel nicht gefunden — bitte Shoriu kontaktieren"}

        # Signatur verifizieren
        expected_key = _make_key(payload)
        if expected_key.replace("-", "") != clean:
            return {"valid": False, "error": "Ungültige Signatur"}

        # Ablaufdatum prüfen
        expires = datetime.strptime(payload["expires"], "%Y-%m-%d")
        if expires < datetime.utcnow():
            return {
                "valid":   False,
                "expired": True,
                "error":   f"Lizenz abgelaufen am {payload['expires']}",
                **payload
            }

        days_left = (expires - datetime.utcnow()).days

        return {
            "valid":     True,
            "plan":      payload.get("plan", "essential"),
            "customer":  payload.get("customer", ""),
            "email":     payload.get("email", ""),
            "max_users": payload.get("users", 1),
            "issued":    payload.get("issued", ""),
            "expires":   payload.get("expires", ""),
            "days_left": days_left,
        }

    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_license_from_db(db) -> dict:
    """Liest und prüft die gespeicherte Lizenz aus der SQLite-DB"""
    from database import Setting
    s = db.query(Setting).filter(Setting.key == "license_key").first()
    if not s or not s.value:
        return {"valid": False, "error": "Kein Lizenzschlüssel eingetragen"}
    return validate_license(s.value)
