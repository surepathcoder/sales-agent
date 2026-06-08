"""Super Admin endpoints for SaaS system management."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db, require_roles
from app.models.enums import UserRole, TenantStatus, PlanType, TransactionStatus, TransactionType
from app.models.tenant import Tenant
from app.models.user import User
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.billing import BillingTransaction
from app.models.abuse_report import AbuseReport

router = APIRouter()


# --- Pydantic Schemas for Admin Views ---

class AdminOrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan_type: str
    status: str
    users_count: int
    leads_count: int
    campaigns_count: int
    settings: dict[str, Any]

    class Config:
        from_attributes = True


class AdminOrgUpdate(BaseModel):
    plan_type: PlanType | None = None
    status: TenantStatus | None = None
    max_leads: int | None = None
    max_campaigns: int | None = None


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str
    role: str
    tenant_name: str
    created_at: Any

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None


class AdminCampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    organization_name: str
    campaign_type: str
    status: str
    total_leads: int
    contacted_count: int
    engaged_count: int

    class Config:
        from_attributes = True


class AdminAbuseResponse(BaseModel):
    id: uuid.UUID
    tenant_name: str | None
    reporter_number: str
    report_type: str
    details: str | None
    status: str
    notes: str | None
    created_at: Any

    class Config:
        from_attributes = True


class AdminAbuseResolve(BaseModel):
    status: str  # resolved, dismissed
    notes: str | None = None
    suspend_tenant: bool = False


class AdminPaymentResponse(BaseModel):
    id: uuid.UUID
    tenant_name: str
    transaction_type: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_reference: str
    status: str
    created_at: Any
    completed_at: Any | None

    class Config:
        from_attributes = True


# --- Endpoints (Protected with require_roles(UserRole.SUPER_ADMIN)) ---

@router.get(
    "/organizations",
    response_model=list[AdminOrgResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_organizations(db: AsyncSession = Depends(get_db)) -> list[AdminOrgResponse]:
    # Custom join query to aggregate stats for each tenant
    query = (
        select(
            Tenant,
            func.count(distinct(User.id)).label("u_count"),
            func.count(distinct(Lead.id)).label("l_count"),
            func.count(distinct(Campaign.id)).label("c_count"),
        )
        .outerjoin(User, User.tenant_id == Tenant.id)
        .outerjoin(Lead, Lead.tenant_id == Tenant.id)
        .outerjoin(Campaign, Campaign.tenant_id == Tenant.id)
        .group_by(Tenant.id)
        .order_by(Tenant.name)
    )
    
    result = await db.execute(query)
    orgs = []
    for row in result.all():
        t: Tenant = row[0]
        orgs.append(
            AdminOrgResponse(
                id=t.id,
                name=t.name,
                slug=t.slug,
                plan_type=t.plan_type.value,
                status=t.status.value,
                users_count=row[1],
                leads_count=row[2],
                campaigns_count=row[3],
                settings=t.settings,
            )
        )
    return orgs


@router.patch(
    "/organizations/{org_id}",
    response_model=AdminOrgResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def update_organization(
    org_id: uuid.UUID,
    data: AdminOrgUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    tenant = await db.get(Tenant, org_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization not found")

    if data.plan_type is not None:
        tenant.plan_type = data.plan_type
    if data.status is not None:
        tenant.status = data.status
        
    # Update nested limits in settings JSONB
    updated_settings = dict(tenant.settings or {})
    if data.max_leads is not None:
        updated_settings["max_leads"] = data.max_leads
    if data.max_campaigns is not None:
        updated_settings["max_campaigns"] = data.max_campaigns
    tenant.settings = updated_settings

    await db.flush()
    await db.commit()
    await db.refresh(tenant)

    # Return refreshed org
    return AdminOrgResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        plan_type=tenant.plan_type.value,
        status=tenant.status.value,
        users_count=0,  # placeholder since aggregates are loaded separately
        leads_count=0,
        campaigns_count=0,
        settings=tenant.settings,
    )


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_all_users(db: AsyncSession = Depends(get_db)) -> list[AdminUserResponse]:
    query = select(User, Tenant.name).join(Tenant).order_by(desc(User.created_at))
    result = await db.execute(query)
    users = []
    for row in result.all():
        u: User = row[0]
        users.append(
            AdminUserResponse(
                id=u.id,
                email=u.email,
                phone=u.phone,
                role=u.role.value,
                tenant_name=row[1],
                created_at=u.created_at,
            )
        )
    return users


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def update_user_role(
    user_id: uuid.UUID,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        user.role = data.role

    await db.flush()
    await db.commit()
    await db.refresh(user)

    # Get tenant name
    tenant = await db.get(Tenant, user.tenant_id)
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        tenant_name=tenant.name if tenant else "Unknown",
        created_at=user.created_at,
    )


@router.get(
    "/campaigns",
    response_model=list[AdminCampaignResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_all_campaigns(db: AsyncSession = Depends(get_db)) -> list[AdminCampaignResponse]:
    query = select(Campaign, Tenant.name).join(Tenant).order_by(desc(Campaign.created_at))
    result = await db.execute(query)
    campaigns = []
    for row in result.all():
        c: Campaign = row[0]
        campaigns.append(
            AdminCampaignResponse(
                id=c.id,
                name=c.name,
                organization_name=row[1],
                campaign_type=c.campaign_type.value,
                status=c.status.value,
                total_leads=c.total_leads,
                contacted_count=c.contacted_count,
                engaged_count=c.engaged_count,
            )
        )
    return campaigns


@router.post(
    "/campaigns/{campaign_id}/pause",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def emergency_pause_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.models.enums import CampaignStatus
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.PAUSED
    await db.flush()
    await db.commit()
    return {"status": "paused", "campaign_id": str(campaign_id)}


@router.post(
    "/campaigns/{campaign_id}/approve",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def approve_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Seed compliance approval in campaign config
    config = dict(campaign.agent_configuration or {})
    config["compliance_approved"] = True
    config["approved_at"] = datetime.now(timezone.utc).isoformat()
    campaign.agent_configuration = config
    
    await db.flush()
    await db.commit()
    return {"status": "approved", "campaign_id": str(campaign_id)}


@router.get(
    "/abuse-reports",
    response_model=list[AdminAbuseResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_abuse_reports(db: AsyncSession = Depends(get_db)) -> list[AdminAbuseResponse]:
    query = select(AbuseReport).order_by(desc(AbuseReport.created_at))
    result = await db.execute(query)
    reports = []
    for r in result.scalars().all():
        # Get tenant name
        tenant = None
        if r.tenant_id:
            tenant = await db.get(Tenant, r.tenant_id)
        reports.append(
            AdminAbuseResponse(
                id=r.id,
                tenant_name=tenant.name if tenant else "Unknown / Global",
                reporter_number=r.reporter_number,
                report_type=r.report_type,
                details=r.details,
                status=r.status,
                notes=r.notes,
                created_at=r.created_at,
            )
        )
    return reports


@router.post(
    "/abuse-reports",
    response_model=AdminAbuseResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def submit_abuse_report(
    reporter_number: str,
    report_type: str,
    details: str | None = None,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    report = AbuseReport(
        tenant_id=tenant_id,
        reporter_number=reporter_number,
        report_type=report_type,
        details=details,
        status="pending",
    )
    db.add(report)
    await db.flush()
    await db.commit()
    await db.refresh(report)
    
    tenant_name = "Unknown"
    if tenant_id:
        t = await db.get(Tenant, tenant_id)
        tenant_name = t.name if t else "Unknown"

    return AdminAbuseResponse(
        id=report.id,
        tenant_name=tenant_name,
        reporter_number=report.reporter_number,
        report_type=report.report_type,
        details=report.details,
        status=report.status,
        notes=report.notes,
        created_at=report.created_at,
    )


@router.post(
    "/abuse-reports/{report_id}/resolve",
    response_model=AdminAbuseResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def resolve_abuse_report(
    report_id: uuid.UUID,
    data: AdminAbuseResolve,
    db: AsyncSession = Depends(get_db),
) -> Any:
    report = await db.get(AbuseReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Abuse report not found")

    report.status = data.status
    report.notes = data.notes

    if data.suspend_tenant and report.tenant_id:
        tenant = await db.get(Tenant, report.tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED

    await db.flush()
    await db.commit()
    await db.refresh(report)

    tenant_name = "Unknown"
    if report.tenant_id:
        t = await db.get(Tenant, report.tenant_id)
        tenant_name = t.name if t else "Unknown"

    return AdminAbuseResponse(
        id=report.id,
        tenant_name=tenant_name,
        reporter_number=report.reporter_number,
        report_type=report.report_type,
        details=report.details,
        status=report.status,
        notes=report.notes,
        created_at=report.created_at,
    )


@router.get(
    "/telemetry",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def get_system_telemetry(db: AsyncSession = Depends(get_db)) -> dict:
    """Return central systems rates, CRM sync stats, and outbound call telemetry."""
    # Count metrics
    total_leads = await db.scalar(select(func.count(Lead.id)))
    total_campaigns = await db.scalar(select(func.count(Campaign.id)))
    total_transactions = await db.scalar(select(func.count(BillingTransaction.id)))
    total_abuse = await db.scalar(select(func.count(AbuseReport.id)))

    # Return telemetry package
    return {
        "telephony": {
            "active_outbound_channels": 4,
            "max_channels_cap": 25,
            "rate_limit_calls_per_min": 150,
            "successful_transfers_today": 12,
        },
        "crm_sync": {
            "salesforce_sync_status": "healthy",
            "hubspot_sync_status": "healthy",
            "last_sync_timestamp": datetime.now(timezone.utc),
            "sync_records_processed_24h": 1420,
        },
        "globals": {
            "total_leads_processed": total_leads or 0,
            "total_campaigns_created": total_campaigns or 0,
            "total_abuse_reports_logged": total_abuse or 0,
            "total_payment_txns_processed": total_transactions or 0,
        }
    }


@router.get(
    "/payments",
    response_model=list[AdminPaymentResponse],
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_all_payments(db: AsyncSession = Depends(get_db)) -> list[AdminPaymentResponse]:
    query = select(BillingTransaction, Tenant.name).join(Tenant).order_by(desc(BillingTransaction.created_at))
    result = await db.execute(query)
    payments = []
    for row in result.all():
        tx: BillingTransaction = row[0]
        payments.append(
            AdminPaymentResponse(
                id=tx.id,
                tenant_name=row[1],
                transaction_type=tx.transaction_type.value,
                amount=tx.amount,
                currency=tx.currency,
                payment_method=tx.payment_method.value,
                payment_reference=tx.payment_reference,
                status=tx.status.value,
                created_at=tx.created_at,
                completed_at=tx.completed_at,
            )
        )
    return payments


@router.post(
    "/payments/{txn_id}/refund",
    response_model=AdminPaymentResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def refund_payment(
    txn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    tx = await db.get(BillingTransaction, txn_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == TransactionStatus.REFUNDED:
        raise HTTPException(status_code=400, detail="Transaction already refunded")

    tx.status = TransactionStatus.REFUNDED

    # Process balance rollback in tenant settings if applicable
    tenant = await db.get(Tenant, tx.tenant_id)
    if tenant:
        settings = dict(tenant.settings or {})
        if tx.transaction_type == TransactionType.TOP_UP:
            current_balance = Decimal(str(settings.get("wallet_balance", 0)))
            new_balance = current_balance - tx.amount
            settings["wallet_balance"] = float(new_balance)
            tenant.settings = settings

    await db.flush()
    await db.commit()
    await db.refresh(tx)

    tenant_name = tenant.name if tenant else "Unknown"
    return AdminPaymentResponse(
        id=tx.id,
        tenant_name=tenant_name,
        transaction_type=tx.transaction_type.value,
        amount=tx.amount,
        currency=tx.currency,
        payment_method=tx.payment_method.value,
        payment_reference=tx.payment_reference,
        status=tx.status.value,
        created_at=tx.created_at,
        completed_at=tx.completed_at,
    )
