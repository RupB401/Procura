from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth
from app.middleware.rate_limit import RedisRateLimitMiddleware
from app.core.errors import RFQException

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Exception handler for our custom RFQException
@app.exception_handler(RFQException)
async def rfq_exception_handler(request: Request, exc: RFQException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Rate Limiter Middleware
app.add_middleware(RedisRateLimitMiddleware)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}
