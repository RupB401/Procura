"""
conftest.py — True End-to-End Blackbox tests.

Hits the live Uvicorn server running in the same Docker container.
No dependency overrides, no shared connection pools.
"""
import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.fixture
async def client():
    # Hit the live uvicorn server on port 8000
    # No transport specified means it will make actual HTTP requests
    async with AsyncClient(base_url="http://127.0.0.1:8000") as c:
        yield c
