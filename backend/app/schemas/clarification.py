from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ClarificationCreate(BaseModel):
    question: str = Field(..., min_length=10)


class ClarificationAnswer(BaseModel):
    answer: str = Field(..., min_length=1)


class ClarificationResponse(BaseModel):
    id: UUID
    rfq_id: UUID
    # Vendor identity is anonymized per MASTER_PROMPT: only buyer sees who asked
    asked_by_vendor_id: Optional[UUID] = None
    question: str
    answer: Optional[str] = None
    is_broadcast: bool
    created_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
