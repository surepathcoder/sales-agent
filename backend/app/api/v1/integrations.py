"""Third-party integration endpoints (WhatsApp, etc.)."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_tenant_id, require_roles
from app.models.enums import UserRole
from app.integrations.whatsapp_web import WhatsAppWebClient

router = APIRouter()


class WhatsAppStatusResponse(BaseModel):
    tenant_id: str
    status: str
    qr: str | None = None


@router.get("/whatsapp/status", response_model=WhatsAppStatusResponse)
async def whatsapp_status(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> WhatsAppStatusResponse:
    client = WhatsAppWebClient()
    data = await client.get_status(str(tenant_id))
    return WhatsAppStatusResponse(
        tenant_id=str(tenant_id),
        status=data.get("status", "unknown"),
    )


@router.get(
    "/whatsapp/qr",
    response_model=WhatsAppStatusResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER))],
)
async def whatsapp_qr(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> WhatsAppStatusResponse:
    client = WhatsAppWebClient()
    data = await client.get_qr(str(tenant_id))
    return WhatsAppStatusResponse(
        tenant_id=str(tenant_id),
        status=data.get("status", "unknown"),
        qr=data.get("qr"),
    )
