#!/usr/bin/env python3
"""
Seed Script — Procura Demo Data
================================
Creates demo accounts and a sample RFQ with line items.

Run inside the backend container:
  docker-compose exec backend python seed.py

Demo Credentials created:
  Buyer  → buyer@procura.demo  / DemoPass1234!
  Vendor → vendor@procura.demo / DemoPass1234!
"""
import asyncio
import sys
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

sys.path.insert(0, "/app")

from app.db.session import AsyncSessionLocal
from app.models.domain import User, RFQ, RFQItem, RFQStatus
from app.core.security import get_password_hash

BUYER_EMAIL  = "buyer@procura.demo"
VENDOR_EMAIL = "vendor@procura.demo"
DEMO_PASS    = "DemoPass1234!"

SAMPLE_RFQ = {
    "title": "Office Equipment Procurement Q4 2026",
    "description": "Quarterly procurement of standard office supplies and equipment for HQ.",
    "currency_code": "USD",
    "items": [
        {"item_code": "LAPTOP-001",  "description": "Business laptop 14-inch, 16GB RAM, 512GB SSD", "required_quantity": 10,  "unit_of_measure": "PCS"},
        {"item_code": "MONITOR-002", "description": "27-inch 4K IPS monitor, USB-C hub",             "required_quantity": 10,  "unit_of_measure": "PCS"},
        {"item_code": "CHAIR-003",   "description": "Ergonomic office chair with lumbar support",    "required_quantity": 20,  "unit_of_measure": "PCS"},
        {"item_code": "PAPER-004",   "description": "A4 copy paper, 80gsm, 500 sheets/ream",        "required_quantity": 200, "unit_of_measure": "BOX"},
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:
        # ── Buyer ──────────────────────────────────────────────────────────
        result = await db.execute(select(User).where(User.email == BUYER_EMAIL))
        buyer = result.scalar_one_or_none()
        if not buyer:
            buyer = User(
                email=BUYER_EMAIL,
                hashed_password=get_password_hash(DEMO_PASS),
                company_name="Procura HQ (Demo Buyer)",
                role="BUYER",
            )
            db.add(buyer)
            await db.flush()
            print(f"  [+] Created buyer: {BUYER_EMAIL}")
        else:
            print(f"  [~] Buyer already exists: {BUYER_EMAIL}")

        # ── Vendor ─────────────────────────────────────────────────────────
        result = await db.execute(select(User).where(User.email == VENDOR_EMAIL))
        vendor = result.scalar_one_or_none()
        if not vendor:
            vendor = User(
                email=VENDOR_EMAIL,
                hashed_password=get_password_hash(DEMO_PASS),
                company_name="SupplyChain Pro (Demo Vendor)",
                role="VENDOR",
            )
            db.add(vendor)
            await db.flush()
            print(f"  [+] Created vendor: {VENDOR_EMAIL}")
        else:
            print(f"  [~] Vendor already exists: {VENDOR_EMAIL}")

        # ── Sample RFQ (OPEN) ──────────────────────────────────────────────
        result = await db.execute(
            select(RFQ).where(RFQ.title == SAMPLE_RFQ["title"], RFQ.buyer_id == buyer.id)
        )
        if not result.scalar_one_or_none():
            rfq = RFQ(
                buyer_id=buyer.id,
                title=SAMPLE_RFQ["title"],
                description=SAMPLE_RFQ["description"],
                currency_code=SAMPLE_RFQ["currency_code"],
                submission_deadline=datetime.now(timezone.utc) + timedelta(days=7),
                status=RFQStatus.OPEN,   # Already published so vendor can see it immediately
            )
            db.add(rfq)
            await db.flush()

            for item_data in SAMPLE_RFQ["items"]:
                db.add(RFQItem(rfq_id=rfq.id, **item_data))

            print(f"  [+] Created OPEN RFQ: {rfq.title}")
        else:
            print(f"  [~] Sample RFQ already exists")

        await db.commit()

    print("\n✅ Seeding complete.")
    print("\nDemo credentials:")
    print(f"  Buyer  → {BUYER_EMAIL}  /  {DEMO_PASS}")
    print(f"  Vendor → {VENDOR_EMAIL}  /  {DEMO_PASS}")
    print(f"\n  Frontend : http://localhost:3000")
    print(f"  API Docs : http://localhost:8001/api/v1/docs")


if __name__ == "__main__":
    asyncio.run(seed())
