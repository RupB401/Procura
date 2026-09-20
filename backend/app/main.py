from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, rfqs, quotes, clarifications
from app.middleware.rate_limit import RedisRateLimitMiddleware
from app.core.errors import RFQException

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# ── Exception handler ──────────────────────────────────────────────────────────
@app.exception_handler(RFQException)
async def rfq_exception_handler(request: Request, exc: RFQException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

# ── CORS ───────────────────────────────────────────────────────────────────────
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Rate Limiter ───────────────────────────────────────────────────────────────
app.add_middleware(RedisRateLimitMiddleware)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix=f"{settings.API_V1_STR}/auth",           tags=["auth"])
app.include_router(rfqs.router,           prefix=f"{settings.API_V1_STR}/rfqs",           tags=["rfqs"])
app.include_router(quotes.router,         prefix=f"{settings.API_V1_STR}/rfqs",           tags=["quotes"])
app.include_router(clarifications.router, prefix=f"{settings.API_V1_STR}/rfqs",           tags=["clarifications"])

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health_check():
    return {"status": "ok"}

@app.get("/ready", tags=["ops"])
async def readiness_check():
    return {"status": "ready"}
