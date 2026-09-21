# Procura — Enterprise RFQ & Procurement Management Platform

> A production-grade, full-stack procurement platform built with **FastAPI**, **React**, **PostgreSQL**, and **Redis**, fully containerised with Docker Compose.

Procura is a B2B platform designed to streamline the Request for Quotation (RFQ) process. It enables Buyers to create and manage RFQs and Vendors to submit, review, and track quotations.

## Live Application URL
The application is configured for deployment on Render.com via the provided `render.yaml` file.
(Replace with live URL after deploying).

## Live Application URL
The application is configured for deployment on Render.com via the provided `render.yaml` file.
(Replace with live URL after deploying).

## Technology Stack
- **Frontend**: React 18, Vite, Tailwind CSS, TypeScript, React Router DOM, @react-oauth/google
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (Async), Uvicorn, Pydantic
- **Database**: PostgreSQL 15 (Relational Data), Redis 7 (Rate Limiting & Caching)
- **Deployment**: Docker, Docker Compose, Render IaC (`render.yaml`)

## Architecture Explanation
- **Client-Server Separation**: The frontend is a single-page application (SPA) built with React that communicates with the backend via RESTful APIs.
- **Async Backend**: FastAPI leverages asynchronous Python to handle high concurrency efficiently. Database operations use `asyncpg`.
- **Database Migrations**: Alembic is used for version control of the database schema (e.g. cascading deletes, new columns).
- **Authentication**: JWT-based authentication for securing endpoints, with middleware validating user roles (`BUYER` vs `VENDOR`) and an optional Google OAuth implementation.
- **State Machine**: RFQ status transitions (DRAFT -> OPEN -> UNDER_REVIEW -> AWARDED) are strictly enforced in the backend routers.
- **Concurrency Control**: "Awarding" a quote utilizes a pessimistic row-level lock (`SELECT FOR UPDATE`) to prevent race conditions when multiple buyers attempt to award simultaneously.

## Features Implemented
- **User Roles**: Buyer and Vendor roles with secure JWT login and registration.
- **Buyer Features**: Create RFQs with line items, description, and delivery location. Close bidding, view quotes, and award contracts.
- **Supplier Features**: Browse active RFQs, search/filter by title/location/status, ask clarification questions, and submit itemized quotations (price, lead time, notes).
- **Interactive UI**: Responsive Tailwind design with glassmorphism elements, loading states, and error boundary handling.

## Assumptions & Limitations
- **Email Delivery**: Actual email sending (e.g., SendGrid) for RFQ notifications is mocked/bypassed in this assignment scope.
- **OAuth Setup**: A dummy Google Client ID is used for showcase purposes. In a real environment, the `VITE_GOOGLE_CLIENT_ID` environment variable must be provided.
- **Mock Data**: A seed script (`backend/seed.py`) is provided to quickly populate the database with dummy users and RFQs for demonstration.

## Setup Instructions (Local Development)

### Prerequisites
- Docker and Docker Compose installed.
- (Optional) Python 3.11+ and Node 20+ if running outside Docker.

### Running with Docker Compose
1. Clone the repository.
2. Run the application:
   ```bash
   docker-compose up --build -d
   ```
3. Initialize dummy data for testing:
   ```bash
   docker exec rfq_fastapi_backend python seed.py
   ```

### Test Accounts (from seed data)
- **Buyer**: `buyer@test.com` / `TestPass123!`
- **Vendor 1**: `vendor1@test.com` / `TestPass123!`
- **Vendor 2**: `vendor2@test.com` / `TestPass123!`

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
