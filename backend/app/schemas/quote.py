from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.domain import QuoteStatus


class QuoteItemCreate(BaseModel):
    rfq_item_id: UUID
    unit_price: float = Field(..., gt=0)
    lead_time_days: int = Field(..., gt=0)
    min_order_quantity: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class QuoteItemResponse(BaseModel):
    id: UUID
    rfq_item_id: UUID
    unit_price: float
    lead_time_days: int
    min_order_quantity: float
    notes: Optional[str]

    class Config:
        from_attributes = True


class QuoteCreate(BaseModel):
    items: List[QuoteItemCreate] = Field(..., min_length=1)


class QuoteResponse(BaseModel):
    id: UUID
    rfq_id: UUID
    vendor_id: UUID
    status: QuoteStatus
    total_bid_amount: float
    submitted_at: datetime
    items: List[QuoteItemResponse] = []

    class Config:
        from_attributes = True
