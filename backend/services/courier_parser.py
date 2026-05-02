"""Parser-Hilfen für das Kurier-Modul.

Funktionen:
- parse_subject_ls_numbers(subject) -> list[str]
    Extrahiert Lieferscheinnummern aus dem Betreff.
- extract_ls_from_filename(filename) -> str | None
    Holt die LS-Nummer aus einem Anhang-Dateinamen, falls enthalten.
- detect_document_type(filename) -> DocumentType
    Leitet den Dokumenttyp aus dem Dateinamen ab.

Bekannte LS-Nummern-Formate (laut Adam):
- 80xxxxxxxx  (10 Ziffern, beginnt mit 80)
- 17xxxxxxxx  (10 Ziffern, beginnt mit 17)
- C_XX_XXXX   (Buchstabe C + zwei Ziffern + vier Ziffern, mit Underscores)

Rechnungsnummern starten mit 88xxxxxxxx; "PI" kann zusätzlich im Namen stehen.
"""

from __future__ import annotations

import re
from typing import Optional

# Public types — bewusst als String-Konstanten, da Pydantic-Literal nur fürs Schema gebraucht wird
DOC_LABEL = "label"
DOC_RECHNUNG = "rechnung"
DOC_LIEFERSCHEIN = "lieferschein"
DOC_PKL = "pkl"
DOC_EDEC = "edec"
DOC_TO = "to"
DOC_OTHER = "other"


# ── Regex-Patterns ────────────────────────────────────────

# Eine einzelne LS-Nummer (für extract_ls_from_filename / parse_subject_ls_numbers)
_LS_PATTERN = re.compile(
    r"(?:80\d{8}|17\d{8}|C_\d{2}_\d{4})",
    re.IGNORECASE,
)

# Rechnungsnummer: 88 + 8 Ziffern
_INVOICE_NUMBER_PATTERN = re.compile(r"88\d{8}")

# Eigene "Token-Grenze": behandelt `_`, `-`, `.`, Whitespace und String-Ende
# als Trenner — `\b` allein wirkt nicht über `_`, weil `_` ein Wort-Zeichen ist.
_TB = r"(?:^|(?<=[\s_\-\.]))"  # Token-Anfang
_TE = r"(?=[\s_\-\.]|$)"       # Token-Ende

# Carrier-Marker im Dateinamen (deuten auf Label hin)
_CARRIER_MARKER_PATTERN = re.compile(
    rf"{_TB}(?:fedex|tnt|dhl|ups|federal\s*express){_TE}",
    re.IGNORECASE,
)

# TO (Transportauftrag) — nur am Anfang oder als Prefix vor LS-Nummer/Trenner.
# "to" ist als englisches Wort zu häufig; deshalb strikt: Datei-Start oder
# explizit "to_<ziffer/c>" / "transportauftrag".
_TO_TOKEN_PATTERN = re.compile(
    r"(?:^to[_\-\s\.]|transportauftrag)",
    re.IGNORECASE,
)

# Label-Schlagwort
_LABEL_KEYWORD_PATTERN = re.compile(
    rf"{_TB}(?:label|awb){_TE}|shipping[\s_\-]?label",
    re.IGNORECASE,
)

# PKL-Schlagwort
_PKL_KEYWORD_PATTERN = re.compile(
    rf"{_TB}pkl{_TE}|packlist|packliste",
    re.IGNORECASE,
)

# Rechnung-Schlagwort (deutsche/englische Begriffe + isoliertes "PI")
_RECHNUNG_KEYWORD_PATTERN = re.compile(
    rf"rechnung|invoice|{_TB}pi{_TE}",
    re.IGNORECASE,
)

# Lieferschein-Präfix: ls_80…, dn_17… etc.
_LS_PREFIX_PATTERN = re.compile(
    rf"{_TB}(?:ls|dn)[_\-\s]?(?:80|17)\d{{8}}",
    re.IGNORECASE,
)

# Lieferschein-Schlagwort
_LS_KEYWORD_PATTERN = re.compile(
    rf"lieferschein|delivery[\s_\-]?note|{_TB}dn{_TE}",
    re.IGNORECASE,
)


# ── Public API ────────────────────────────────────────────

def parse_subject_ls_numbers(subject: str | None) -> list[str]:
    """Extrahiert alle Lieferscheinnummern aus einem Betreff.

    Trenner sind egal (`+`, `/`, `,`, Leerzeichen, …) — wir suchen alle Vorkommen.
    Reihenfolge bleibt erhalten, Duplikate werden entfernt.
    """
    if not subject:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for match in _LS_PATTERN.findall(subject):
        norm = match.upper()
        if norm not in seen:
            seen.add(norm)
            found.append(norm)
    return found


def extract_ls_from_filename(filename: str | None) -> Optional[str]:
    """Liefert die erste LS-Nummer im Dateinamen oder None."""
    if not filename:
        return None
    m = _LS_PATTERN.search(filename)
    return m.group(0).upper() if m else None


def detect_document_type(filename: str | None) -> str:
    """Leitet den Dokumenttyp aus dem Dateinamen ab.

    Priorität (von spezifisch zu allgemein):
      1. EDEC                       → "edec"
      2. PKL                        → "pkl"
      3. Carrier-Marker im Namen    → "label"   (Versandlabel der Carrier)
      4. Rechnungsnummer 88…/PI/…   → "rechnung"
      5. LS-Präfix (ls_/dn_) oder
         Lieferschein-Schlagwort    → "lieferschein"
      6. TO-Token                   → "to"
      7. LS-Nummer alleine im Namen → "lieferschein"
      8. Sonst                      → "other"
    """
    if not filename:
        return DOC_OTHER

    name = filename.lower()
    base = re.sub(r"\.[a-z0-9]{1,5}$", "", name)  # Endung weg

    # 1. EDEC (Substring reicht — "edec" tritt nirgends sonst auf)
    if "edec" in base:
        return DOC_EDEC

    # 2. PKL / Packlist
    if _PKL_KEYWORD_PATTERN.search(base):
        return DOC_PKL

    # 3. Label: Carrier-Marker im Namen ODER Label-Keyword
    if _CARRIER_MARKER_PATTERN.search(base) or _LABEL_KEYWORD_PATTERN.search(base):
        return DOC_LABEL

    # 4. Rechnung: 88…-Nummer ODER Rechnung/Invoice/PI
    if _INVOICE_NUMBER_PATTERN.search(base) or _RECHNUNG_KEYWORD_PATTERN.search(base):
        return DOC_RECHNUNG

    # 5. Lieferschein-Präfix oder explizites Schlagwort
    if _LS_PREFIX_PATTERN.search(base) or _LS_KEYWORD_PATTERN.search(base):
        return DOC_LIEFERSCHEIN

    # 6. TO (Transportauftrag) — nur als klares Prefix
    if _TO_TOKEN_PATTERN.search(base):
        return DOC_TO

    # 7. Reine LS-Nummer im Namen → Lieferschein (Adam: "die Nummer allein")
    if _LS_PATTERN.search(base):
        return DOC_LIEFERSCHEIN

    return DOC_OTHER
