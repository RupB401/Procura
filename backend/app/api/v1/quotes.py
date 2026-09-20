"""
Quote API Router — Phase 4.
Vendors submit quotes; Buyers award quotes (with DB row locking).

Business rules enforced:
- Only VENDOR role can submit quotes
- RFQ must be OPEN to accept quotes
- Vendor may only submit one quote per RFQ
- Quote items must cover ALL RFQ line items
- total_bid_amount is server-calculated (not trusted from client)
- Only BUYER who owns the RFQ can award a quote
- Awarding uses SELECT FOR UPDATE to prevent race conditions
- Awarding transitions RFQ -> AWARDED and all other quotes -> REJECTED
"""
from typing import List, Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_buyer, get_current_user, get_current_vendor
from app.core.errors import ForbiddenException, NotFoundException, StateException, ValidationException
from app.db.session import get_db
from app.integrations.erp_transformer import build_erp_payload
from app.models.domain import Quote, QuoteItem, QuoteStatus, RFQ, RFQItem, RFQStatus, User
from app.schemas.quote import QuoteCreate, QuoteResponse
from app.services.audit import write_audit_log

router = APIRouter()


async def _get_rfq_or_404(rfq_id: UUID, db: AsyncSession) -> RFQ:
    result = await db.execute(
        select(RFQ).where(RFQ.id == rfq_id).options(selectinload(RFQ.items))
    )
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise NotFoundException(f"RFQ {rfq_id} not found")
    return rfq


@router.post("/{rfq_id}/quotes", response_model=QuoteResponse, status_code=201)
async def submit_quote(
    rfq_id: UUID,
    payload: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_vendor),
):
    """Vendor submits a quote for an OPEN RFQ."""
    rfq = await _get_rfq_or_404(rfq_id, db)

    if rfq.status != RFQStatus.OPEN:
        raise StateException("Quotes can only be submitted when RFQ is OPEN")

    # Prevent duplicate quotes from same vendor
    existing = await db.execute(
        select(Quote).where(Quote.rfq_id == rfq_id, Quote.vendor_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise ValidationException("You have already submitted a quote for this RFQ")

    # Validate that every RFQ item is covered
    rfq_item_ids = {item.id for item in rfq.items}
    submitted_item_ids = {item.rfq_item_id for item in payload.items}
    if rfq_item_ids != submitted_item_ids:
        raise ValidationException(
            "Quote must include a line item for every RFQ line item (no more, no less)"
        )

    # Fetch RFQ items keyed by id for quantity lookup
    rfq_items_map: Dict[UUID, RFQItem] = {item.id: item for item in rfq.items}

    # Server-side total calculation — never trust client-provided totals
    total = sum(
        float(item.unit_price) * float(rfq_items_map[item.rfq_item_id].required_quantity)
        for item in payload.items
    )

    quote = Quote(
        rfq_id=rfq_id,
        vendor_id=current_user.id,
        status=QuoteStatus.SUBMITTED,
        total_bid_amount=total,
    )
    db.add(quote)
    await db.flush()

    for item_in in payload.items:
        db.add(QuoteItem(quote_id=quote.id, **item_in.model_dump()))

    await write_audit_log(
        db, current_user.id, "QUOTE_SUBMITTED", "quotes", quote.id,
        {"rfq_id": str(rfq_id), "total_bid_amount": total}
    )
    await db.commit()
    await db.refresh(quote)

    result = await db.execute(
        select(Quote).where(Quote.id == quote.id).options(selectinload(Quote.items))
    )
    return result.scalar_one()


@router.get("/{rfq_id}/quotes", response_model=List[QuoteResponse])
async def list_quotes(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List quotes for an RFQ.
    - BUYER: sees all quotes (only when UNDER_REVIEW or AWARDED)
    - VENDOR: sees only their own quote
    """
    rfq = await _get_rfq_or_404(rfq_id, db)

    if current_user.role == "BUYER":
        if rfq.buyer_id != current_user.id:
            raise ForbiddenException("You do not own this RFQ")
        if rfq.status not in (RFQStatus.UNDER_REVIEW, RFQStatus.AWARDED):
            raise StateException("Quotes are only visible once RFQ is UNDER_REVIEW or AWARDED")
        result = await db.execute(
            select(Quote).where(Quote.rfq_id == rfq_id).options(selectinload(Quote.items))
        )
    else:
        # Vendor sees only their own quote
        result = await db.execute(
            select(Quote)
            .where(Quote.rfq_id == rfq_id, Quote.vendor_id == current_user.id)
            .options(selectinload(Quote.items))
        )

    return result.scalars().all()


@router.post("/{rfq_id}/quotes/{quote_id}/award", response_model=Dict[str, Any])
async def award_quote(
    rfq_id: UUID,
    quote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
):
    """
    Award a specific quote. Uses SELECT FOR UPDATE row lock to prevent race conditions.
    - RFQ must be in UNDER_REVIEW state
    - Winning quote -> AWARDED
    - All other quotes -> REJECTED
    - RFQ -> AWARDED
    - Returns ERP payload for integration
    """
    # Lock the RFQ row
    result = await db.execute(
        select(RFQ)
        .where(RFQ.id == rfq_id)
        .with_for_update()
        .options(selectinload(RFQ.items))
    )
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise NotFoundException(f"RFQ {rfq_id} not found")

    if rfq.buyer_id != current_user.id:
        raise ForbiddenException("You do not own this RFQ")

    if rfq.status != RFQStatus.UNDER_REVIEW:
        raise StateException("Quotes can only be awarded when RFQ is UNDER_REVIEW")

    # Fetch winning quote with its items and rfq_item references
    win_result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.rfq_id == rfq_id)
        .with_for_update()
        .options(selectinload(Quote.items).selectinload(QuoteItem.rfq_item))
    )
    winner = win_result.scalar_one_or_none()
    if not winner:
        raise NotFoundException(f"Quote {quote_id} not found for this RFQ")

    if winner.status != QuoteStatus.SUBMITTED:
        raise StateException("Only SUBMITTED quotes can be awarded")

    # Reject all other quotes
    all_quotes_result = await db.execute(
        select(Quote).where(Quote.rfq_id == rfq_id, Quote.id != quote_id)
    )
    for q in all_quotes_result.scalars().all():
        q.status = QuoteStatus.REJECTED
        await write_audit_log(
            db, current_user.id, "QUOTE_REJECTED", "quotes", q.id,
            {"rfq_id": str(rfq_id), "reason": "Another quote was awarded"}
        )

    # Award the winner
    winner.status = QuoteStatus.AWARDED
    rfq.status = RFQStatus.AWARDED

    await write_audit_log(
        db, current_user.id, "QUOTE_AWARDED", "quotes", winner.id,
        {"rfq_id": str(rfq_id), "total_bid_amount": float(winner.total_bid_amount)}
    )
    await write_audit_log(
        db, current_user.id, "RFQ_AWARDED", "rfqs", rfq.id,
        {"awarded_quote_id": str(winner.id)}
    )

    # Build ERP payload before commit
    erp_payload = build_erp_payload(rfq, winner)

    await db.commit()

    return {
        "message": "Quote awarded successfully",
        "awarded_quote_id": str(winner.id),
        "erp_payload": erp_payload,
    }
