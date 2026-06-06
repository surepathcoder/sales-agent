"""Lead discovery and CRUD endpoints."""

import csv
import io
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_current_user_id, get_db
from app.models.enums import LeadStatus
from app.schemas.common import JobResponse, PaginatedResponse
from app.schemas.contact import LeadContactCreate, LeadContactResponse
from app.schemas.lead import (
    DiscoverLeadsRequest,
    LeadCreate,
    LeadDossierResponse,
    LeadResponse,
    LeadUpdate,
)
from app.services.lead_service import LeadService

router = APIRouter()


async def _run_scout_job(
    job_id: str,
    tenant_id: uuid.UUID,
    criteria: dict,
    auto_enrich: bool,
) -> None:
    from app.agents.supervisor import run_scout_discovery

    await run_scout_discovery(
        job_id=job_id,
        tenant_id=tenant_id,
        target_criteria=criteria,
        auto_enrich=auto_enrich,
    )


@router.post("/discover", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def discover_leads(
    data: DiscoverLeadsRequest,
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        _run_scout_job,
        job_id,
        tenant_id,
        data.target_criteria.model_dump(),
        data.auto_enrich,
    )
    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Scout agent started — searching Google Maps, Facebook, Instagram, and web",
    )


@router.get("", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    status: LeadStatus | None = None,
    assigned_to: uuid.UUID | None = None,
    priority: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LeadResponse]:
    svc = LeadService(db, tenant_id)
    leads, total = await svc.list_leads(status, assigned_to, priority, search, page, limit)
    items = []
    for lead in leads:
        resp = LeadResponse.model_validate(lead)
        resp.contact_count = await svc.get_contact_count(lead.id)
        items.append(resp)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=svc.calc_pages(total, limit),
    )


@router.get("/{lead_id}", response_model=LeadDossierResponse)
async def get_lead(
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> LeadDossierResponse:
    svc = LeadService(db, tenant_id)
    lead = await svc.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found / Mteja hajapatikana")
    resp = LeadDossierResponse.model_validate(lead)
    resp.contact_count = len(lead.contacts)
    resp.contacts = lead.contacts
    resp.interactions = lead.interactions
    resp.deals = lead.deals
    resp.agent_memories = lead.agent_memories
    return resp


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    svc = LeadService(db, tenant_id)
    try:
        lead = await svc.create_lead(data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    resp = LeadResponse.model_validate(lead)
    resp.contact_count = 0
    return resp


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    data: LeadUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    svc = LeadService(db, tenant_id)
    lead = await svc.update_lead(lead_id, data)
    if not lead:
        raise HTTPException(status_code=404)
    resp = LeadResponse.model_validate(lead)
    resp.contact_count = await svc.get_contact_count(lead.id)
    return resp


@router.get("/{lead_id}/contacts", response_model=list[LeadContactResponse])
async def list_lead_contacts(
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[LeadContactResponse]:
    svc = LeadService(db, tenant_id)
    contacts = await svc.list_contacts(lead_id)
    if not contacts and not await svc.get_lead(lead_id):
        raise HTTPException(status_code=404)
    return [LeadContactResponse.model_validate(c) for c in contacts]


@router.post(
    "/{lead_id}/contacts",
    response_model=LeadContactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_lead_contact(
    lead_id: uuid.UUID,
    data: LeadContactCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> LeadContactResponse:
    svc = LeadService(db, tenant_id)
    contact = await svc.add_contact(lead_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadContactResponse.model_validate(contact)


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/import", response_model=ImportResult)
async def import_leads_csv(
    file: UploadFile,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    """Import leads from CSV (company_name, phone, address columns)."""
    svc = LeadService(db, tenant_id)
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    errors: list[str] = []

    for row in reader:
        name = (row.get("company_name") or row.get("company") or row.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        phone = (row.get("phone") or row.get("whatsapp") or row.get("mobile") or "").strip() or None
        try:
            lead = await svc.create_lead(LeadCreate(
                company_name=name,
                address=row.get("address"),
                custom_fields={"phone": phone, "imported": True},
            ))
            if phone:
                await svc.add_contact_from_phone(lead.id, phone, name)
            imported += 1
        except ValueError as e:
            if "Duplicate" in str(e) or "tayari" in str(e) or "limit" in str(e).lower():
                skipped += 1
            else:
                errors.append(f"{name}: {e}")
        except Exception as e:
            errors.append(f"{name}: {e}")

    return ImportResult(imported=imported, skipped=skipped, errors=errors[:20])
