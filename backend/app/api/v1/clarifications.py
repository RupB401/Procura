"""
Clarification API Router — Phase 4.

Rules from MASTER_PROMPT:
- VENDOR can ask questions on OPEN RFQs
- Questions are anonymized when returned to other vendors (asked_by_vendor_id is omitted)
- BUYER sees who asked (asked_by_vendor_id is included)
- BUYER answers questions; answered questions are broadcast to all vendors
- Rate limit: 20 clarifications/min (handled in middleware)
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.api.deps import get_current_buyer, get_current_user, get_current_vendor
from app.core.errors import ForbiddenException, NotFoundException, StateException
from app.db.session import get_db
from app.models.domain import ClarificationThread, RFQ, RFQStatus, User
from app.schemas.clarification import ClarificationAnswer, ClarificationCreate, ClarificationResponse
from app.services.audit import write_audit_log

router = APIRouter()


async def _get_rfq_or_404(rfq_id: UUID, db: AsyncSession) -> RFQ:
    result = await db.execute(select(RFQ).where(RFQ.id == rfq_id))
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise NotFoundException(f"RFQ {rfq_id} not found")
    return rfq


@router.post("/{rfq_id}/clarifications", response_model=ClarificationResponse, status_code=201)
async def ask_clarification(
    rfq_id: UUID,
    payload: ClarificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_vendor),
):
    """Vendor asks a clarification question on an OPEN RFQ."""
    rfq = await _get_rfq_or_404(rfq_id, db)

    if rfq.status != RFQStatus.OPEN:
        raise StateException("Clarifications can only be asked on OPEN RFQs")

    thread = ClarificationThread(
        rfq_id=rfq_id,
        asked_by_vendor_id=current_user.id,
        question=payload.question,
        is_broadcast=True,  # per MASTER_PROMPT: all answered Q&As are broadcast
    )
    db.add(thread)
    await db.flush()

    await write_audit_log(
        db, current_user.id, "CLARIFICATION_ASKED", "clarification_threads", thread.id,
        {"rfq_id": str(rfq_id)}
    )
    await db.commit()
    await db.refresh(thread)

    # Return with vendor identity visible only to themselves
    response = ClarificationResponse.model_validate(thread)
    return response


@router.get("/{rfq_id}/clarifications", response_model=List[ClarificationResponse])
async def list_clarifications(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List clarification threads for an RFQ.
    - BUYER sees asked_by_vendor_id on all questions.
    - VENDOR sees asked_by_vendor_id only on their own questions; others are anonymized (null).
    """
    rfq = await _get_rfq_or_404(rfq_id, db)

    # Vendors can only view clarifications for OPEN / UNDER_REVIEW / AWARDED RFQs
    if current_user.role == "VENDOR" and rfq.status not in (
        RFQStatus.OPEN, RFQStatus.UNDER_REVIEW, RFQStatus.AWARDED
    ):
        raise ForbiddenException("You do not have access to this RFQ")

    result = await db.execute(
        select(ClarificationThread)
        .where(ClarificationThread.rfq_id == rfq_id)
        .order_by(ClarificationThread.created_at.asc())
    )
    threads = result.scalars().all()

    responses = []
    for thread in threads:
        data = ClarificationResponse.model_validate(thread)
        # Anonymize: vendors see NULL vendor_id unless it's their own question
        if current_user.role == "VENDOR" and thread.asked_by_vendor_id != current_user.id:
            data.asked_by_vendor_id = None
        responses.append(data)

    return responses


@router.post(
    "/{rfq_id}/clarifications/{thread_id}/answer",
    response_model=ClarificationResponse,
)
async def answer_clarification(
    rfq_id: UUID,
    thread_id: UUID,
    payload: ClarificationAnswer,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Buyer answers a clarification question. Answer is broadcast to all vendors."""
    rfq = await _get_rfq_or_404(rfq_id, db)

    if rfq.buyer_id != current_user.id:
        raise ForbiddenException("You do not own this RFQ")

    result = await db.execute(
        select(ClarificationThread).where(
            ClarificationThread.id == thread_id,
            ClarificationThread.rfq_id == rfq_id,
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise NotFoundException("Clarification thread not found")

    if thread.answer is not None:
        raise StateException("This question has already been answered")

    thread.answer = payload.answer
    thread.answered_at = datetime.now(timezone.utc)

    await write_audit_log(
        db, current_user.id, "CLARIFICATION_ANSWERED", "clarification_threads", thread.id,
        {"rfq_id": str(rfq_id)}
    )
    await db.commit()
    await db.refresh(thread)
    return thread
