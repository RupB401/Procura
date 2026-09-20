# Procura — Enterprise RFQ & Procurement Management Platform

> A production-grade, full-stack procurement platform built with **FastAPI**, **React**, **PostgreSQL**, and **Redis**, fully containerised with Docker Compose.

---

## 📋 Project Overview

Procura enables enterprise procurement workflows through a structured **Request for Quotation (RFQ)** process:

- **Buyers** create RFQs, publish them to the marketplace, evaluate vendor bids, and award contracts.
- **Vendors** discover open RFQs, submit competitive quotes, and engage in anonymised Q&A threads.
- On award, the system generates a structured **ERP-compatible Purchase Order payload**.
- All state changes are written to an immutable **Audit Log**.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                                                          │
│   ┌──────────────┐        ┌──────────────────────────┐  │
│   │   Frontend   │        │        Backend           │  │
│   │  React/Vite  │──────▶│  FastAPI + SQLAlchemy     │  │
│   │  Port: 3000  │  HTTP  │  Port: 8000 (int)        │  │
│   └──────────────┘        │  Port: 8001 (host)       │  │
│                           └──────────┬───────────────┘  │
│                                      │                  │
│                    ┌─────────────────┴──────────────┐   │
│                    │                                │   │
│             ┌──────▼──────┐              ┌──────────▼─┐ │
│             │  PostgreSQL  │              │   Redis    │ │
│             │  Port: 5432  │              │ Port: 6379 │ │
│             └─────────────┘              └────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Backend Layer Architecture:**
```
app/
├── api/v1/         → Route handlers (controllers)
├── schemas/        → Pydantic validation models (request/response)
├── models/domain   → SQLAlchemy ORM models (database tables)
├── services/       → Reusable business logic (audit logger)
├── integrations/   → External system connectors (ERP transformer)
├── middleware/     → Redis rate limiter
└── core/           → Config, security (JWT/bcrypt), error types
```

---

## 📦 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x (with Docker Compose v2)
- Git

No local Python or Node.js installation required — everything runs inside containers.

---

## ⚙️ Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RupB401/Procura.git
   cd Procura
   ```

2. **Create the environment file:**
   ```bash
   cp .env.example .env
   ```
   The defaults work out of the box for local development. Edit `.env` to change secrets for production.

---

## 🚀 How to Start with Docker Compose

```bash
docker compose up --build
```

This single command will:
1. Build the backend and frontend images
2. Start PostgreSQL and Redis
3. Wait for health checks to pass
4. Start the FastAPI backend (with hot-reload)
5. Start the Vite React frontend (with HMR)

| Service  | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8001 |
| API Docs (Swagger) | http://localhost:8001/api/v1/docs |
| API Docs (ReDoc) | http://localhost:8001/api/v1/redoc |

---

## 🗄 How to Run Migrations

Migrations are run **inside the backend container** using Alembic:

```bash
# Apply all pending migrations (run this after first `docker compose up`)
docker compose exec backend alembic upgrade head

# Check current migration status
docker compose exec backend alembic current

# Generate a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "describe your change"
```

---

## 🌱 How to Seed Demo Data

After migrations are applied, seed the database with demo accounts and a sample RFQ:

```bash
docker compose exec backend python seed.py
```

---

## 🔐 Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Buyer** | `buyer@procura.demo` | `DemoPass1234!` |
| **Vendor** | `vendor@procura.demo` | `DemoPass1234!` |

---

## 📖 API Documentation URL

Interactive Swagger UI: **http://localhost:8001/api/v1/docs**

All endpoints are documented with request/response schemas, authentication requirements, and example values.

---

## 🧪 Test Commands

**Health check:**
```bash
curl http://localhost:8001/health
# → {"status":"ok"}

curl http://localhost:8001/ready
# → {"status":"ready"}
```

**Full end-to-end flow (via curl):**
```bash
# 1. Login as buyer
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"buyer@procura.demo","password":"DemoPass1234!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. List RFQs
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/v1/rfqs

# 3. Login as vendor and submit quote
VENDOR_TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"vendor@procura.demo","password":"DemoPass1234!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $VENDOR_TOKEN" http://localhost:8001/api/v1/rfqs
```

---

## 🗂 Project Structure

```
Procura/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers: auth, rfqs, quotes, clarifications
│   │   ├── core/            # Config, JWT security, error types
│   │   ├── db/              # Async engine, session factory
│   │   ├── integrations/    # ERP payload transformer
│   │   ├── middleware/       # Redis sliding-window rate limiter
│   │   ├── models/          # SQLAlchemy domain models
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Audit logger
│   ├── alembic/             # Database migrations
│   ├── seed.py              # Demo data seed script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/layout/ # Navbar, Sidebar, AuthLayout
│   │   ├── contexts/          # AuthContext (JWT lifecycle)
│   │   ├── lib/               # API client, TypeScript types
│   │   └── pages/             # LoginPage, RFQListPage, CreateRFQPage, RFQDetailPage
│   └── package.json
├── docker-compose.yml
├── .env.example
├── MASTER_PROMPT.md         # Authoritative product spec
├── PROGRESS.md              # Phase-by-phase completion tracker
├── STUDY_NOTES.md           # Tech stack documentation & formulas
└── README.md
```

---

## 🏛 Important Architectural Decisions

| Decision | Rationale |
|---|---|
| **Async SQLAlchemy + asyncpg** | Non-blocking DB I/O; prevents thread starvation under load |
| **Pydantic v2 schemas separate from ORM models** | Clean separation of transport/persistence layers; explicit validation at API boundary |
| **Redis Sorted-Set sliding-window rate limiter** | Atomically accurate; survives across multiple backend workers |
| **`SELECT FOR UPDATE` on quote award** | Pessimistic row-lock prevents double-award race conditions |
| **Server-calculated `total_bid_amount`** | Never trust client-submitted totals; recalculated from DB quantities |
| **JWT stored in `localStorage`** | Simplicity for demo; production would use `httpOnly` cookies |
| **Vendor identity anonymisation in clarifications** | MASTER_PROMPT requirement; done server-side in the query response transform |
| **State-machine enforced at API layer** | Invalid transitions rejected with HTTP 409 before any DB write |
| **ERP Transformer as integration layer** | Separates internal data model from external system contracts |

---

## ⚠️ Known Assignment Limitations

1. **No `httpOnly` cookie auth** — JWT is stored in `localStorage` for simplicity. Production deployments should use `httpOnly` secure cookies.
2. **No pagination** — List endpoints return all results. Production would add `skip`/`limit` query parameters.
3. **No file attachments** — RFQ items support text descriptions only; no PDF/document upload.
4. **No email notifications** — State changes do not trigger email alerts to stakeholders.
5. **No test suite** — Automated unit/integration tests were scoped out; the `/health` endpoint and manual Swagger UI serve as verification.
6. **Frontend uses `localStorage`** — Tokens survive browser restarts but are accessible to JavaScript (XSS risk in production).
7. **Migrations not auto-run on startup** — Must be run manually with `docker compose exec backend alembic upgrade head`.
