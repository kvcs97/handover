from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import json

# Datenbank liegt lokal beim Kunden
DB_PATH = os.path.join(os.path.expanduser("~"), ".handover", "handover.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Tabellen ──────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    name          = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="operator")  # admin | operator | viewer
    active        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    id            = Column(Integer, primary_key=True)
    key           = Column(String, unique=True, nullable=False)
    value         = Column(Text, nullable=True)
    # Beispiel-Keys: company_name, company_logo, printer_name,
    #                data_source_type, data_source_path, setup_done


class Carrier(Base):
    __tablename__ = "carriers"
    id            = Column(Integer, primary_key=True)
    company_name  = Column(String, nullable=False, unique=True)
    last_used     = Column(DateTime, default=datetime.utcnow)
    created_at    = Column(DateTime, default=datetime.utcnow)
    handovers     = relationship("Handover", back_populates="carrier")


class Handover(Base):
    __tablename__ = "handovers"
    id            = Column(Integer, primary_key=True)
    referenz      = Column(String, nullable=False)
    carrier_id    = Column(Integer, ForeignKey("carriers.id"), nullable=True)
    truck_plate   = Column(String, nullable=True)
    driver_name   = Column(String, nullable=True)
    status        = Column(String, default="pending")  # pending | signed | archived
    pdf_path      = Column(String, nullable=True)      # Pfad zum archivierten PDF
    created_at    = Column(DateTime, default=datetime.utcnow)
    signed_at     = Column(DateTime, nullable=True)
    created_by    = Column(Integer, ForeignKey("users.id"))
    carrier       = relationship("Carrier", back_populates="handovers")
    signature     = relationship("Signature", back_populates="handover", uselist=False)
    audit_logs    = relationship("AuditLog", back_populates="handover")


class Signature(Base):
    __tablename__ = "signatures"
    id            = Column(Integer, primary_key=True)
    handover_id   = Column(Integer, ForeignKey("handovers.id"), unique=True)
    png_data      = Column(Text, nullable=False)   # Base64 PNG
    signer_name   = Column(String, nullable=False)
    timestamp     = Column(DateTime, default=datetime.utcnow)
    handover      = relationship("Handover", back_populates="signature")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id"))
    handover_id   = Column(Integer, ForeignKey("handovers.id"), nullable=True)
    action        = Column(String, nullable=False)  # z.B. "login", "handover_created", "signed"
    detail        = Column(Text, nullable=True)
    timestamp     = Column(DateTime, default=datetime.utcnow)
    handover      = relationship("Handover", back_populates="audit_logs")


# ── Kurier-Modul ───────────────────────────────────────────

class CourierCarrier(Base):
    __tablename__ = "courier_carriers"
    id                  = Column(Integer, primary_key=True)
    name                = Column(String, nullable=False, unique=True)        # interner Key, z.B. "fedex_tnt"
    display_name        = Column(String, nullable=False)                     # UI-Anzeigename
    detection_keywords  = Column(Text, nullable=False)                        # JSON-Array: ["fedex","tnt",...]
    print_set_rules     = Column(Text, nullable=False)                        # JSON: {"default":[...], "overrides":{...}}
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    shipments           = relationship("CourierShipment", back_populates="carrier")
    signatures          = relationship("CourierSignature", back_populates="carrier")


class CourierShipment(Base):
    __tablename__ = "courier_shipments"
    id                      = Column(Integer, primary_key=True)
    delivery_note_numbers   = Column(Text, nullable=False)                    # JSON-Array von LS-Nummern
    carrier_id              = Column(Integer, ForeignKey("courier_carriers.id"), nullable=True)
    email_id                = Column(String, nullable=False)                  # IMAP Message-ID
    email_subject           = Column(String, nullable=True)
    email_date              = Column(DateTime, nullable=False)
    status                  = Column(String, default="open")                  # open | printed | signed | archived
    process_date            = Column(String, nullable=False)                  # Verarbeitungstag (YYYY-MM-DD)
    created_at              = Column(DateTime, default=datetime.utcnow)
    carrier                 = relationship("CourierCarrier", back_populates="shipments")
    documents               = relationship("CourierDocument", back_populates="shipment", cascade="all, delete-orphan")
    archive_entries         = relationship("CourierArchive", back_populates="shipment")


class CourierDocument(Base):
    __tablename__ = "courier_documents"
    id                      = Column(Integer, primary_key=True)
    shipment_id             = Column(Integer, ForeignKey("courier_shipments.id", ondelete="CASCADE"), nullable=False)
    filename                = Column(String, nullable=False)
    delivery_note_number    = Column(String, nullable=True)                   # zugeordnete LS-Nummer
    document_type           = Column(String, nullable=False)                  # label|rechnung|lieferschein|pkl|edec|to|other
    local_path              = Column(String, nullable=True)
    should_print            = Column(Boolean, default=False)
    was_printed             = Column(Boolean, default=False)
    created_at              = Column(DateTime, default=datetime.utcnow)
    shipment                = relationship("CourierShipment", back_populates="documents")


class CourierSignature(Base):
    __tablename__ = "courier_signatures"
    id                      = Column(Integer, primary_key=True)
    carrier_id              = Column(Integer, ForeignKey("courier_carriers.id"), nullable=False)
    process_date            = Column(String, nullable=False)                  # YYYY-MM-DD
    signature_data          = Column(Text, nullable=False)                    # Base64 PNG
    signer_name             = Column(String, nullable=True)
    signed_at               = Column(DateTime, nullable=False)
    created_at              = Column(DateTime, default=datetime.utcnow)
    carrier                 = relationship("CourierCarrier", back_populates="signatures")
    archive_entries         = relationship("CourierArchive", back_populates="signature")


class CourierArchive(Base):
    __tablename__ = "courier_archive"
    id                      = Column(Integer, primary_key=True)
    shipment_id             = Column(Integer, ForeignKey("courier_shipments.id"), nullable=False)
    signature_id            = Column(Integer, ForeignKey("courier_signatures.id"), nullable=False)
    signed_document_path    = Column(String, nullable=False)                  # gebrannter PKL/Lieferschein
    archive_path            = Column(String, nullable=False)                  # Pfad im Archiv-Ordner
    archived_at             = Column(DateTime, default=datetime.utcnow)
    shipment                = relationship("CourierShipment", back_populates="archive_entries")
    signature               = relationship("CourierSignature", back_populates="archive_entries")


# ── DB Dependency ──────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_courier_carriers()


def _seed_courier_carriers():
    """Default-Carrier (FedEx/TNT, DHL, UPS) anlegen, falls noch nicht vorhanden."""
    db = SessionLocal()
    try:
        if db.query(CourierCarrier).count() > 0:
            return

        defaults = [
            {
                "name": "fedex_tnt",
                "display_name": "FedEx / TNT",
                "detection_keywords": ["fedex", "tnt", "federal express"],
                # TNT-Override: zusätzlich EDEC drucken, wenn Keyword "tnt" matcht
                "print_set_rules": {
                    "default": ["label", "rechnung"],
                    "overrides": {"tnt": ["label", "rechnung", "edec"]},
                },
            },
            {
                "name": "dhl",
                "display_name": "DHL",
                "detection_keywords": ["dhl", "deutsche post"],
                "print_set_rules": {
                    "default": ["label", "rechnung", "lieferschein", "pkl", "edec", "to"],
                    "overrides": {},
                },
            },
            {
                "name": "ups",
                "display_name": "UPS",
                "detection_keywords": ["ups", "united parcel"],
                "print_set_rules": {
                    "default": ["label", "rechnung", "lieferschein", "pkl", "edec", "to"],
                    "overrides": {},
                },
            },
        ]

        for c in defaults:
            db.add(CourierCarrier(
                name=c["name"],
                display_name=c["display_name"],
                detection_keywords=json.dumps(c["detection_keywords"]),
                print_set_rules=json.dumps(c["print_set_rules"]),
                is_active=True,
            ))
        db.commit()
    finally:
        db.close()
