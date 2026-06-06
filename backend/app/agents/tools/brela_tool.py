"""BRELA company lookup tool for agent use."""

from typing import Any

from app.integrations.brela_ors import BRELAORSClient


async def brela_lookup(reg_number: str) -> dict[str, Any] | None:
  client = BRELAORSClient()
  return await client.lookup_company(reg_number)
