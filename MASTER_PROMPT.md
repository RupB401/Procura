# Enterprise RFQ Application - Complete Master Blueprint & Prompt

## System Overview & Architecture

You are tasked with building a production-ready, enterprise-grade
**Request for Quotation (RFQ) Application**. The system requires high
reliability, scalability, defensive rate-limiting, and an exceptionally
polished, minimalist user interface.

### Tech Stack Constraints

-   **Backend:** FastAPI (Python 3.11+, asynchronous pattern with
    `asyncpg` and `SQLAlchemy`).
-   **Frontend:** React (TypeScript, Vite, Tailwind CSS).
-   **Primary Database:** PostgreSQL 15 (relational, transactional
    safety).
-   **Caching & Rate Limiting:** Redis 7 (high-performance in-memory
    key-value store).
-   **Containerization:** Docker & Docker Compose.

------------------------------------------------------------------------

## Stage 1: Infrastructure & Container Setup

Create a `docker-compose.yml` file at the root of the project to
orchestrate the services with secure isolated networking and strict
initialization sequencing.

``` yaml
version: '3.8'

networks:
  rfq_network:
    driver: bridge

services:
  db:
    image: postgres:15-alpine
    container_name: rfq_postgres_db
    environment:
      POSTGRES_USER: rfq_admin
      POSTGRES_PASSWORD: secure_rfq_password_2026
      POSTGRES_DB: rfq_enterprise_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - rfq_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rfq_admin -d rfq_enterprise_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: rfq_redis_cache
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    networks:
      - rfq_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rfq_fastapi_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://rfq_admin:secure_rfq_password_2026@db:5432/rfq_enterprise_db
      - REDIS_URL=redis://redis:6379/0
    networks:
      - rfq_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: rfq_react_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    networks:
      - rfq_network
    depends_on:
      - backend

volumes:
  pgdata:
  redisdata:
```

------------------------------------------------------------------------

## Stage 2: Dependency Specification & Base Configuration

Configure project manifests to lock versions down and establish base
execution rules.

### 2.1 Backend Environment Setup (`backend/requirements.txt`)

``` text
fastapi==0.110.0
uvicorn==0.28.0
sqlalchemy==2.0.28
asyncpg==0.29.0
redis==5.0.3
pydantic==2.6.4
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
```

### 2.2 Frontend Node Manifest (`frontend/package.json`)

``` json
{
  "name": "rfq-enterprise-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 3000",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.359.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.2.2",
    "vite": "^5.1.6"
  }
}
```

### 2.3 Tailwind CSS Theme Configuration (`frontend/tailwind.config.js`)

``` javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      spacing: {
        '2xs': '4px',
        'xs': '8px',
        'sm': '12px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        brand: {
          bg: '#FFFFFF',
          surface: '#F8F9FA',
          border: '#E9ECEF',
          text: '#212529',
          muted: '#6C757D',
          accent: '#0052CC', // Single subtle corporate color variable
        }
      }
    },
  },
  plugins: [],
}
```

------------------------------------------------------------------------

## Stage 3: Database Schema & Relational Modeling

Implement this relational PostgreSQL layout natively via SQLAlchemy
models. The schema uses explicit precision scales, indexes, and full
relational safety mechanisms.

``` sql
-- Enums for status integrity
CREATE TYPE rfq_status AS ENUM ('DRAFT', 'OPEN', 'UNDER_REVIEW', 'AWARDED', 'CANCELLED');
CREATE TYPE quote_status AS ENUM ('SUBMITTED', 'REJECTED', 'AWARDED');

-- Users / Business Entities
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'BUYER' or 'VENDOR'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Master RFQ Document
CREATE TABLE rfqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status rfq_status DEFAULT 'DRAFT' NOT NULL,
    submission_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Individual line items inside an RFQ
CREATE TABLE rfq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs(id) ON DELETE CASCADE,
    item_code VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    required_quantity NUMERIC(12, 2) NOT NULL,
    unit_of_measure VARCHAR(25) NOT NULL
);

-- Vendor Bids / Quotations
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    status quote_status DEFAULT 'SUBMITTED' NOT NULL,
    total_bid_amount NUMERIC(15, 2) NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Vendor Itemized Bid Specifics
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    rfq_item_id UUID REFERENCES rfq_items(id) ON DELETE RESTRICT,
    unit_price NUMERIC(12, 2) NOT NULL,
    lead_time_days INT NOT NULL,
    min_order_quantity NUMERIC(12, 2) DEFAULT 0.00,
    notes TEXT
);

-- Anonymous Clarification Thread Board
CREATE TABLE clarification_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id UUID REFERENCES rfqs(id) ON DELETE CASCADE,
    asked_by_vendor_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Hidden visually to buyers
    question TEXT NOT NULL,
    answer TEXT,
    is_broadcast BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    answered_at TIMESTAMP WITH TIME ZONE
);

-- High-Compliance Audit Logs Table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    delta_changes JSONB NOT NULL, -- Holds structural before/after differences
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization Indexes
CREATE INDEX idx_rfqs_status ON rfqs(status);
CREATE INDEX idx_quotes_rfq ON quotes(rfq_id);
CREATE INDEX idx_quote_items_rfq_item ON quote_items(rfq_item_id);
CREATE INDEX idx_audit_target ON audit_logs(target_table, target_id);
```

------------------------------------------------------------------------

## Stage 4: Backend Implementation Blueprint

### 4.1 Redis Distributed Rate-Limiter Middleware

Construct an async application middleware layer inside FastAPI
implementing an atomic Redis-backed sliding-window rate limiter.

Requirements: - The algorithm MUST be a sliding-window counter, not a
token bucket. - The decision to accept/reject and increment the request
count MUST be atomic. Prefer a Redis Lua script or an equivalent atomic
Redis operation. - Unauthenticated requests are identified by source
IP. - Authenticated requests are identified by authenticated user ID
plus source IP. - Return HTTP 429 with a `Retry-After` header when the
limit is exceeded. - Rate-limit configuration MUST be
environment-driven. - Authentication endpoints MUST have stricter limits
than ordinary API endpoints. - Health/readiness endpoints must not be
blocked by the general API limiter. - Do not trust arbitrary
client-supplied forwarding headers unless a trusted reverse-proxy
configuration explicitly enables them.

``` python
import time
from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, redis_url: str, rate_limit_per_minute: int = 60):
        super().__init__(app)
        self.redis = aioredis.from_url(redis_url)
        self.rate_limit = rate_limit_per_minute

    async def dispatch(self, request: Request, call_next):
        # Identify clients by IP address or User ID
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        current_time = time.time()
        window_start = current_time - 60
        
        async with self.redis.pipeline(transaction=True) as pipe:
            # Multi-exec transaction context block
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(current_time): current_time})
            await pipe.expire(key, 60)
            _, request_count, _, _ = await pipe.execute()
            
        if request_count > self.rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. System limits structured to 60 requests per minute max."
            )
            
        return await call_next(request)
```

### 4.2 Cache-Aside Pattern Implementation Example

Use Redis caching for read operations (`GET` routes) on long-lived
calculations, such as the total bids metadata payload, clear the cache
anytime a mutate/write payload (`POST`/`PUT`/`DELETE`) hits that entity.

### 4.3 Anti-Collusion Multi-Vendor Clarification Logic

-   Any vendor can post a question to `clarification_threads`.
-   The backend API layer must enforce structural scrubbing: when a
    `BUYER` pulls the thread list, the endpoint response explicitly
    leaves out the `asked_by_vendor_id` key entirely.
-   Once the buyer submits an update payload typing into the `answer`
    text-field, the system shifts `is_broadcast` flag to True, allowing
    all vendor profile tokens to pull down the newly clear instructions.

### 4.4 Downstream ERP Payloads Hand-off Factory

Generate an automated transformer tool mapping fields out of the
databases into an external structural payload once an RFQ changes status
to `AWARDED`. Financial values MUST remain `Decimal` throughout the
backend and integration layer; never convert monetary values to Python
`float`:

``` python
def transform_rfq_to_purchase_order(rfq_data, awarded_quote_data) -> dict:
    return {
        "erp_integration_id": f"PO-{rfq_data['id'][:8].upper()}",
        "vendor_tax_identifier": awarded_quote_data["vendor_company_tax_id"],
        "financial_total_allocation": float(awarded_quote_data["total_bid_amount"]),
        "line_items": [
            {
                "sku_reference": item["item_code"],
                "purchase_quantity": float(item["required_quantity"]),
                "cleared_unit_cost": float(item["negotiated_price"])
            } for item in awarded_quote_data["items"]
        ]
    }
```

------------------------------------------------------------------------

## Stage 5: Frontend Design System & Component Library

Follow these precise styling parameters to build your UI components: \*
**Grid:** Strict 8pt grid alignment for sizing and padding (`space-y-2`,
`p-4`, `p-8`). \* **Aesthetics:** Minimalist and enterprise-grade. No
heavy shadows, gradients, or neobrutalism. \* **Palette:** Pure
monochrome (`#FFFFFF`, `#F8F9FA`, `#E9ECEF`, `#212529`) with a single
accent color (`#0052CC`) used sparingly for active states or primary
call-to-actions.

### 5.1 Monochromatic Main Layout Blueprint (`frontend/src/components/Layout.tsx`)

``` tsx
import React from 'react';
import { Shield, FileText, BarChart3, HelpCircle } from 'lucide-react';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans antialiased flex flex-col">
      {/* Top Main Navigation Header */}
      <header className="h-16 border-b border-gray-200/50 px-6 flex items-center justify-between bg-white/70 backdrop-blur-md z-10 sticky top-0">
        <div className="flex items-center space-x-6">
          <span className="font-mono font-bold tracking-tight text-sm uppercase flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#0052CC]" /> Core_Sourcing // Enterprise
          </span>
          <nav className="hidden md:flex space-x-4">
            <a href="#" className="text-xs uppercase font-medium text-gray-900 border-b-2 border-[#0052CC] px-1 py-5 flex items-center gap-1.5"><FileText className="w-3.5 h-3.5"/> RFQs</a>
            <a href="#" className="text-xs uppercase font-medium text-gray-500 hover:text-gray-900 px-1 py-5 flex items-center gap-1.5"><BarChart3 className="w-3.5 h-3.5"/> Analysis</a>
            <a href="#" className="text-xs uppercase font-medium text-gray-500 hover:text-gray-900 px-1 py-5 flex items-center gap-1.5"><HelpCircle className="w-3.5 h-3.5"/> Clarifications</a>
          </nav>
        </div>
        <div className="flex items-center space-x-3 text-right">
          <div className="text-xs font-mono">
            <span className="block text-gray-900 font-medium">Procurement_Ops</span>
            <span className="block text-gray-400 text-[10px]">Buyer Account</span>
          </div>
        </div>
      </header>

      {/* Main Container Viewport */}
      <main className="flex-1 bg-[#F8F9FA] p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {children}
        </div>
      </main>
    </div>
  );
};
```

### 5.2 Side-by-Side Line-Item Evaluation Grid (`frontend/src/components/NormalizationGrid.tsx`)

``` tsx
import React from 'react';

interface MatrixColumn {
  vendorName: string;
  unitPrice: number;
  leadTime: number;
  moq: number;
}

interface MatrixRow {
  itemCode: string;
  description: string;
  qty: number;
  bids: Record<string, MatrixColumn>;
}

export const NormalizationGrid: React.FC<{ data: MatrixRow[] }> = ({ data }) => {
  return (
    <div className="border border-gray-200 bg-white rounded-none overflow-hidden shadow-none">
      <div className="p-4 border-b border-gray-200 bg-white">
        <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-gray-900">Cross-Vendor Bid Matrix Overview</h3>
        <p className="text-xs text-gray-500 mt-1">Normalized live analysis metric mapping unit pricing scales alongside strict logistics lead thresholds.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-sans text-xs">
          <thead>
            <tr className="bg-[#F8F9FA] border-b border-gray-200">
              <th className="p-3 font-mono font-medium text-gray-500 border-r border-gray-200">Item Details</th>
              <th className="p-3 font-mono font-medium text-gray-500 text-center border-r border-gray-200">Qty</th>
              {/* Dynamic Mapping for Vendors column headers inside dataset */}
              {Object.keys(data?.[0]?.bids || {}).map((vendorKey) => (
                <th key={vendorKey} colSpan={3} className="p-2 font-mono font-medium text-gray-900 text-center border-r border-gray-200 uppercase bg-gray-50 tracking-wide">
                  {vendorKey}
                </th>
              ))}
            </tr>
            <tr className="bg-white border-b border-gray-200 text-[11px] text-gray-500 font-mono">
              <th className="p-2 border-r border-gray-200">Identifier / Specs</th>
              <th className="p-2 text-center border-r border-gray-200">-</th>
              {Object.keys(data?.[0]?.bids || {}).map((vendorKey) => (
                <React.Fragment key={`sub-${vendorKey}`}>
                  <th className="p-2 text-right text-gray-700 bg-white">Unit ($)</th>
                  <th className="p-2 text-center text-gray-600 bg-white">L/T (Days)</th>
                  <th className="p-2 text-right text-gray-600 border-r border-gray-200 bg-white">MOQ</th>
                </React.Fragment>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 font-mono">
            {data.map((row) => (
              <tr key={row.itemCode} className="hover:bg-gray-50 transition-colors duration-150">
                <td className="p-3 border-r border-gray-200 font-medium text-gray-900">
                  <div className="font-bold font-mono">{row.itemCode}</div>
                  <div className="text-xs font-sans text-gray-500 mt-0.5">{row.description}</div>
                </td>
                <td className="p-3 text-center border-r border-gray-200 font-bold text-gray-900 bg-[#F8F9FA]">
                  {row.qty.toLocaleString()}
                </td>
                {Object.entries(row.bids).map(([vendor, bid]) => {
                  // Subtle logic calculation to spot the absolute lowest price variable
                  const prices = Object.values(row.bids).map(b => b.unitPrice);
                  const isLowest = bid.unitPrice === Math.min(...prices);
                  
                  return (
                    <React.Fragment key={`${row.itemCode}-${vendor}`}>
                      <td className={`p-3 text-right border-0 font-bold ${isLowest ? 'text-[#0052CC] bg-blue-50/40' : 'text-gray-900'}`}>
                        {bid.unitPrice.toFixed(2)}
                      </td>
                      <td className="p-3 text-center text-gray-600 border-0">{bid.leadTime}</td>
                      <td className="p-3 text-right text-gray-600 border-r border-gray-200">{bid.moq.toLocaleString()}</td>
                    </React.Fragment>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

------------------------------------------------------------------------

## Instructions for Execution

1.  Parse this entire blueprint prompt.
2.  Generate all missing configurations, including the required
    `Dockerfile` architectures for both the backend and frontend
    services.
3.  Build the backend code with SQLAlchemy asynchronous model references
    matching Stage 3 exactly.
4.  Integrate the Redis rate-limiting and optimization strategies
    outlined in Stage 4.
5.  Create the components using the exact design choices from Stage 5,
    avoiding any excessive decorative elements.

------------------------------------------------------------------------

# Stage 6: Agentic Execution Contract --- NON-NEGOTIABLE

This section converts the blueprint into an executable implementation
specification. Do not invent missing business behavior when a rule is
defined below. Do not omit requirements because an example
implementation above is incomplete. When the earlier sections conflict
with this section, this section takes precedence.

## 6.1 Primary Objective

Build a runnable full-stack RFQ application that can be demonstrated
end-to-end by an interviewer.

The application MUST provide two roles:

-   `BUYER`
-   `VENDOR`

The minimum demonstrable workflow is:

``` text
Buyer registers/logs in
        ↓
Buyer creates RFQ draft
        ↓
Buyer adds RFQ line items
        ↓
Buyer publishes RFQ
        ↓
Vendor logs in
        ↓
Vendor discovers an OPEN RFQ
        ↓
Vendor asks a clarification question (optional)
        ↓
Buyer answers clarification
        ↓
Vendor submits a quotation
        ↓
Buyer opens quotation comparison
        ↓
Buyer reviews normalized vendor bids
        ↓
Buyer awards one quotation
        ↓
System rejects all other submitted quotations
        ↓
RFQ becomes AWARDED
        ↓
ERP purchase-order payload is generated
        ↓
All important state changes are audit logged
```

The system is a technical assignment, not a real production procurement
platform. Do not add unnecessary enterprise infrastructure that prevents
the application from being run locally. Prioritize correctness, clean
architecture, security, and a polished demonstration.

------------------------------------------------------------------------

# Stage 7: Actors, Permissions & Authorization

## 7.1 Roles

### BUYER

Can:

-   create RFQs
-   edit own DRAFT RFQs
-   publish own DRAFT RFQs
-   view own RFQs
-   view quotations belonging to own RFQs
-   answer clarification questions on own RFQs
-   award a quotation on own RFQs
-   cancel own RFQs when the state machine permits it
-   view audit events relevant to their own actions/resources

Cannot:

-   submit vendor quotations
-   modify another buyer's RFQ
-   view vendor identity behind an anonymous clarification question
-   modify submitted vendor quotations

### VENDOR

Can:

-   view OPEN RFQs available to vendors
-   view RFQ details and line items
-   submit one quotation per RFQ
-   view and respond to their own quotation where permitted
-   ask clarification questions
-   view broadcast clarification answers

Cannot:

-   create or publish RFQs
-   view another vendor's quotation
-   view another vendor's identity through clarification APIs
-   award or cancel RFQs
-   modify a quotation after it has been submitted unless an explicit
    future revision workflow is added

## 7.2 Object-Level Authorization

Every resource endpoint MUST perform server-side authorization.

Never rely on hidden frontend buttons for authorization.

Examples:

-   Buyer A cannot access Buyer B's RFQ by changing the UUID in the URL.
-   Vendor A cannot retrieve Vendor B's quote by changing the quote
    UUID.
-   Vendor cannot submit a quote to a non-OPEN RFQ.
-   Buyer cannot award an RFQ they do not own.

All authorization checks MUST happen before returning protected resource
data.

------------------------------------------------------------------------

# Stage 8: Authentication

Implement JWT-based authentication.

Required endpoints:

``` text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

Requirements:

-   Passwords MUST be hashed with bcrypt or an equivalent secure
    password hashing scheme.
-   Never store plaintext passwords.
-   JWT secret MUST come from environment configuration.
-   Access-token expiration MUST be configurable.
-   JWT payload MUST contain user ID and role.
-   Login failures must return a generic authentication error and must
    not disclose whether an email exists.
-   Authentication endpoints must have stricter rate limits.
-   Frontend must persist authentication state safely for this
    assignment and attach the bearer token to API requests.
-   API must return `401` for missing/invalid authentication.
-   API must return `403` for authenticated users lacking permission.

For this assignment, a refresh-token system is optional and should not
be implemented unless needed by the chosen frontend architecture.

------------------------------------------------------------------------

# Stage 9: RFQ State Machine

The following state transitions are the only valid transitions:

``` text
DRAFT
 ├── OPEN
 └── CANCELLED

OPEN
 ├── UNDER_REVIEW
 └── CANCELLED

UNDER_REVIEW
 ├── AWARDED
 └── CANCELLED

AWARDED
 └── terminal

CANCELLED
 └── terminal
```

Rules:

-   Only the owning buyer may transition an RFQ.
-   `DRAFT → OPEN` requires at least one RFQ item.
-   An RFQ cannot be published if its submission deadline is in the
    past.
-   `OPEN → UNDER_REVIEW` is allowed after the submission deadline has
    passed, or through an explicit buyer action after submissions close.
-   `AWARDED` and `CANCELLED` are terminal states.
-   No API may directly assign an arbitrary status supplied by the
    client.
-   State transitions must be validated server-side.
-   Every state transition must create an audit log.

------------------------------------------------------------------------

# Stage 10: Quote State Machine

Valid quote transitions:

``` text
SUBMITTED
 ├── AWARDED
 └── REJECTED

AWARDED
 └── terminal

REJECTED
 └── terminal
```

Rules:

-   A vendor may have at most one active quote per RFQ.
-   A quote may only be submitted while the RFQ is `OPEN` and before the
    submission deadline.
-   A submitted quote cannot be edited.
-   When one quote is awarded:
    -   selected quote becomes `AWARDED`
    -   every other `SUBMITTED` quote for the same RFQ becomes
        `REJECTED`
    -   RFQ becomes `AWARDED`
-   Awarding MUST happen inside one database transaction.
-   The RFQ row MUST be locked during the award operation
    (`SELECT ... FOR UPDATE` or equivalent).
-   The backend MUST re-check RFQ state and quote state inside the
    transaction.
-   Two concurrent award requests MUST NOT produce two awarded quotes.

------------------------------------------------------------------------

# Stage 11: RFQ and Quote Business Rules

## 11.1 RFQ

Required:

-   title
-   description
-   submission deadline
-   at least one line item before publishing

Each line item requires:

-   item code
-   description
-   quantity
-   unit of measure

Validation:

-   quantity must be greater than zero
-   item code must not be empty
-   description must not be empty
-   deadline must be in the future when publishing

## 11.2 Quote

Every quote item MUST correspond to exactly one RFQ item.

A vendor quote MUST contain exactly one quote item for every RFQ item.

Therefore:

``` text
RFQ has N items
Vendor quote must contain N quote items
```

No duplicate `rfq_item_id` values are allowed inside a quote.

Add database uniqueness constraints:

``` text
UNIQUE(rfq_id, vendor_id)
UNIQUE(quote_id, rfq_item_id)
```

The backend calculates the quote total.

The client MUST NOT be trusted for:

-   total bid amount
-   line subtotal
-   award status
-   RFQ status

For each line:

``` text
line_total = required_quantity × unit_price
```

The quote total is:

``` text
total_bid_amount = SUM(all line_total values)
```

Use `Decimal` / PostgreSQL `NUMERIC` for monetary calculations. Never
convert monetary values to `float`.

------------------------------------------------------------------------

# Stage 12: Financial Model

For this assignment, use one currency per RFQ.

Add:

``` text
currency_code CHAR(3) NOT NULL DEFAULT 'USD'
```

to the appropriate financial entity.

Do not implement multi-currency conversion.

The assignment does not require:

-   tax calculation
-   discounts
-   freight
-   payment schedules
-   foreign-exchange conversion

unless explicitly added later.

Keep the financial model simple and internally consistent.

------------------------------------------------------------------------

# Stage 13: Database Requirements

Use SQLAlchemy 2.x async models matching the relational model.

Use Alembic for schema migrations.

Do NOT create production schema solely through application-startup
`create_all()`.

Required constraints:

``` text
users.email UNIQUE
UNIQUE(rfq_id, vendor_id)
UNIQUE(quote_id, rfq_item_id)
```

Add appropriate indexes for:

-   users.email
-   rfqs.buyer_id
-   rfqs.status
-   rfqs.submission_deadline
-   rfq_items.rfq_id
-   quotes.rfq_id
-   quotes.vendor_id
-   quote_items.quote_id
-   quote_items.rfq_item_id
-   clarification_threads.rfq_id
-   audit_logs.target_table + target_id
-   audit_logs.timestamp

Use timezone-aware timestamps everywhere.

Enable UUID generation through PostgreSQL or application-side UUID
generation consistently.

------------------------------------------------------------------------

# Stage 14: Clarification Rules

Clarifications are anonymous between vendors and buyers.

Vendor identity MUST NOT be exposed through buyer-facing clarification
responses.

Vendor identity may remain stored internally as `asked_by_vendor_id` for
authorization and audit purposes.

Rules:

-   Any eligible vendor may ask a clarification question for an OPEN
    RFQ.
-   The buyer who owns the RFQ may answer.
-   The buyer response is broadcast to all eligible vendors.
-   Other vendors can see the question and answer, but not the asking
    vendor's identity.
-   Vendors cannot modify another vendor's question.
-   Questions and answers are audit logged.
-   Do not expose `asked_by_vendor_id` in
    public/vendor-facing/buyer-facing DTOs unless the endpoint
    explicitly requires internal authorization data.
-   Use Pydantic response schemas that whitelist fields instead of
    serializing SQLAlchemy models directly.

------------------------------------------------------------------------

# Stage 15: API Contract

All API routes must use:

``` text
/api/v1/...
```

Required endpoint groups:

``` text
Authentication
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me

RFQs
GET  /api/v1/rfqs
POST /api/v1/rfqs
GET  /api/v1/rfqs/{rfq_id}
PUT  /api/v1/rfqs/{rfq_id}
POST /api/v1/rfqs/{rfq_id}/publish
POST /api/v1/rfqs/{rfq_id}/cancel
POST /api/v1/rfqs/{rfq_id}/review

Quotes
GET  /api/v1/rfqs/{rfq_id}/quotes
POST /api/v1/rfqs/{rfq_id}/quotes
GET  /api/v1/quotes/{quote_id}

Clarifications
GET  /api/v1/rfqs/{rfq_id}/clarifications
POST /api/v1/rfqs/{rfq_id}/clarifications
POST /api/v1/clarifications/{clarification_id}/answer

Award
POST /api/v1/rfqs/{rfq_id}/award

Health
GET /health
GET /ready
```

Every endpoint MUST define:

-   allowed roles
-   authentication requirement
-   request Pydantic schema
-   response Pydantic schema
-   validation rules
-   expected HTTP status codes
-   authorization checks
-   relevant error codes

Use a consistent error structure:

``` json
{
  "error": {
    "code": "RFQ_DEADLINE_PASSED",
    "message": "The RFQ submission deadline has passed.",
    "request_id": "..."
  }
}
```

Use appropriate status codes including:

``` text
400 validation/business error
401 authentication failure
403 authorization failure
404 resource not found
409 state/conflict error
422 request validation error
429 rate limit exceeded
500 unexpected server error
```

Do not expose internal stack traces in API responses.

------------------------------------------------------------------------

# Stage 16: Pagination, Filtering and Sorting

List endpoints MUST support pagination.

At minimum:

``` text
page
page_size
```

RFQ listing should support:

``` text
status
search
sort
```

Use safe server-side sorting. Never interpolate arbitrary
client-provided column names directly into SQL.

Return pagination metadata.

The default page size must be reasonable, such as 20, with a hard
maximum of 100.

------------------------------------------------------------------------

# Stage 17: Redis Requirements

## Rate limiting

Use Redis for distributed rate limiting.

Recommended defaults:

``` text
General API:
60 requests/minute

Authentication:
10 requests/minute

Quote submission:
10 requests/minute

Clarification posting:
20 requests/minute
```

Make these environment-configurable.

## Caching

Cache only safe read-heavy data.

Example:

``` text
rfq:{rfq_id}:summary
rfq:{rfq_id}:clarifications
```

Every cached entry MUST have:

-   explicit TTL
-   deterministic key
-   JSON serialization
-   documented invalidation behavior

Invalidate relevant cache keys after mutations.

Never cache authorization-sensitive data without including the
appropriate user/role identity in the key.

------------------------------------------------------------------------

# Stage 18: Project Structure

Use this structure unless there is a strong technical reason to deviate:

``` text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── errors.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── api/
│   │   └── v1/
│   ├── middleware/
│   └── integrations/
├── alembic/
├── tests/
├── Dockerfile
├── requirements.txt
└── alembic.ini

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── hooks/
│   ├── types/
│   ├── auth/
│   └── App.tsx
├── public/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

Keep business logic out of route handlers.

Use:

``` text
router → service → repository → database
```

where appropriate.

------------------------------------------------------------------------

# Stage 19: Frontend Requirements

Required screens:

### Authentication

-   Login
-   Registration
-   role selection
-   glassmorphic design elements (semi-transparent backgrounds, backdrop blur, subtle borders) for authentication screens

### Buyer

-   Buyer dashboard
-   RFQ list
-   Create RFQ
-   Edit draft RFQ
-   RFQ detail
-   Clarification panel
-   Quote comparison
-   Award confirmation

### Vendor

-   Vendor dashboard
-   Available RFQs
-   RFQ detail
-   Quote submission
-   Clarification panel
-   Submitted quote view

### System

-   loading states
-   empty states
-   validation errors
-   API errors
-   unauthorized state
-   not-found state
-   confirmation dialogs
-   dark mode toggle

The frontend must never decide whether an operation is authorized. It
should only reflect backend authorization results.

------------------------------------------------------------------------



# Stage 19A: Dashboard Analytics & Data Visualization

The application MUST include lightweight data visualizations where they materially improve understanding of procurement data.

Do not create a generic "analytics dashboard" filled with decorative charts. Every visualization must represent real data returned by the backend.

## Buyer Dashboard

Display:

### 1. RFQ Status Distribution

Render a donut/pie chart showing the buyer's RFQs grouped by:

- DRAFT
- OPEN
- UNDER_REVIEW
- AWARDED
- CANCELLED

The chart must use real backend data.

If there are no RFQs, show an appropriate empty state instead of an empty chart.

### 2. RFQ Creation Trend

Render a line chart showing the number of RFQs created over time.

Use an appropriate time aggregation such as:

- weekly for short datasets
- monthly for larger datasets

Do not fabricate historical data.

### 3. Selected RFQ Quote Comparison

On the RFQ detail / quote comparison page, provide a bar chart comparing submitted quote totals.

Example:

Vendor A | ₹120,000  
Vendor B | ₹135,000  
Vendor C | ₹127,500

The chart is informational only.

Do not automatically recommend or select a vendor based solely on price.

### 4. Procurement KPIs

Display concise KPI cards for:

- Total RFQs
- Open RFQs
- RFQs awaiting review
- Awarded RFQs
- Total quotations received

For a selected RFQ, display:

- Number of quotations
- Number of vendors participating
- Lowest submitted bid
- Highest submitted bid
- Bid spread
- Awarded amount, if awarded

### 5. Response Rate

Where vendor invitation/participation data is available, display:

```text
Response Rate =
vendors who submitted a quote /
vendors eligible to participate × 100
```

Do not calculate this metric if the system does not have reliable eligible-vendor data.

## Vendor Dashboard

Display:

- Open RFQs
- Submitted quotations
- Pending clarification activity
- Awarded quotations

Optional visualization:

- Vendor's own quotation activity over time

Do not expose competing vendor prices or private competitor information to vendors.

## Visualization Rules

- Charts MUST use real API data.
- Do not hardcode chart values.
- Do not generate fake/demo analytics after the application is running.
- Charts must have clear titles and units.
- Charts must have loading, empty, and error states.
- Charts must be responsive.
- Use accessible labels/tooltips where practical.
- Avoid 3D charts.
- Avoid decorative charts with no analytical purpose.
- Keep the number of charts small.
- The detailed quotation comparison table remains the source of truth; charts are supplementary.
- Use a charting library compatible with the existing React/TypeScript stack.
- Do not introduce a second UI component framework solely for charts.

## Quote Comparison Visualization

The quote comparison page MUST contain both:

1. The normalized comparison grid.
2. A visual comparison of total bid amounts.

The grid provides detailed line-item information.

The chart provides rapid visual comparison of overall bid totals.

Neither visualization should automatically determine the award decision.

# Stage 20: UI Requirements

Preserve the existing minimalist visual language.

Requirements:

-   8px spacing system
-   monochrome base palette
-   one restrained accent color
-   glassmorphic elements for specific components (e.g., authentication screens, top navigation bar)
-   dark mode toggle support
-   no gradients
-   no excessive shadows
-   no decorative dashboards
-   clear typography hierarchy
-   responsive layout
-   keyboard-accessible controls
-   visible focus states
-   semantic HTML
-   accessible form labels
-   tables usable on smaller screens through horizontal scrolling

Do not sacrifice usability merely to make the UI look "enterprise".

------------------------------------------------------------------------

# Stage 21: Normalization Grid Correction

The existing `NormalizationGrid.tsx` example contains a data-shape
issue.

`data` is `MatrixRow[]`, so vendor keys MUST NOT be read using:

``` text
data.bids
```

Derive vendor columns from a row, for example:

``` text
Object.keys(data[0]?.bids ?? {})
```

or derive a stable vendor-column list before rendering.

Also ensure that vendor names are not used as unescaped HTML or unsafe
keys.

The component must correctly handle:

``` text
zero rows
one vendor
multiple vendors
missing bid data
large numbers
long descriptions
```

The lowest-price highlighting is informational only. Do not treat the
lowest price as an automatic award recommendation.

------------------------------------------------------------------------

# Stage 22: ERP Integration

The ERP transformer is an integration boundary, not a real ERP
connection.

Implement:

``` text
transform_rfq_to_purchase_order(...)
```

as a deterministic pure service.

Requirements:

-   no network call
-   no database mutation inside the transformer
-   input validated before transformation
-   monetary values remain Decimal
-   output validated by a Pydantic model
-   generated payload must contain:
    -   integration ID
    -   RFQ ID
    -   awarded quote ID
    -   vendor ID/company information required by the schema
    -   currency
    -   total amount
    -   line items
-   transformation must only occur for an awarded quote

Persisting the generated payload is optional for this assignment, but
the generated result must be visible through the demonstration workflow
or logs.

------------------------------------------------------------------------

# Stage 23: Audit Logging

Audit all state-changing operations.

At minimum:

``` text
USER_REGISTERED
USER_LOGIN_SUCCESS
USER_LOGIN_FAILED
RFQ_CREATED
RFQ_UPDATED
RFQ_PUBLISHED
RFQ_REVIEW_STARTED
RFQ_CANCELLED
CLARIFICATION_CREATED
CLARIFICATION_ANSWERED
QUOTE_SUBMITTED
QUOTE_AWARDED
QUOTE_REJECTED
ERP_PAYLOAD_GENERATED
AUTHORIZATION_DENIED
```

Audit records must include enough information to understand:

``` text
who
what
when
which resource
what changed
```

Audit logs must be append-only from the application user's perspective.

Do not expose passwords, JWTs, or other secrets in audit logs.

------------------------------------------------------------------------

# Stage 24: Environment & Secrets

Create:

``` text
.env.example
```

Required environment variables should include at minimum:

``` text
DATABASE_URL
REDIS_URL
JWT_SECRET
JWT_ACCESS_TOKEN_EXPIRE_MINUTES
CORS_ORIGINS
RATE_LIMIT_GENERAL
RATE_LIMIT_AUTH
RATE_LIMIT_QUOTE
```

Do NOT hardcode production secrets.

The Docker Compose file may provide development defaults only if clearly
marked as development-only.

Do not commit `.env`.

------------------------------------------------------------------------

# Stage 25: Docker Requirements

Provide:

``` text
backend/Dockerfile
frontend/Dockerfile
docker-compose.yml
```

Requirements:

-   backend container runs FastAPI
-   frontend container runs Vite in development
-   production frontend build must be possible
-   services communicate through Docker network
-   health checks are defined for PostgreSQL and Redis
-   backend waits for healthy database/Redis
-   database credentials come from environment configuration
-   containers should run as non-root where practical
-   no unnecessary host port exposure in production configuration
-   development and production concerns should be clearly separated

The browser uses:

``` text
http://localhost:8000
```

for the development API.

Container-to-container communication uses service names such as:

``` text
db
redis
backend
```

Do not confuse browser networking with Docker-internal networking.

------------------------------------------------------------------------

# Stage 26: Testing Requirements

The implementation is not complete until tests cover the critical
workflow.

Minimum backend tests:

``` text
registration
login
invalid login
role authorization
RFQ creation
RFQ validation
RFQ publication
deadline enforcement
quote submission
duplicate quote rejection
missing quote item rejection
quote total calculation
clarification anonymity
award transaction
automatic rejection of other quotes
invalid state transitions
object-level authorization
rate limiting
```

Minimum end-to-end scenario:

``` text
Create buyer
Create vendor
Buyer creates RFQ
Buyer publishes RFQ
Vendor sees RFQ
Vendor submits quote
Buyer sees quote
Buyer awards quote
Other quotes are rejected
RFQ is AWARDED
ERP payload is generated
Audit records exist
```

Tests MUST be deterministic and runnable in Docker/local development.

------------------------------------------------------------------------

# Stage 27: Seed Data

Provide a deterministic development seed command/script.

Seed:

``` text
1 buyer
2 vendors
2 RFQs
multiple RFQ items
multiple quotations
at least one clarification thread
```

Passwords must be development-only and documented in the README.

Seed data must make the comparison grid immediately demonstrable.

------------------------------------------------------------------------

# Stage 28: README Requirements

Create a root `README.md` containing:

1.  Project overview
2.  Architecture diagram in text/Markdown
3.  Prerequisites
4.  Environment setup
5.  How to start with Docker Compose
6.  How to run migrations
7.  How to seed demo data
8.  Demo credentials
9.  API documentation URL
10. Test commands
11. Project structure
12. Important architectural decisions
13. Known assignment limitations

The README must contain the exact commands required to run the
application from a clean checkout.

------------------------------------------------------------------------

# Stage 29: Definition of Done

The implementation is considered complete ONLY when all of the following
are true:

-   [ ] `docker compose up --build` starts the stack successfully.
-   [ ] PostgreSQL becomes healthy.
-   [ ] Redis becomes healthy.
-   [ ] Alembic migrations run successfully.
-   [ ] `/health` returns HTTP 200.
-   [ ] `/ready` verifies required dependencies.
-   [ ] Frontend loads successfully.
-   [ ] Buyer registration works.
-   [ ] Vendor registration works.
-   [ ] Login works.
-   [ ] Role-based access control works.
-   [ ] Buyer can create an RFQ.
-   [ ] Buyer can add line items.
-   [ ] Buyer can publish an RFQ.
-   [ ] Vendor can discover an OPEN RFQ.
-   [ ] Vendor can submit exactly one valid quote.
-   [ ] Backend calculates the quote total.
-   [ ] Vendor cannot submit after deadline.
-   [ ] Vendor cannot submit duplicate quote.
-   [ ] Clarifications work without exposing vendor identity.
-   [ ] Buyer can enter review.
-   [ ] Buyer can compare quotes.
-   [ ] Buyer can award one quote.
-   [ ] Concurrent award attempts cannot create multiple awarded quotes.
-   [ ] Other quotes become REJECTED.
-   [ ] RFQ becomes AWARDED.
-   [ ] ERP payload is generated.
-   [ ] Audit logs are created.
-   [ ] Redis rate limiting works.
-   [ ] API errors use the documented error structure.
-   [ ] Pagination works on list endpoints.
-   [ ] Tests pass.
-   [ ] README is complete.
-   [ ] No secrets are committed.
-   [ ] No known critical authorization vulnerability remains.

------------------------------------------------------------------------

# Stage 30: Agent Execution Strategy

Do NOT attempt to generate the entire project in one uncontrolled pass.

Execute in this order:

``` text
Phase 1 — Inspect
↓
Create project tree and verify requirements.

Phase 2 — Infrastructure
↓
Docker Compose
PostgreSQL
Redis
Dockerfiles
environment configuration

Phase 3 — Database
↓
SQLAlchemy models
Alembic
constraints
indexes
seed data

Phase 4 — Backend foundation
↓
configuration
database session
authentication
authorization
error handling
logging

Phase 5 — Core business logic
↓
RFQ service
quote service
clarification service
award transaction
ERP transformer

Phase 6 — API
↓
Pydantic schemas
routers
pagination
authorization
rate limiting
caching

Phase 7 — Frontend
↓
routing
authentication
buyer screens
vendor screens
comparison grid
loading/error/empty states

Phase 8 — Testing
↓
unit tests
integration tests
critical end-to-end workflow

Phase 9 — Validation
↓
docker compose build
migrations
seed
tests
manual API smoke test
manual UI smoke test

Phase 10 — Final cleanup
↓
README
remove dead code
remove hardcoded secrets
verify imports
verify TypeScript
verify formatting
```

At the end of every phase, verify the generated files compile/run before
proceeding.

If a phase fails, fix the failure before continuing.

Do not silently skip failed requirements.

------------------------------------------------------------------------

# Stage 31: Agent Output Rules

When executing this prompt:

1.  Inspect existing files before creating replacements.
2.  Preserve working code unless modification is required.
3.  Do not create duplicate implementations of the same feature.
4.  Do not leave TODO placeholders for required functionality.
5.  Do not use mock API calls when the real backend endpoint is
    required.
6.  Do not fabricate successful API responses.
7.  Do not silently weaken authentication or authorization to make the
    demo work.
8.  Do not hardcode secrets.
9.  Do not use floating-point arithmetic for monetary values.
10. Do not expose internal database models directly through API
    responses.
11. Do not expose vendor identity through anonymous clarification APIs.
12. Do not implement business-critical state transitions only on the
    frontend.
13. Do not claim the application is production-ready unless the
    Definition of Done passes.
14. If a requirement is technically impossible or conflicts with another
    requirement, stop and report the conflict instead of silently
    choosing behavior.
15. Prefer simple, maintainable implementations appropriate for an
    interview assignment over unnecessary enterprise complexity.

------------------------------------------------------------------------

# Stage 32: Final Verification Report

After implementation, produce a concise final report containing:

``` text
1. What was implemented
2. Project structure
3. How to run it
4. Demo credentials
5. API documentation location
6. Tests executed and results
7. Any known limitations
8. Any deliberate deviations from the specification
```

Do not state that a test passed unless it was actually executed.

Do not state that Docker works unless the Docker build/start process was
actually verified.
