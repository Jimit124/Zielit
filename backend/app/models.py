import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Date, DateTime, ForeignKey, CheckConstraint,
    UniqueConstraint, ARRAY, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    contact_email = Column(Text, nullable=False)
    api_key = Column(Text, unique=True, nullable=False)
    sftp_username = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="customer", cascade="all, delete")
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete")
    segments = relationship("Segment", back_populates="customer", cascade="all, delete")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    filename = Column(Text, nullable=False)
    source = Column(Text, nullable=False)  # 'sftp' | 'api'
    status = Column(Text, nullable=False, default="processing")  # processing|complete|failed
    row_count = Column(Integer, default=0)
    loaded_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_report = Column(JSONB, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    customer = relationship("Customer", back_populates="uploads")

    __table_args__ = (
        CheckConstraint("source IN ('sftp','api')", name="ck_upload_source"),
        CheckConstraint("status IN ('processing','complete','failed')", name="ck_upload_status"),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    email = Column(Text, nullable=False)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    company = Column(Text, nullable=True)
    industry = Column(Text, nullable=True)
    job_title = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    engagement_score = Column(Integer, default=0)
    last_purchase_date = Column(Date, nullable=True)
    consent_status = Column(Text, nullable=False, default="unknown")  # opted_in|opted_out|unknown
    consent_date = Column(Date, nullable=True)
    tags = Column(ARRAY(String), default=list)
    source_upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="contacts")

    __table_args__ = (
        UniqueConstraint("customer_id", "email", name="uq_contact_customer_email"),
        CheckConstraint("consent_status IN ('opted_in','opted_out','unknown')", name="ck_consent_status"),
    )


class Segment(Base):
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    rules = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    customer = relationship("Customer", back_populates="segments")
