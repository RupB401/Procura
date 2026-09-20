"""
RFQ API Router — Phase 4.
Implements full CRUD + state-machine transitions as per MASTER_PROMPT.

State transitions (BUYER only):
  DRAFT -> OPEN          (publish)
  OPEN  -> UNDER_REVIEW  (close bidding)
  OPEN  -> CANCELLED     (cancel)
  UNDER_REVIEW -> AWARDED (done via quote award)
  UNDER_REVIEW -> CANCELLED
"""
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_buyer, get_current_user
from app.core.errors import ForbiddenException, NotFoundException, StateException, ValidationException
from app.db.session import get_db
from app.models.domain import RFQ, RFQItem, RFQStatus, User
from app.schemas.rfq import RFQCreate, RFQListResponse, RFQResponse, RFQUpdate
from app.services.audit import write_audit_log

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS = {
    RFQStatus.DRAFT: {RFQStatus.OPEN, RFQStatus.CANCELLED},
    RFQStatus.OPEN: {RFQStatus.UNDER_REVIEW, RFQStatus.CANCELLED},
    RFQStatus.UNDER_REVIEW: {RFQStatus.AWARDED, RFQStatus.CANCELLED},
    RFQStatus.AWARDED: set(),
    RFQStatus.CANCELLED: set(),
}


async def _get_rfq_or_404(rfq_id: UUID, db: AsyncSession, load_items: bool = False) -> RFQ:
    q = select(RFQ).where(RFQ.id == rfq_id)
    if load_items:
        q = q.options(selectinload(RFQ.items))
    result = await db.execute(q)
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise NotFoundException(f"RFQ {rfq_id} not found")
    return rfq


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=RFQResponse, status_code=201)
async def create_rfq(
    payload: RFQCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Create a new RFQ in DRAFT status (BUYER only)."""
    if payload.submission_deadline <= datetime.now(timezone.utc):
        raise ValidationException("submission_deadline must be in the future")

    rfq = RFQ(
        buyer_id=current_user.id,
        title=payload.title,
        description=payload.description,
        submission_deadline=payload.submission_deadline,
        currency_code=payload.currency_code.upper(),
        status=RFQStatus.DRAFT,
    )
    db.add(rfq)
    await db.flush()  # get rfq.id before inserting items

    for item_in in payload.items:
        db.add(RFQItem(rfq_id=rfq.id, **item_in.model_dump()))

    await write_audit_log(
        db, current_user.id, "RFQ_CREATED", "rfqs", rfq.id,
        {"title": rfq.title, "status": rfq.status.value}
    )
    await db.commit()
    await db.refresh(rfq)
    # reload with items
    return await _get_rfq_or_404(rfq.id, db, load_items=True)


@router.get("", response_model=List[RFQListResponse])
async def list_rfqs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List RFQs.
    - BUYER: sees own RFQs only.
    - VENDOR: sees all OPEN / UNDER_REVIEW RFQs.
    """
    if current_user.role == "BUYER":
        result = await db.execute(select(RFQ).where(RFQ.buyer_id == current_user.id).order_by(RFQ.created_at.desc()))
    else:
        result = await db.execute(
            select(RFQ)
            .where(RFQ.status.in_([RFQStatus.OPEN, RFQStatus.UNDER_REVIEW]))
            .order_by(RFQ.submission_deadline.asc())
        )
    return result.scalars().all()


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single RFQ with its line items."""
    rfq = await _get_rfq_or_404(rfq_id, db, load_items=True)

    # Vendors may only view OPEN / UNDER_REVIEW / AWARDED RFQs
    if current_user.role == "VENDOR" and rfq.status not in (
        RFQStatus.OPEN, RFQStatus.UNDER_REVIEW, RFQStatus.AWARDED
    ):
        raise ForbiddenException("You do not have access to this RFQ")

    # Buyers may only view their own RFQs
    if current_user.role == "BUYER" and rfq.buyer_id != current_user.id:
        raise ForbiddenException("You do not have access to this RFQ")

    return rfq


@router.patch("/{rfq_id}", response_model=RFQResponse)
async def update_rfq(
    rfq_id: UUID,
    payload: RFQUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Update RFQ metadata. Only allowed in DRAFT status."""
    rfq = await _get_rfq_or_404(rfq_id, db, load_items=True)

    if rfq.buyer_id != current_user.id:
        raise ForbiddenException("You do not own this RFQ")
    if rfq.status != RFQStatus.DRAFT:
        raise StateException("Only DRAFT RFQs can be edited")

    changes = {}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(rfq, field, value)
            changes[field] = str(value)

    await write_audit_log(db, current_user.id, "RFQ_UPDATED", "rfqs", rfq.id, changes)
    await db.commit()
    return await _get_rfq_or_404(rfq_id, db, load_items=True)


@router.post("/{rfq_id}/publish", response_model=RFQResponse)
async def publish_rfq(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Transition RFQ from DRAFT -> OPEN."""
    return await _transition(rfq_id, RFQStatus.OPEN, db, current_user, "RFQ_PUBLISHED")


@router.post("/{rfq_id}/close", response_model=RFQResponse)
async def close_rfq(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Transition RFQ from OPEN -> UNDER_REVIEW."""
    return await _transition(rfq_id, RFQStatus.UNDER_REVIEW, db, current_user, "RFQ_CLOSED")


@router.post("/{rfq_id}/cancel", response_model=RFQResponse)
async def cancel_rfq(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """Cancel an RFQ from DRAFT, OPEN, or UNDER_REVIEW."""
    return await _transition(rfq_id, RFQStatus.CANCELLED, db, current_user, "RFQ_CANCELLED")


async def _transition(
    rfq_id: UUID,
    new_status: RFQStatus,
    db: AsyncSession,
    current_user: User,
    action_type: str,
) -> RFQ:
    rfq = await _get_rfq_or_404(rfq_id, db, load_items=True)

    if rfq.buyer_id != current_user.id:
        raise ForbiddenException("You do not own this RFQ")

    if new_status not in _VALID_TRANSITIONS.get(rfq.status, set()):
        raise StateException(
            f"Cannot transition from {rfq.status.value} to {new_status.value}"
        )

    old_status = rfq.status.value
    rfq.status = new_status
    await write_audit_log(
        db, current_user.id, action_type, "rfqs", rfq.id,
        {"old_status": old_status, "new_status": new_status.value}
    )
    await db.commit()
    return await _get_rfq_or_404(rfq_id, db, load_items=True)
