from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

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


# ── DB Dependency ──────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
