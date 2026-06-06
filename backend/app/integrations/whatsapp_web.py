"""HTTP client for WhatsApp Web.js sidecar service."""

import httpx

from app.config import get_settings


class WhatsAppWebClient:
  def __init__(self) -> None:
    self.base_url = get_settings().whatsapp_service_url

  async def send_message(self, tenant_id: str, to: str, message: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
      resp = await client.post(
        f"{self.base_url}/send",
        json={"tenant_id": tenant_id, "to": to, "message": message},
      )
      resp.raise_for_status()
      return resp.json()

  async def get_status(self, tenant_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
      resp = await client.get(f"{self.base_url}/status/{tenant_id}")
      resp.raise_for_status()
      return resp.json()

  async def get_qr(self, tenant_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
      resp = await client.get(f"{self.base_url}/qr/{tenant_id}")
      resp.raise_for_status()
      return resp.json()
