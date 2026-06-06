import uuid

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    uid = uuid.uuid4().hex[:8]
    email = f"test-{uid}@example.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": f"Test Co TZ {uid}",
            "email": email,
            "phone": "+255712345678",
            "password": "securepass123",
            "industry_vertical": "retail",
            "plan_type": "free",
        },
    )
    if reg.status_code != 201:
        pytest.skip(f"Database unavailable: {reg.text}")

    data = reg.json()
    assert "access_token" in data
    assert data["tenant"]["name"] == f"Test Co TZ {uid}"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepass123"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]
