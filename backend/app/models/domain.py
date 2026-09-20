import uuid
from sqlalchemy import Column, String, Text, Boolean, Numeric, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class RFQStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    AWARDED = "AWARDED"
    CANCELLED = "CANCELLED"

class QuoteStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    REJECTED = "REJECTED"
    AWARDED = "AWARDED"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False) # 'BUYER' or 'VENDOR'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SAEnum(RFQStatus, name="rfq_status"), default=RFQStatus.DRAFT, nullable=False, index=True)
    submission_deadline = Column(DateTime(timezone=True), nullable=False, index=True)
    currency_code = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="rfq")
    clarifications = relationship("ClarificationThread", back_populates="rfq")

class RFQItem(Base):
    __tablename__ = "rfq_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), index=True)
    item_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    required_quantity = Column(Numeric(12, 2), nullable=False)
    unit_of_measure = Column(String(25), nullable=False)

    rfq = relationship("RFQ", back_populates="items")
    quote_items = relationship("QuoteItem", back_populates="rfq_item")

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status = Column(SAEnum(QuoteStatus, name="quote_status"), default=QuoteStatus.SUBMITTED, nullable=False)
    total_bid_amount = Column(Numeric(15, 2), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    rfq = relationship("RFQ", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

class QuoteItem(Base):
    __tablename__ = "quote_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    rfq_item_id = Column(UUID(as_uuid=True), ForeignKey("rfq_items.id", ondelete="RESTRICT"), index=True)
    unit_price = Column(Numeric(12, 2), nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_order_quantity = Column(Numeric(12, 2), default=0.00)
    notes = Column(Text)

    quote = relationship("Quote", back_populates="items")
    rfq_item = relationship("RFQItem", back_populates="quote_items")

class ClarificationThread(Base):
    __tablename__ = "clarification_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), index=True)
    asked_by_vendor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    is_broadcast = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    answered_at = Column(DateTime(timezone=True), nullable=True)

    rfq = relationship("RFQ", back_populates="clarifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)
    target_table = Column(String(100), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    delta_changes = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

