"""Pydantic Schemas für das Kurier-Modul.

SQLAlchemy ORM-Modelle leben weiterhin in database.py (CourierCarrier,
CourierShipment, CourierDocument, CourierSignature, CourierArchive).
Hier werden ausschließlich die Request/Response-Schemas der FastAPI-Routen
sowie ein paar Hilfstypen definiert.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


CarrierName = str  # interner Key (z.B. "fedex_tnt", "dhl", "ups", oder zukünftige Carrier)
DocumentType = Literal["label", "rechnung", "lieferschein", "pkl", "edec", "to", "other"]
ShipmentStatus = Literal["open", "printed", "signed", "archived"]
SignatureStatus = Literal["pending", "signed"]


# ── Carrier ────────────────────────────────────────────────

class PrintSetRules(BaseModel):
    """JSON-Struktur in CourierCarrier.print_set_rules."""
    default: list[DocumentType]
    overrides: dict[str, list[DocumentType]] = Field(default_factory=dict)


class CarrierBase(BaseModel):
    name: CarrierName
    display_name: str
    detection_keywords: list[str]
    print_set_rules: PrintSetRules
    is_active: bool = True


class CarrierCreate(CarrierBase):
    pass


class CarrierUpdate(BaseModel):
    display_name: Optional[str] = None
    detection_keywords: Optional[list[str]] = None
    print_set_rules: Optional[PrintSetRules] = None
    is_active: Optional[bool] = None


class CarrierOut(CarrierBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Documents ──────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int
    shipment_id: int
    filename: str
    delivery_note_number: Optional[str] = None
    document_type: DocumentType
    local_path: Optional[str] = None
    should_print: bool
    was_printed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentPrintToggle(BaseModel):
    should_print: bool


# ── Shipments ──────────────────────────────────────────────

class ShipmentBase(BaseModel):
    delivery_note_numbers: list[str]
    carrier_id: Optional[int] = None
    email_id: str
    email_subject: Optional[str] = None
    email_date: datetime
    process_date: str  # YYYY-MM-DD


class ShipmentCreate(ShipmentBase):
    @field_validator("delivery_note_numbers")
    @classmethod
    def _at_least_one_ls(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Mindestens eine Lieferscheinnummer erforderlich")
        return v


class ShipmentOut(ShipmentBase):
    id: int
    status: ShipmentStatus
    created_at: datetime
    documents: list[DocumentOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus


# ── Carrier-Gruppe (für Dashboard-Antwort) ────────────────

class CarrierGroup(BaseModel):
    carrier: CarrierOut
    shipments: list[ShipmentOut]
    signature_status: SignatureStatus = "pending"
    signed_at: Optional[datetime] = None


# ── Signatures ─────────────────────────────────────────────

class SignatureCreate(BaseModel):
    signature_data: str  # Base64 PNG
    signer_name: Optional[str] = None
    process_date: str    # YYYY-MM-DD


class SignatureOut(BaseModel):
    id: int
    carrier_id: int
    process_date: str
    signature_data: str
    signer_name: Optional[str] = None
    signed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Archive ────────────────────────────────────────────────

class ArchiveOut(BaseModel):
    id: int
    shipment_id: int
    signature_id: int
    signed_document_path: str
    archive_path: str
    archived_at: datetime

    model_config = {"from_attributes": True}


class ArchiveListItem(BaseModel):
    """Reicheres Antwort-Schema für die Archiv-Übersicht: Archive-Eintrag
    plus joined Carrier/Sendung/Signatur-Infos für die UI."""
    archive_id: int
    archived_at: datetime
    process_date: str
    signed_document_path: str
    delivery_note_numbers: list[str]
    email_subject: Optional[str] = None
    email_date: Optional[datetime] = None
    carrier_id: int
    carrier_name: str
    carrier_display_name: str
    signer_name: Optional[str] = None
    signed_at: datetime


# ── E-Mail-Verarbeitung ────────────────────────────────────

class FetchEmailsRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD; default = heute


class ProcessEmailsResponse(BaseModel):
    process_date: str
    total_emails: int
    total_shipments: int
    carrier_groups: list[CarrierGroup]
    unmatched_shipments: list[ShipmentOut] = Field(default_factory=list)
