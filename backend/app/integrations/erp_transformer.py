"""
ERP Payload Transformer.
Converts internal awarded Quote + RFQ data into a structured
ERP-compatible purchase order payload (JSON), as required by MASTER_PROMPT.
"""
from typing import Any, Dict
from app.models.domain import Quote, RFQ


def build_erp_payload(rfq: RFQ, quote: Quote) -> Dict[str, Any]:
    """
    Transform awarded quote data into an ERP purchase order payload.
    Structure follows a generic ERP PO schema.
    """
    line_items = []
    for qi in quote.items:
        line_items.append({
            "line_number": len(line_items) + 1,
            "item_code": qi.rfq_item.item_code if qi.rfq_item else str(qi.rfq_item_id),
            "description": qi.rfq_item.description if qi.rfq_item else "",
            "ordered_quantity": float(qi.rfq_item.required_quantity) if qi.rfq_item else 0,
            "unit_of_measure": qi.rfq_item.unit_of_measure if qi.rfq_item else "",
            "unit_price": float(qi.unit_price),
            "lead_time_days": qi.lead_time_days,
            "line_total": float(qi.unit_price) * float(qi.rfq_item.required_quantity if qi.rfq_item else 0),
        })

    return {
        "erp_document_type": "PURCHASE_ORDER",
        "source_system": "RFQ_PLATFORM",
        "rfq_id": str(rfq.id),
        "rfq_title": rfq.title,
        "purchase_order": {
            "po_reference": f"PO-{str(rfq.id)[:8].upper()}",
            "currency_code": rfq.currency_code,
            "vendor_id": str(quote.vendor_id),
            "quote_id": str(quote.id),
            "total_amount": float(quote.total_bid_amount),
            "line_items": line_items,
        },
    }
