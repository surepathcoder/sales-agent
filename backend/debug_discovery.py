import asyncio
import uuid
import sys
import os

# add backend path
sys.path.append(r"c:\Users\surep\OneDrive\Desktop\projects\sales1\kijani-ai\backend")
from app.agents.supervisor import run_scout_discovery

async def run():
    tenant_id = uuid.uuid4()
    job_id = "test-job-id"
    criteria = {
        "location": "Arusha",
        "industry": "hardware stores",
        "category": "",
        "max_results": 50
    }
    try:
        await run_scout_discovery(job_id, tenant_id, criteria, True)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
