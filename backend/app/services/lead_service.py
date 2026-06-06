"""Lead CRUD — all queries filtered by tenant_id."""

import uuid
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import LeadStatus
from app.models.lead import Lead
from app.models.lead_contact import LeadContact
from app.models.enums import ContactType
from app.schemas.contact import LeadContactCreate
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services.tenant_service import TenantService
from app.utils.phone import normalize_tz_phone


class LeadService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def count_leads(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Lead).where(Lead.tenant_id == self.tenant_id)
        )
        return result.scalar_one()

    async def check_lead_limit(self) -> bool:
        tenant_svc = TenantService(self.db, self.tenant_id)
        tenant = await tenant_svc.get_tenant()
        if not tenant:
            return False
        limits = tenant_svc.get_plan_limits(tenant.plan_type.value)
        count = await self.count_leads()
        return count < limits["max_leads"]

    async def find_duplicate(self, company_name: str, phone: str | None = None) -> Lead | None:
        """Detect duplicate by company name or contact phone within tenant."""
        pattern = f"%{company_name.strip()}%"
        result = await self.db.execute(
            select(Lead).where(
                Lead.tenant_id == self.tenant_id,
                Lead.company_name.ilike(pattern),
            ).limit(1)
        )
        dup = result.scalar_one_or_none()
        if dup:
            return dup
        if phone:
            from app.models.lead_contact import LeadContact

            contact_result = await self.db.execute(
                select(Lead)
                .join(LeadContact, LeadContact.lead_id == Lead.id)
                .where(
                    Lead.tenant_id == self.tenant_id,
                    LeadContact.whatsapp_number == phone,
                )
                .limit(1)
            )
            return contact_result.scalar_one_or_none()
        return None

    async def create_lead(self, data: LeadCreate, skip_duplicate: bool = False) -> Lead:
        if not await self.check_lead_limit():
            raise ValueError("Lead limit reached for your plan / Kikomo cha wateja kimefikiwa")

        phone = data.custom_fields.get("phone") if data.custom_fields else None
        if not skip_duplicate:
            existing = await self.find_duplicate(data.company_name, phone)
            if existing:
                raise ValueError(
                    f"Duplicate lead: {existing.company_name} already exists / Mteja tayari yupo"
                )

        lead = Lead(
            tenant_id=self.tenant_id,
            company_name=data.company_name,
            trading_name=data.trading_name,
            source=data.source,
            brela_reg_number=data.brela_reg_number,
            industry_code=data.industry_code,
            company_size=data.company_size,
            address=data.address,
            location_lat=data.location_lat,
            location_lng=data.location_lng,
            tags=data.tags,
            custom_fields=data.custom_fields,
        )
        self.db.add(lead)
        await self.db.flush()
        await self.db.refresh(lead)
        return lead

    async def list_leads(
        self,
        status: LeadStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        priority: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Lead], int]:
        query = select(Lead).where(Lead.tenant_id == self.tenant_id)

        if status:
            query = query.where(Lead.status == status)
        if assigned_to:
            query = query.where(Lead.assigned_to == assigned_to)
        if priority:
            query = query.where(Lead.priority == priority)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(Lead.company_name.ilike(pattern), Lead.trading_name.ilike(pattern))
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        query = query.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        leads = list(result.scalars().all())
        return leads, total

    async def get_lead(self, lead_id: uuid.UUID) -> Lead | None:
        result = await self.db.execute(
            select(Lead)
            .where(Lead.id == lead_id, Lead.tenant_id == self.tenant_id)
            .options(
                selectinload(Lead.contacts),
                selectinload(Lead.interactions),
                selectinload(Lead.deals),
                selectinload(Lead.agent_memories),
            )
        )
        return result.scalar_one_or_none()

    async def update_lead(self, lead_id: uuid.UUID, data: LeadUpdate) -> Lead | None:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lead, field, value)
        return lead

    async def get_contact_count(self, lead_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(LeadContact)
            .where(LeadContact.lead_id == lead_id, LeadContact.tenant_id == self.tenant_id)
        )
        return result.scalar_one()

    async def list_contacts(self, lead_id: uuid.UUID) -> list[LeadContact]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return []
        return lead.contacts

    async def add_contact(self, lead_id: uuid.UUID, data: LeadContactCreate) -> LeadContact | None:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        try:
            whatsapp = normalize_tz_phone(data.whatsapp_number)
        except ValueError:
            whatsapp = data.whatsapp_number

        contact = LeadContact(
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            first_name=data.first_name,
            last_name=data.last_name or "",
            title=data.title,
            email=data.email,
            phone=data.phone,
            whatsapp_number=whatsapp,
            contact_type=data.contact_type,
            is_decision_maker=data.is_decision_maker,
            influence_level=data.influence_level,
            language_preference=data.language_preference,
        )
        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def add_contact_from_phone(
        self,
        lead_id: uuid.UUID,
        phone: str | None,
        company_name: str,
    ) -> LeadContact | None:
        if not phone:
            return None
        try:
            whatsapp = normalize_tz_phone(phone)
        except ValueError:
            return None

        existing = await self.db.execute(
            select(LeadContact).where(
                LeadContact.lead_id == lead_id,
                LeadContact.tenant_id == self.tenant_id,
                LeadContact.whatsapp_number == whatsapp,
            )
        )
        if existing.scalar_one_or_none():
            return None

        return await self.add_contact(
            lead_id,
            LeadContactCreate(
                first_name=company_name.split()[0][:100] if company_name else "Contact",
                last_name="",
                whatsapp_number=whatsapp,
                phone=whatsapp,
                contact_type=ContactType.MANAGER,
                is_decision_maker=True,
            ),
        )

    @staticmethod
    def calc_pages(total: int, limit: int) -> int:
        return ceil(total / limit) if total else 0
