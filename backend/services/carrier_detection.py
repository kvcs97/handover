"""Carrier-Erkennung für das Kurier-Modul.

Matcht die `detection_keywords` (JSON-Array pro Carrier) gegen Betreff +
Dateinamen einer eingehenden E-Mail. Erkennt zusätzlich, welches einzelne
Keyword den Treffer ausgelöst hat — wird für `print_set_rules.overrides`
gebraucht (z.B. TNT-Override innerhalb der FedEx/TNT-Gruppe).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from database import CourierCarrier


@dataclass
class CarrierMatch:
    carrier: CourierCarrier
    matched_keywords: list[str]   # alle Keywords die irgendwo getroffen haben
    override_key: Optional[str]   # passendes Override aus print_set_rules (z.B. "tnt") oder None


def _haystack(subject: str | None, filenames: Iterable[str]) -> str:
    parts: list[str] = []
    if subject:
        parts.append(subject)
    parts.extend(f for f in filenames if f)
    return " \n ".join(parts).lower()


def _keywords_from_carrier(carrier: CourierCarrier) -> list[str]:
    raw = carrier.detection_keywords or "[]"
    try:
        parsed = json.loads(raw)
        return [str(k) for k in parsed if k]
    except (json.JSONDecodeError, TypeError):
        return []


def _overrides_from_carrier(carrier: CourierCarrier) -> dict[str, list[str]]:
    raw = carrier.print_set_rules or "{}"
    try:
        rules = json.loads(raw)
        ov = rules.get("overrides") or {}
        return {str(k): list(v) for k, v in ov.items() if isinstance(v, list)}
    except (json.JSONDecodeError, TypeError, AttributeError):
        return {}


def detect_carrier(
    subject: str | None,
    filenames: Iterable[str],
    carriers: Iterable[CourierCarrier],
) -> Optional[CarrierMatch]:
    """Sucht den passenden Carrier für eine E-Mail.

    Strategie:
    - Über alle aktiven Carrier laufen, jedes Keyword als Wort-Match (`\\b…\\b`)
      gegen den kombinierten Heystack (Betreff + Dateinamen) prüfen.
    - Carrier mit den meisten Keyword-Treffern gewinnt; bei Gleichstand
      gewinnt der zuerst gefundene (DB-Reihenfolge).
    - Override-Key wird gesetzt, wenn eines der getroffenen Keywords
      gleichzeitig als Schlüssel in `print_set_rules.overrides` existiert.

    Gibt None zurück, wenn kein Carrier matcht.
    """
    haystack = _haystack(subject, filenames)
    if not haystack.strip():
        return None

    best: Optional[CarrierMatch] = None
    best_score = 0

    for carrier in carriers:
        if not getattr(carrier, "is_active", True):
            continue

        keywords = _keywords_from_carrier(carrier)
        if not keywords:
            continue

        hits: list[str] = []
        for kw in keywords:
            kw_lc = kw.strip().lower()
            if not kw_lc:
                continue
            # Wort-Grenzen, damit "ups" nicht in "groups" matcht
            pattern = r"(?<![a-z0-9])" + re.escape(kw_lc) + r"(?![a-z0-9])"
            if re.search(pattern, haystack):
                hits.append(kw_lc)

        if not hits:
            continue

        if len(hits) > best_score:
            overrides = _overrides_from_carrier(carrier)
            override_key: Optional[str] = None
            for hit in hits:
                if hit in overrides:
                    override_key = hit
                    break

            best = CarrierMatch(
                carrier=carrier,
                matched_keywords=hits,
                override_key=override_key,
            )
            best_score = len(hits)

    return best
