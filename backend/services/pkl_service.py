import urllib.request
import json as _json
import time
from sqlalchemy.orm import Session
from database import Setting

PKL_TIMEOUT = 3.0


def _get_setting(db: Session, key: str) -> str:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value else ""


def _get_config(db: Session):
    return _get_setting(db, "pkl_bin_id"), _get_setting(db, "pkl_api_key")


def _fetch_record(bin_id: str, api_key: str):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}/latest"
    req = urllib.request.Request(url, headers={"X-Master-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=PKL_TIMEOUT) as resp:
            return _json.loads(resp.read()).get("record", {})
    except Exception:
        return None


def _find_locations(data: dict, referenz: str) -> list:
    locations = []
    for zone, rows in data.items():
        if not isinstance(rows, dict):
            continue
        for row_name, slots in rows.items():
            if not isinstance(slots, dict):
                continue
            for val in slots.values():
                if val == referenz:
                    locations.append(f"Zone {zone} · {row_name}")
                    break
    return locations


def lookup_pkl(db: Session, referenz: str) -> list:
    """Gibt Liste von Lagerort-Strings zurück, z.B. ["Zone A · R3", "Zone B · K1"]."""
    bin_id, api_key = _get_config(db)
    if not bin_id or not api_key:
        return []
    record = _fetch_record(bin_id, api_key)
    if not record:
        return []
    return _find_locations(record.get("data", {}), referenz)


def delete_pkl_entry(db: Session, referenz: str) -> bool:
    """Löscht alle Slots mit dieser Referenz aus JSONBin. Gibt True zurück wenn erfolgreich."""
    bin_id, api_key = _get_config(db)
    if not bin_id or not api_key:
        return True

    record = _fetch_record(bin_id, api_key)
    if not record:
        return False

    data = record.get("data", {})
    config = record.get("config", {})
    changed = False

    for zone in data.values():
        if not isinstance(zone, dict):
            continue
        for row in zone.values():
            if not isinstance(row, dict):
                continue
            to_delete = [k for k, v in row.items() if v == referenz]
            for k in to_delete:
                del row[k]
                changed = True

    if not changed:
        return True

    payload = _json.dumps({
        "data": data,
        "config": config,
        "_ts": int(time.time() * 1000),
    }).encode("utf-8")

    put_url = f"https://api.jsonbin.io/v3/b/{bin_id}"
    req = urllib.request.Request(
        put_url,
        data=payload,
        headers={
            "X-Master-Key": api_key,
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=PKL_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False
