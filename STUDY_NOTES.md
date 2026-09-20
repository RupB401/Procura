# Procura: RFQ & Procurement Management Platform - Study Notes

## 1. Technology Stack & Rationale

### Backend (Python ecosystem)
*   **FastAPI:** Chosen for its extremely high performance (built on Starlette), native async support, and automatic OpenAPI (Swagger) documentation generation via Pydantic.
*   **Pydantic:** Used for data validation and schema definitions. It tightly integrates with FastAPI to ensure payloads strictly match the API contract.
*   **SQLAlchemy (Async) & asyncpg:** The standard ORM for Python. We use the async engine to avoid blocking the event loop on database I/O, ensuring high concurrency. `asyncpg` is the fastest PostgreSQL driver for Python.
*   **Alembic:** The de-facto database migration tool for SQLAlchemy. Used to track schema changes and generate deterministic migration scripts.
*   **PostgreSQL:** Chosen as the primary relational database because of its robust ACID compliance, JSONB support (used for audit logs), and enterprise-grade reliability.
*   **Redis:** Used as an in-memory data store for the distributed rate limiter. It provides atomic operations (`ZADD`, `ZREMRANGEBYSCORE`) necessary to implement precise sliding-window rate limiting.

### Frontend (JavaScript/TypeScript ecosystem)
*   **React & Vite:** React is chosen for component-based UI development. Vite is the build tool, chosen over Create React App (CRA) or Webpack for its near-instant cold server start and blazing-fast Hot Module Replacement (HMR).
*   **Tailwind CSS:** A utility-first CSS framework. Chosen for rapid UI development and implementing the specific **glassmorphic design system** requested. It allows styling without context switching between JS and CSS files.

### Infrastructure
*   **Docker & Docker Compose:** Used to containerize the application ensuring the "works on my machine" guarantee. It spins up the backend, frontend, PostgreSQL, and Redis in an isolated, networked environment.

---

## 2. Architecture: What We Did Where

The backend follows a domain-driven, layered architecture:

*   **`app/main.py`:** The FastAPI application entry point. This is where we wire up CORS middleware, the Redis Rate Limiter, exception handlers, and include all API routers.
*   **`app/core/`:** Contains application-wide configurations (`config.py` loading `.env`), JWT security and password hashing (`security.py`), and standard API error definitions (`errors.py`).
*   **`app/db/`:** Database connection setup (`session.py`) and the declarative base (`base.py`).
*   **`app/models/`:** The SQLAlchemy ORM models (`domain.py`) representing the physical database tables (Users, RFQs, Quotes, Clarifications, AuditLogs).
*   **`app/schemas/`:** Pydantic models. These define the exact JSON structure expected in HTTP requests and responses. They enforce validation before the data ever reaches the business logic.
*   **`app/api/v1/`:** The API routers (Controllers). This is where the core business logic resides:
    *   `auth.py`: Registration and JWT login.
    *   `rfqs.py`: RFQ creation, listing, and state transitions (Draft -> Open -> Closed).
    *   `quotes.py`: Quote submission and the Awarding logic.
    *   `clarifications.py`: Q&A threads with identity anonymization.
*   **`app/services/`:** Reusable business services. Currently holds `audit.py` which writes immutable records for every state change.
*   **`app/integrations/`:** Contains `erp_transformer.py` which converts awarded quotes into a structured JSON payload for external ERP consumption.

---

## 3. Core Business Logic & Algorithms

### A. The State Machine
The system relies on strict state transitions enforced at the API level:
*   **RFQ Statuses:** `DRAFT` $\rightarrow$ `OPEN` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `AWARDED`
*   **Quote Statuses:** `SUBMITTED` $\rightarrow$ (`AWARDED` | `REJECTED`)

### B. Concurrency & Row Locking (Pessimistic Locking)
When a buyer awards a quote, we must ensure no other buyer awards a different quote at the exact same millisecond. 
We use **`SELECT ... FOR UPDATE`** in SQLAlchemy (`.with_for_update()`). This tells PostgreSQL to physically lock the RFQ row. Any concurrent request trying to award a quote for the same RFQ will be forced to wait until the first transaction commits or rolls back.

### C. Data Anonymization
In the Clarification Q&A threads, when a Vendor fetches the list of questions, the backend conditionally scrubs the `asked_by_vendor_id`. If the ID matches the requesting vendor, it is kept; otherwise, it is set to `null` to prevent vendors from knowing who else is bidding.

---

## 4. Numerical Formulas Used

### 1. Quote Total Bid Amount Calculation
Client-submitted totals are explicitly untrusted. The backend recalculates the total bid amount during quote submission to prevent manipulation.

$$Total\_Bid\_Amount = \sum_{i=1}^{n} (Unit\_Price_i \times Required\_Quantity_i)$$

Where $n$ is the total number of line items in the RFQ. The $Required\_Quantity$ is fetched directly from the database's RFQ Items, not from the vendor's payload.

### 2. Line Item Total (For ERP Payload)
When generating the Purchase Order for the ERP system, the line-item total is calculated as:

$$Line\_Total = Unit\_Price \times Required\_Quantity$$

### 3. Distributed Sliding-Window Rate Limiter
The Redis middleware uses a sliding log algorithm via Redis Sorted Sets (`ZSET`).

1.  **Window Start:** $T_{start} = T_{current} - 60 \text{ seconds}$
2.  **Prune Old Requests:** Remove all entries in the sorted set with a score $< T_{start}$.
3.  **Count Current Requests:** $N = \text{Count of remaining items in the set}$
4.  **Evaluate:**
    $$If \ N \ge Limit_{max}: \text{Block Request (HTTP 429)}$$
    $$If \ N < Limit_{max}: \text{Allow Request and add } T_{current} \text{ to set}$$

The maximum limits are dynamically applied based on the route (e.g., Auth is strictly limited to 10 req/min, while generic routes allow 60 req/min).

---

## 5. Phase 5: Frontend Foundation

We initialized the frontend application using React, Vite, and TypeScript.
*   **Vite Configuration:** Set up to run on host `0.0.0.0` inside Docker, providing ultra-fast HMR during development.
*   **Tailwind CSS:** Configured strictly to support `class`-based Dark Mode.
*   **Design System:** We built custom utility classes in `index.css` (`.glass`, `.glass-card`) using `backdrop-blur-md` and `bg-white/70` to strictly enforce the requested **Glassmorphic** aesthetics.
*   **Layout Components:** Created reusable `Navbar`, `Sidebar`, and `AuthLayout` components. They dynamically react to user roles (`BUYER` vs `VENDOR`) and handle the Dark Mode toggle logic by mutating the DOM `classList`.

---

## 6. Phase 6: Frontend Application Logic

### Architecture Pattern: Client-Side State Machine Router
Instead of a full routing library (React Router), we use a simple discriminated union type `AppPage` in `App.tsx` to perform conditional rendering. This keeps the bundle minimal and the logic transparent.

```
type AppPage =
  | { name: 'rfq-list' }
  | { name: 'rfq-create' }
  | { name: 'rfq-detail'; id: string }
```

### Components Built

| File | Role |
|---|---|
| `lib/api.ts` | Fetch wrapper that injects `Authorization: Bearer <token>` and JSON-parses errors |
| `lib/types.ts` | TypeScript interfaces mirroring the backend Pydantic schemas |
| `contexts/AuthContext.tsx` | React Context providing `login`, `register`, `logout`, and `user` state; persists JWT in `localStorage` |
| `pages/LoginPage.tsx` | Glassmorphic auth form with tab-switch between Sign In / Register and role selector |
| `pages/RFQListPage.tsx` | Role-aware RFQ list; Buyer sees own RFQs, Vendor sees OPEN/UNDER_REVIEW; status badges |
| `pages/CreateRFQPage.tsx` | Dynamic multi-item RFQ creation form with quantity/UOM inputs |
| `pages/RFQDetailPage.tsx` | Full detail view: state transition actions, vendor quote submission, buyer quote comparison with award button, clarification Q&A panel |

### Security Pattern: Auth Guard
`AppShell` checks `isLoading` then `user`. If `user` is `null`, it renders `<LoginPage>` — effectively a client-side auth guard without a router.

### Token Flow
1. User submits login form → backend returns `{ access_token: "..." }`
2. Token stored in `localStorage`
3. `api.ts` reads it on every request and injects `Authorization` header
4. On page reload, `AuthContext` calls `GET /auth/me` to re-validate the token
5. If invalid (expired/tampered), token is cleared and user is logged out

---

## 7. Phase 7: Verification & Handoff

### Dependency Gotcha: passlib + bcrypt Version Incompatibility
`passlib==1.7.4` (released in 2020) uses internal bcrypt API `bcrypt.__about__.__version__` which was removed in `bcrypt>=4.1`. Solution: pin `bcrypt==4.0.1` in `requirements.txt`.

### Seed Script Architecture
The seed script (`backend/seed.py`) uses the same async SQLAlchemy session as the application. Key pattern:
```python
async with AsyncSessionLocal() as db:
    ...
    await db.commit()
```
It is idempotent — re-running it will detect existing records and skip creation (no duplicates).

### Smoke Test Results (Stage 29 Definition of Done)

| Test | Result |
|---|---|
| `/health` returns HTTP 200 | ✅ PASS |
| `/ready` returns HTTP 200 | ✅ PASS |
| Buyer login works | ✅ PASS |
| Vendor login works | ✅ PASS |
| Role-based access control (RBAC) | ✅ PASS |
| Buyer can create an RFQ (DRAFT) | ✅ PASS |
| Buyer can publish RFQ (DRAFT→OPEN) | ✅ PASS |
| Vendor can discover OPEN RFQ | ✅ PASS |
| Vendor can submit a quote | ✅ PASS |
| Buyer can close bidding (OPEN→UNDER_REVIEW) | ✅ PASS |
| Buyer can award a quote | ✅ PASS |
| ERP purchase order payload generated on award | ✅ PASS |
| Vendor correctly blocked from creating RFQ (HTTP 401) | ✅ PASS |

**All 13 smoke tests passed.**

### Phase 8 & 9 (Testing & Cleanup)
- **E2E Testing:** Due to asyncpg connection pooling issues with pytest-asyncio, the integration test suite was written to hit the live running Uvicorn server in a separate container using an httpx.AsyncClient (blackbox testing approach). This tests the real DB pool and real middleware stack.
- **Security Cleanup:** Verified that bcrypt==4.0.1 provides passlib compat without issues and no sensitive hardcoded strings exist beyond dev defaults.
