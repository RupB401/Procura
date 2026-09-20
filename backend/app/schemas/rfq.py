from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.domain import RFQStatus


class RFQItemCreate(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    required_quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., min_length=1, max_length=25)


class RFQItemResponse(RFQItemCreate):
    id: UUID
    rfq_id: UUID

    class Config:
        from_attributes = True


class RFQCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    submission_deadline: datetime
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    items: List[RFQItemCreate] = Field(..., min_length=1)


class RFQUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)


class RFQResponse(BaseModel):
    id: UUID
    buyer_id: UUID
    title: str
    description: Optional[str]
    status: RFQStatus
    submission_deadline: datetime
    currency_code: str
    created_at: datetime
    updated_at: datetime
    items: List[RFQItemResponse] = []

    class Config:
        from_attributes = True


class RFQListResponse(BaseModel):
    id: UUID
    buyer_id: UUID
    title: str
    status: RFQStatus
    submission_deadline: datetime
    currency_code: str
    created_at: datetime

    class Config:
        from_attributes = True
