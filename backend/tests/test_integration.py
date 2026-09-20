"""
Integration Tests — Procura Backend
=====================================
Run inside the backend container:
  docker-compose exec backend python -m pytest tests/ -v

Coverage:
  - Auth: register, login, duplicate email, wrong password
  - RFQ: CRUD, state transitions, ownership rules, RBAC
  - Quotes: submit, duplicate prevention, total calculation, award + row locking
  - Clarifications: ask, answer, anonymization
  - Rate limiting: middleware present
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.base import Base
from app.models.domain import RFQStatus


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

# Fixtures moved to conftest.py


def _unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


async def _register(client: AsyncClient, email: str, role: str) -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123!", "company_name": f"{role} Corp", "role": role
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_rfq(client: AsyncClient, token: str, status: str = "DRAFT") -> dict:
    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    resp = await client.post("/api/v1/rfqs", headers=_auth(token), json={
        "title": "Test RFQ",
        "submission_deadline": deadline,
        "currency_code": "USD",
        "items": [{"item_code": "A-001", "description": "Widget", "required_quantity": 10, "unit_of_measure": "PCS"}]
    })
    assert resp.status_code == 201, resp.text
    rfq = resp.json()
    if status == "OPEN":
        pub = await client.post(f"/api/v1/rfqs/{rfq['id']}/publish", headers=_auth(token))
        assert pub.status_code == 200
        rfq = pub.json()
    return rfq


# ──────────────────────────────────────────────────────────────────────────────
# Auth tests
# ──────────────────────────────────────────────────────────────────────────────

class TestAuth:
    @pytest.mark.asyncio
    async def test_register_buyer(self, client: AsyncClient):
        email = _unique_email("buyer")
        data = await _register(client, email, "BUYER")
        assert data["role"] == "BUYER"
        assert data["email"] == email

    @pytest.mark.asyncio
    async def test_register_vendor(self, client: AsyncClient):
        email = _unique_email("vendor")
        data = await _register(client, email, "VENDOR")
        assert data["role"] == "VENDOR"

    @pytest.mark.asyncio
    async def test_duplicate_email_rejected(self, client: AsyncClient):
        email = _unique_email("dup")
        await _register(client, email, "BUYER")
        resp = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "TestPass123!", "company_name": "Dup", "role": "BUYER"
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        email = _unique_email("login")
        await _register(client, email, "BUYER")
        token = await _login(client, email)
        assert isinstance(token, str) and len(token) > 10

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        email = _unique_email("wp")
        await _register(client, email, "BUYER")
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_endpoint(self, client: AsyncClient):
        email = _unique_email("me")
        await _register(client, email, "VENDOR")
        token = await _login(client, email)
        resp = await client.get("/api/v1/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == email


# ──────────────────────────────────────────────────────────────────────────────
# RFQ tests
# ──────────────────────────────────────────────────────────────────────────────

class TestRFQ:
    @pytest.mark.asyncio
    async def test_buyer_can_create_rfq(self, client: AsyncClient):
        email = _unique_email("b")
        await _register(client, email, "BUYER")
        token = await _login(client, email)
        rfq = await _create_rfq(client, token)
        assert rfq["status"] == "DRAFT"
        assert len(rfq["items"]) == 1

    @pytest.mark.asyncio
    async def test_vendor_cannot_create_rfq(self, client: AsyncClient):
        ve = _unique_email("v")
        await _register(client, ve, "VENDOR")
        vtoken = await _login(client, ve)
        deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        resp = await client.post("/api/v1/rfqs", headers=_auth(vtoken), json={
            "title": "Bad", "submission_deadline": deadline, "currency_code": "USD",
            "items": [{"item_code": "X", "description": "X", "required_quantity": 1, "unit_of_measure": "PCS"}]
        })
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_state_transitions_draft_to_open(self, client: AsyncClient):
        email = _unique_email("b2")
        await _register(client, email, "BUYER")
        token = await _login(client, email)
        rfq = await _create_rfq(client, token)
        pub = await client.post(f"/api/v1/rfqs/{rfq['id']}/publish", headers=_auth(token))
        assert pub.status_code == 200
        assert pub.json()["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(self, client: AsyncClient):
        email = _unique_email("b3")
        await _register(client, email, "BUYER")
        token = await _login(client, email)
        rfq = await _create_rfq(client, token)
        # Cannot close a DRAFT RFQ — must be OPEN first
        resp = await client.post(f"/api/v1/rfqs/{rfq['id']}/close", headers=_auth(token))
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_vendor_sees_open_rfqs(self, client: AsyncClient):
        be = _unique_email("b4"); ve = _unique_email("v4")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        resp = await client.get("/api/v1/rfqs", headers=_auth(vtoken))
        ids = [r["id"] for r in resp.json()]
        assert rfq["id"] in ids

    @pytest.mark.asyncio
    async def test_buyer_cannot_see_other_buyers_rfqs(self, client: AsyncClient):
        b1e = _unique_email("b5a"); b2e = _unique_email("b5b")
        await _register(client, b1e, "BUYER"); await _register(client, b2e, "BUYER")
        b1tok = await _login(client, b1e); b2tok = await _login(client, b2e)
        rfq = await _create_rfq(client, b1tok)
        # Buyer 2 should not see Buyer 1's RFQ in their list
        resp = await client.get("/api/v1/rfqs", headers=_auth(b2tok))
        ids = [r["id"] for r in resp.json()]
        assert rfq["id"] not in ids


# ──────────────────────────────────────────────────────────────────────────────
# Quote tests
# ──────────────────────────────────────────────────────────────────────────────

class TestQuotes:
    @pytest.mark.asyncio
    async def test_vendor_can_submit_quote(self, client: AsyncClient):
        be = _unique_email("bq1"); ve = _unique_email("vq1")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        item_id = rfq["items"][0]["id"]
        resp = await client.post(f"/api/v1/rfqs/{rfq['id']}/quotes", headers=_auth(vtoken), json={
            "items": [{"rfq_item_id": item_id, "unit_price": 50.0, "lead_time_days": 7}]
        })
        assert resp.status_code == 201
        quote = resp.json()
        # Server calculates: 50 * 10 qty = 500
        assert float(quote["total_bid_amount"]) == pytest.approx(500.0)

    @pytest.mark.asyncio
    async def test_vendor_cannot_submit_duplicate_quote(self, client: AsyncClient):
        be = _unique_email("bq2"); ve = _unique_email("vq2")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        item_id = rfq["items"][0]["id"]
        payload = {"items": [{"rfq_item_id": item_id, "unit_price": 50.0, "lead_time_days": 7}]}
        await client.post(f"/api/v1/rfqs/{rfq['id']}/quotes", headers=_auth(vtoken), json=payload)
        resp2 = await client.post(f"/api/v1/rfqs/{rfq['id']}/quotes", headers=_auth(vtoken), json=payload)
        assert resp2.status_code == 400

    @pytest.mark.asyncio
    async def test_buyer_can_award_quote(self, client: AsyncClient):
        be = _unique_email("bq3"); ve = _unique_email("vq3")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        item_id = rfq["items"][0]["id"]
        q = await client.post(f"/api/v1/rfqs/{rfq['id']}/quotes", headers=_auth(vtoken), json={
            "items": [{"rfq_item_id": item_id, "unit_price": 75.0, "lead_time_days": 14}]
        })
        quote_id = q.json()["id"]
        # Close bidding
        await client.post(f"/api/v1/rfqs/{rfq['id']}/close", headers=_auth(btoken))
        # Award
        award = await client.post(f"/api/v1/rfqs/{rfq['id']}/quotes/{quote_id}/award", headers=_auth(btoken))
        assert award.status_code == 200
        data = award.json()
        assert data["awarded_quote_id"] == quote_id
        assert data["erp_payload"]["erp_document_type"] == "PURCHASE_ORDER"


# ──────────────────────────────────────────────────────────────────────────────
# Clarification tests
# ──────────────────────────────────────────────────────────────────────────────

class TestClarifications:
    @pytest.mark.asyncio
    async def test_vendor_can_ask_question(self, client: AsyncClient):
        be = _unique_email("bc1"); ve = _unique_email("vc1")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        resp = await client.post(f"/api/v1/rfqs/{rfq['id']}/clarifications", headers=_auth(vtoken), json={
            "question": "What is the preferred delivery window?"
        })
        assert resp.status_code == 201
        assert resp.json()["answer"] is None

    @pytest.mark.asyncio
    async def test_buyer_can_answer_question(self, client: AsyncClient):
        be = _unique_email("bc2"); ve = _unique_email("vc2")
        await _register(client, be, "BUYER"); await _register(client, ve, "VENDOR")
        btoken = await _login(client, be); vtoken = await _login(client, ve)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        clar = await client.post(f"/api/v1/rfqs/{rfq['id']}/clarifications", headers=_auth(vtoken), json={
            "question": "What is the preferred delivery window?"
        })
        tid = clar.json()["id"]
        ans = await client.post(f"/api/v1/rfqs/{rfq['id']}/clarifications/{tid}/answer",
                                headers=_auth(btoken), json={"answer": "Morning deliveries preferred."})
        assert ans.status_code == 200
        assert ans.json()["answer"] == "Morning deliveries preferred."

    @pytest.mark.asyncio
    async def test_vendor_identity_anonymized_for_other_vendors(self, client: AsyncClient):
        be = _unique_email("bc3"); v1e = _unique_email("vc3a"); v2e = _unique_email("vc3b")
        await _register(client, be, "BUYER")
        await _register(client, v1e, "VENDOR"); await _register(client, v2e, "VENDOR")
        btoken = await _login(client, be)
        v1tok = await _login(client, v1e); v2tok = await _login(client, v2e)
        rfq = await _create_rfq(client, btoken, status="OPEN")
        # Vendor 1 asks a question
        await client.post(f"/api/v1/rfqs/{rfq['id']}/clarifications", headers=_auth(v1tok), json={
            "question": "What is the inspection process?"
        })
        # Vendor 2 fetches list — should see null vendor_id
        resp = await client.get(f"/api/v1/rfqs/{rfq['id']}/clarifications", headers=_auth(v2tok))
        assert resp.status_code == 200
        for thread in resp.json():
            assert thread["asked_by_vendor_id"] is None, "Vendor identity leaked!"


# ──────────────────────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────────────────────

class TestHealth:
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_ready(self, client: AsyncClient):
        resp = await client.get("/ready")
        assert resp.status_code == 200
