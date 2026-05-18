"""Extrahiert Tracking-Nummern aus Carrier-Label-PDFs via Text-Extraktion.

Funktioniert zuverlässig für digital generierte PDFs (FedEx, DHL, UPS, TNT).
Gibt None zurück wenn kein Muster passt — kein Fehler, nur kein Link.
"""

from __future__ import annotations

import re
from typing import Optional


# Muster sortiert nach Spezifität (spezifische zuerst)
_PATTERNS = [
    # UPS: 1Z + 16 alphanumerische Zeichen
    (r"\b(1Z[A-Z0-9]{16})\b", True),
    # DHL Express / DHL Paket
    (r"\b(JJD\d{18})\b", False),
    (r"\b(JD\d{18})\b", False),
    # FedEx: 96-Präfix + 18–20 Ziffern
    (r"\b(96\d{18,20})\b", False),
    # TNT / Post International: 2 Buchstaben + 9 Ziffern + 2 Buchstaben
    (r"\b([A-Z]{2}\d{9}[A-Z]{2})\b", False),
    # Kontext-sensitiv: Nummer nach Tracking-Schlüsselwort
    (
        r"(?:tracking|sendungsnummer|tracking[\s\-]?(?:nr|no|number|nummer|id)|awb|airwaybill)"
        r"[:\s#\-]*([A-Z0-9]{8,22})",
        True,   # case-insensitive
    ),
    # FedEx 15-stellig
    (r"(?<![.\d])(\d{15})(?![.\d])", False),
    # FedEx 12-stellig
    (r"(?<![.\d])(\d{12})(?![.\d])", False),
]


def extract_tracking_number(pdf_path: str) -> Optional[str]:
    """Versucht, eine Tracking-Nummer aus einem Label-PDF zu lesen.

    Gibt die erste gefundene Tracking-Nummer zurück, sonst None.
    Wirft keine Exception — Fehler bei der Extraktion werden still ignoriert.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            return None

        for pattern, case_insensitive in _PATTERNS:
            flags = re.IGNORECASE if case_insensitive else 0
            m = re.search(pattern, text, flags)
            if m:
                candidate = re.sub(r"\s+", "", m.group(1)).upper()
                if len(candidate) >= 8:
                    return candidate

    except Exception:
        pass

    return None
