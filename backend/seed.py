#!/usr/bin/env python3
"""
Seed Script — Procura Showcase Demo Data
========================================
Creates demo accounts and multiple RFQs in various states to showcase the dashboard.
"""
import asyncio
import sys
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

sys.path.insert(0, "/app")

from app.db.session import AsyncSessionLocal
from app.models.domain import User, RFQ, RFQItem, RFQStatus, Quote, QuoteItem, QuoteStatus, ClarificationThread
from app.core.security import get_password_hash

BUYER_EMAIL  = "buyer@test.com"
VENDOR_EMAIL = "vendor1@test.com"
VENDOR2_EMAIL = "vendor2@test.com"
DEMO_PASS    = "TestPass123!"

async def seed():
    async with AsyncSessionLocal() as db:
        # Create users
        users = []
        for em, comp, role in [
            (BUYER_EMAIL, "Procura HQ Buyer", "BUYER"),
            (VENDOR_EMAIL, "TechSupply Inc Vendor", "VENDOR"),
            (VENDOR2_EMAIL, "Global Solutions Vendor", "VENDOR")
        ]:
            res = await db.execute(select(User).where(User.email == em))
            u = res.scalar_one_or_none()
            if not u:
                u = User(email=em, hashed_password=get_password_hash(DEMO_PASS), company_name=comp, role=role)
                db.add(u)
                await db.flush()
            users.append(u)
            
        buyer, v1, v2 = users

        # Sample RFQs
        rfqs_data = [
            {
                "title": "Office Equipment Procurement Q4 2026",
                "desc": "Quarterly procurement of standard office supplies and equipment.",
                "status": RFQStatus.OPEN,
                "days": 7,
                "items": [
                    {"code": "LAP-01", "desc": "Business laptop 14-inch", "qty": 10, "uom": "PCS", "est": 1200},
                    {"code": "MON-01", "desc": "27-inch 4K monitor", "qty": 10, "uom": "PCS", "est": 300},
                ]
            },
            {
                "title": "Data Center Server Upgrade",
                "desc": "Looking for high-density rack servers.",
                "status": RFQStatus.OPEN,
                "days": 14,
                "items": [
                    {"code": "SRV-2U", "desc": "2U Rack Server, 64-core", "qty": 5, "uom": "PCS", "est": 8500},
                ]
            },
            {
                "title": "Cloud Infrastructure Migration Consulting",
                "desc": "Need expert consulting for AWS migration.",
                "status": RFQStatus.DRAFT,
                "days": 30,
                "items": [
                    {"code": "CONSULT", "desc": "Senior Cloud Architect Hours", "qty": 160, "uom": "HRS", "est": 150},
                ]
            },
            {
                "title": "Q3 Network Switch Refresh",
                "desc": "Replacing edge switches in branch offices.",
                "status": RFQStatus.UNDER_REVIEW,
                "days": -2,
                "items": [
                    {"code": "SW-48P", "desc": "48-port PoE+ Switch", "qty": 12, "uom": "PCS", "est": 2200},
                ]
            },
            {
                "title": "Archived: Fleet Vehicles 2025",
                "desc": "Purchase of 5 electric sedans.",
                "status": RFQStatus.AWARDED,
                "days": -30,
                "items": [
                    {"code": "EV-SEDAN", "desc": "Electric Sedan, >300mi range", "qty": 5, "uom": "PCS", "est": 45000},
                ]
            }
        ]

        # Check if already seeded
        res = await db.execute(select(RFQ).where(RFQ.buyer_id == buyer.id))
        if res.scalars().first():
            print("Already seeded. Clearing out old data (simulating account delete setup)...")
            await db.delete(buyer) # Cascades will drop everything
            await db.flush()
            # Recreate buyer
            buyer = User(email=BUYER_EMAIL, hashed_password=get_password_hash(DEMO_PASS), company_name="Procura HQ Buyer", role="BUYER")
            db.add(buyer)
            await db.flush()
            
        print("Seeding RFQs...")
        for r_data in rfqs_data:
            rfq = RFQ(
                buyer_id=buyer.id,
                title=r_data["title"],
                description=r_data["desc"],
                status=r_data["status"],
                submission_deadline=datetime.now(timezone.utc) + timedelta(days=r_data["days"]),
                currency_code="USD"
            )
            db.add(rfq)
            await db.flush()
            
            items = []
            for idata in r_data["items"]:
                it = RFQItem(rfq_id=rfq.id, item_code=idata["code"], description=idata["desc"], required_quantity=idata["qty"], unit_of_measure=idata["uom"])
                db.add(it)
                items.append((it, idata["est"]))
            await db.flush()
            
            # Add quotes if it's OPEN, UNDER_REVIEW or AWARDED
            if r_data["status"] in [RFQStatus.OPEN, RFQStatus.UNDER_REVIEW, RFQStatus.AWARDED]:
                # Vendor 1 quotes
                q1_tot = 0
                q1 = Quote(rfq_id=rfq.id, vendor_id=v1.id, status=QuoteStatus.SUBMITTED, total_bid_amount=0)
                db.add(q1)
                await db.flush()
                for it, est in items:
                    price = est * random.uniform(0.9, 1.1)
                    q1_tot += price * float(it.required_quantity)
                    db.add(QuoteItem(quote_id=q1.id, rfq_item_id=it.id, unit_price=price, lead_time_days=random.randint(5,14)))
                q1.total_bid_amount = q1_tot
                
                # Vendor 2 quotes on some
                if random.choice([True, False]):
                    q2_tot = 0
                    q2 = Quote(rfq_id=rfq.id, vendor_id=v2.id, status=QuoteStatus.SUBMITTED, total_bid_amount=0)
                    db.add(q2)
                    await db.flush()
                    for it, est in items:
                        price = est * random.uniform(0.85, 1.15)
                        q2_tot += price * float(it.required_quantity)
                        db.add(QuoteItem(quote_id=q2.id, rfq_item_id=it.id, unit_price=price, lead_time_days=random.randint(7,21)))
                    q2.total_bid_amount = q2_tot

                if r_data["status"] == RFQStatus.AWARDED:
                    q1.status = QuoteStatus.AWARDED

            # Add some Q&A for OPEN RFQs
            if r_data["status"] == RFQStatus.OPEN:
                ct = ClarificationThread(
                    rfq_id=rfq.id,
                    asked_by_vendor_id=v1.id,
                    question="Does the laptop requirement include accidental damage protection?",
                    answer="Yes, please include 3-year ADP in the unit price.",
                    answered_at=datetime.now(timezone.utc)
                )
                db.add(ct)

        await db.commit()
        print("✅ Showcase seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
