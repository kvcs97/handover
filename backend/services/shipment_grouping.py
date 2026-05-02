"""Sendungs-Gruppierung & Druckset-Berechnung.

Eine eingehende E-Mail kann 1 oder mehrere Lieferscheinnummern enthalten.
Pro LS-Nummer entsteht eine `ShipmentDraft` mit den Anhängen, die ihr
zuzuordnen sind. Anhänge ohne erkannte LS-Nummer werden — falls die Mail
*genau eine* LS-Nummer hat — dieser zugeordnet, sonst auf einen
Sammel-„unassigned"-Eintrag gelegt (manuell zuzuordnen im Frontend).

Außerdem: `compute_print_set` wendet `print_set_rules.default` auf alle
Dokumente einer Sendung an, mit optionalem Override (z.B. TNT → +EDEC).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterable, Optional

from database import CourierCarrier
from services.courier_parser import detect_document_type, extract_ls_from_filename


@dataclass
class AttachmentDraft:
    """Anhang einer E-Mail, vor dem Persistieren."""
    filename: str
    content_b64: str                  # PDF als Base64 (vom IMAP-Service geliefert)
    document_type: str = "other"      # vom Parser gefüllt
    delivery_note_number: Optional[str] = None
    should_print: bool = False        # vom Druckset-Setter gefüllt


@dataclass
class ShipmentDraft:
    """Eine LS-Nummer + ihre zugeordneten Anhänge."""
    delivery_note_numbers: list[str]  # in der Regel genau eine — bei "unassigned" leer
    attachments: list[AttachmentDraft] = field(default_factory=list)


def _enrich_attachments(raw_attachments: Iterable[dict]) -> list[AttachmentDraft]:
    """Aus IMAP-Anhängen (dicts) enriched AttachmentDrafts machen."""
    out: list[AttachmentDraft] = []
    for att in raw_attachments:
        filename = att.get("name") or att.get("filename") or ""
        content = att.get("content") or ""
        out.append(AttachmentDraft(
            filename=filename,
            content_b64=content,
            document_type=detect_document_type(filename),
            delivery_note_number=extract_ls_from_filename(filename),
        ))
    return out


def group_into_shipments(
    ls_numbers: list[str],
    raw_attachments: Iterable[dict],
) -> list[ShipmentDraft]:
    """Splittet eine E-Mail in 1..n Sendungen.

    - Pro LS-Nummer im Betreff entsteht eine Sendung.
    - Anhänge werden über die LS-Nummer im Dateinamen zugeordnet.
    - Anhänge ohne erkannte LS-Nummer:
        * wenn die Mail genau 1 LS-Nummer hat → dieser zuordnen
        * sonst → auf eine zusätzliche "unassigned"-Sendung legen
    - Mail ohne erkannte LS-Nummer im Betreff → eine Sendung mit
      delivery_note_numbers=[] (Frontend fragt manuelle Zuordnung an)
    """
    enriched = _enrich_attachments(raw_attachments)

    # Edge-Case: keine LS-Nummern im Betreff
    if not ls_numbers:
        return [ShipmentDraft(delivery_note_numbers=[], attachments=enriched)]

    # Map LS → Sendung
    by_ls: dict[str, ShipmentDraft] = {ls: ShipmentDraft(delivery_note_numbers=[ls]) for ls in ls_numbers}
    unassigned: list[AttachmentDraft] = []

    for att in enriched:
        if att.delivery_note_number and att.delivery_note_number in by_ls:
            by_ls[att.delivery_note_number].attachments.append(att)
        else:
            unassigned.append(att)

    # Single-LS-Mail: ungebundene Anhänge gehören dieser einen Sendung
    if len(ls_numbers) == 1 and unassigned:
        by_ls[ls_numbers[0]].attachments.extend(unassigned)
        unassigned = []

    drafts = list(by_ls.values())
    if unassigned:
        drafts.append(ShipmentDraft(delivery_note_numbers=[], attachments=unassigned))
    return drafts


# ── Druckset-Logik ────────────────────────────────────────

def _print_set_for_carrier(carrier: CourierCarrier, override_key: Optional[str]) -> set[str]:
    """Liest `print_set_rules` und liefert die zu druckenden DocumentTypes.

    Override-Logik: wenn ein Override-Key getroffen wurde (z.B. "tnt"), wird
    die override-Liste *anstelle* der default-Liste verwendet — so steht es
    in der Spec (`print_set_rules.overrides.tnt = [label, rechnung, edec]`).
    """
    try:
        rules = json.loads(carrier.print_set_rules or "{}")
    except (json.JSONDecodeError, TypeError):
        rules = {}

    default = rules.get("default") or []
    overrides = rules.get("overrides") or {}
    if override_key and override_key in overrides:
        chosen = overrides[override_key]
    else:
        chosen = default

    return {str(d).lower() for d in chosen}


def compute_print_set(
    shipment: ShipmentDraft,
    carrier: Optional[CourierCarrier],
    override_key: Optional[str],
) -> None:
    """Setzt `should_print` auf jedem Anhang gemäß Carrier-Regel.

    Mutiert die übergebene ShipmentDraft in-place. Wenn kein Carrier
    erkannt ist, bleibt `should_print=False` für alle (manuelle Auswahl).
    """
    if carrier is None:
        for att in shipment.attachments:
            att.should_print = False
        return

    targets = _print_set_for_carrier(carrier, override_key)
    for att in shipment.attachments:
        att.should_print = att.document_type in targets
