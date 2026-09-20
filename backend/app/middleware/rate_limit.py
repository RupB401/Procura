import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis
from app.core.config import settings

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.redis = aioredis.from_url(settings.REDIS_URL)

    async def dispatch(self, request: Request, call_next):
        # Determine the appropriate rate limit for the route
        path = request.url.path
        if "/api/v1/auth" in path:
            rate_limit = settings.RATE_LIMIT_AUTH
        elif "quotes" in path and request.method == "POST":
            rate_limit = settings.RATE_LIMIT_QUOTE
        elif "clarifications" in path and request.method == "POST":
            rate_limit = settings.RATE_LIMIT_CLARIFICATION
        elif "/health" in path or "/ready" in path:
            return await call_next(request) # Skip healthchecks
        else:
            rate_limit = settings.RATE_LIMIT_GENERAL

        client_ip = request.client.host
        
        # In a real app we might also append the user ID if authenticated.
        # But we don't have the user ID parsed here easily unless we decode the JWT in the middleware, 
        # which is expensive. So we will rely on IP for the basic middleware.
        key = f"rate_limit:{client_ip}:{path}"
        
        current_time = time.time()
        window_start = current_time - 60
        
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(current_time): current_time})
            await pipe.expire(key, 60)
            results = await pipe.execute()
            
            request_count = results[1]
            
        if request_count >= rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. System limit is {rate_limit} requests per minute."
                    }
                },
                headers={"Retry-After": "60"}
            )
            
        return await call_next(request)
