"""Pytest async fixtures."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    with patch("app.database.init_db", new_callable=AsyncMock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def mock_groq_score():
    with patch("app.integrations.groq_client.GroqClient.score_lead", new_callable=AsyncMock) as m:
        m.return_value = {"score": 75, "priority": "warm", "reasoning": "test"}
        yield m
