"""End-to-end smoke test against a running Kijani API."""

import asyncio
import sys
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8002"
UID = uuid.uuid4().hex[:8]


async def main() -> None:
    results: list[tuple[str, bool, str]] = []

    async with httpx.AsyncClient(base_url=BASE, timeout=120.0) as client:
        # 1. Health
        r = await client.get("/health")
        ok = r.status_code == 200 and r.json().get("status") == "healthy"
        results.append(("Health check", ok, r.text[:120]))

        # 2. Register
        email = f"smoke-{UID}@example.com"
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"Smoke Test Co {UID}",
                "email": email,
                "phone": "+255712345678",
                "password": "securepass123",
                "plan_type": "free",
            },
        )
        ok = r.status_code == 201
        results.append(("Register", ok, f"{r.status_code} {r.text[:100]}"))
        if not ok:
            _print_results(results)
            sys.exit(1)

        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Discover leads
        r = await client.post(
            "/api/v1/leads/discover",
            headers=headers,
            json={
                "target_criteria": {
                    "industries": ["hardware"],
                    "locations": ["Dar es Salaam"],
                    "sources": ["google_maps"],
                    "search_query": "hardware stores",
                    "max_results": 5,
                },
                "auto_enrich": False,
            },
        )
        ok = r.status_code == 202
        job_id = r.json().get("job_id") if ok else None
        results.append(("Discover leads (queued)", ok, f"job_id={job_id}"))

        # 4. Poll job
        saved = 0
        if job_id:
            for _ in range(60):
                await asyncio.sleep(2)
                jr = await client.get(f"/api/v1/agents/job/{job_id}", headers=headers)
                if jr.status_code != 200:
                    continue
                data = jr.json()
                if data.get("status") in ("completed", "failed"):
                    saved = data.get("saved_count", 0)
                    ok = data.get("status") == "completed" and saved >= 1
                    results.append(
                        ("Discovery job",
                         ok,
                         f"status={data.get('status')} saved={saved} warning={data.get('warning', '')}"),
                    )
                    break
            else:
                results.append(("Discovery job", False, "timeout waiting for job"))

        # 5. List leads
        r = await client.get("/api/v1/leads", headers=headers)
        leads = r.json().get("items", []) if r.status_code == 200 else []
        ok = r.status_code == 200 and len(leads) >= 1
        results.append(("List leads", ok, f"count={len(leads)}"))

        lead_id = leads[0]["id"] if leads else None

        # 6. Contacts
        if lead_id:
            r = await client.get(f"/api/v1/leads/{lead_id}/contacts", headers=headers)
            contacts = r.json() if r.status_code == 200 else []
            ok = r.status_code == 200 and len(contacts) >= 1
            results.append(("Lead contacts", ok, f"count={len(contacts)}"))

        # 7. Outreach agent
        if lead_id:
            r = await client.post(
                "/api/v1/agents/trigger/outreach",
                headers=headers,
                json={"lead_id": lead_id},
            )
            outreach_job = r.json().get("job_id") if r.status_code == 200 else None
            results.append(("Trigger outreach", r.status_code == 200, f"job={outreach_job}"))
            if outreach_job:
                await asyncio.sleep(5)

        # 8. Pending outreach
        r = await client.get("/api/v1/interactions/pending", headers=headers)
        pending = r.json() if r.status_code == 200 else []
        results.append(("Pending outreach", r.status_code == 200, f"count={len(pending)}"))

        # 9. Create campaign
        if lead_id:
            r = await client.post(
                "/api/v1/campaigns",
                headers=headers,
                json={
                    "name": f"Smoke Campaign {UID}",
                    "campaign_type": "outbound_sequence",
                    "lead_pool": [lead_id],
                    "agent_configuration": {"human_approval_required": True},
                    "sequence_steps": [{"step_order": 1, "channel": "whatsapp"}],
                },
            )
            campaign_id = r.json().get("id") if r.status_code == 201 else None
            results.append(("Create campaign", r.status_code == 201, f"id={campaign_id}"))

            # 10. List campaigns
            r = await client.get("/api/v1/campaigns", headers=headers)
            campaigns = r.json() if r.status_code == 200 else []
            results.append(("List campaigns", r.status_code == 200 and len(campaigns) >= 1, f"count={len(campaigns)}"))

            # 11. Analytics
            r = await client.get("/api/v1/analytics/dashboard", headers=headers)
            results.append(("Analytics dashboard", r.status_code == 200, f"leads={r.json().get('total_leads') if r.status_code==200 else 'err'}"))

    _print_results(results)
    failed = [name for name, ok, _ in results if not ok]
    sys.exit(1 if failed else 0)


def _print_results(results: list[tuple[str, bool, str]]) -> None:
    print(f"\n{'='*60}")
    print(f"Kijani AI Smoke Test — {BASE}")
    print(f"{'='*60}")
    for name, ok, detail in results:
        icon = "PASS" if ok else "FAIL"
        print(f"  [{icon}] {name}: {detail}")
    print(f"{'='*60}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"  {passed}/{len(results)} passed\n")


if __name__ == "__main__":
    asyncio.run(main())
