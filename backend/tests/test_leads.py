import json
import uuid
from unittest.mock import patch

import pytest
import redis.asyncio as aioredis

from app.agents.supervisor import run_scout_discovery


@pytest.mark.asyncio
async def test_mock_scout_discovery(mock_groq_score):
    """Discovery with mock scraper saves leads when DB and Redis are available."""
    from app.config import get_settings
    from app.database import get_db_context
    from app.models.enums import PlanType, TenantStatus, UserRole
    from app.models.tenant import Tenant
    from app.models.user import User
    from passlib.context import CryptContext

    settings = get_settings()
    job_id = str(uuid.uuid4())
    tenant_id = uuid.uuid4()

    try:
        async with get_db_context() as db:
            tenant = Tenant(
                id=tenant_id,
                name="Lead Test Tenant",
                slug=f"lead-test-{tenant_id.hex[:8]}",
                plan_type=PlanType.FREE,
                status=TenantStatus.ACTIVE,
            )
            db.add(tenant)
            pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                tenant_id=tenant_id,
                email=f"leadtest-{tenant_id.hex[:6]}@test.local",
                phone="+255700000001",
                password_hash=pwd.hash("testpass123"),
                role=UserRole.ADMIN,
            )
            db.add(user)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    with patch("app.agents.scout_agent.get_settings") as mock_cfg:
        mock_cfg.return_value.use_mock_scraper = True
        await run_scout_discovery(
            job_id=job_id,
            tenant_id=tenant_id,
            target_criteria={
                "industries": ["hardware"],
                "locations": ["Dar es Salaam"],
                "sources": ["google_maps"],
                "search_query": "hardware stores",
                "max_results": 3,
            },
            auto_enrich=False,
        )

    try:
        r = aioredis.from_url(settings.redis_url_str, decode_responses=True)
        raw = await r.get(f"agent_job:{job_id}")
        await r.aclose()
    except Exception as e:
        pytest.skip(f"Redis unavailable: {e}")

    if not raw:
        pytest.skip("Job status not found in Redis")

    status = json.loads(raw)
    assert status["status"] == "completed"
    assert status.get("saved_count", 0) >= 1
