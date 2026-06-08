import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.database import get_db_context
from app.models.enums import PlanType, TenantStatus, UserRole, CampaignType, CampaignStatus, LeadStatus
from app.models.tenant import Tenant
from app.models.user import User
from app.models.lead import Lead
from app.models.lead_contact import LeadContact
from app.schemas.campaign import CampaignCreate
from app.services.campaign_service import CampaignService
from app.services.campaign_executor import execute_campaign
from passlib.context import CryptContext


@pytest.fixture
def mock_groq_outreach():
    with patch("app.integrations.groq_client.GroqClient.generate_outreach_message", new_callable=AsyncMock) as m:
        m.return_value = json.dumps({"message": "Habari! Hii ni Kijani AI."})
        yield m


@pytest.mark.asyncio
async def test_campaign_creation_and_execution(mock_groq_outreach):
    job_id = str(uuid.uuid4())
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    lead_id = uuid.uuid4()

    try:
        async with get_db_context() as db:
            # Create Tenant
            tenant = Tenant(
                id=tenant_id,
                name="Campaign Test Tenant",
                slug=f"camp-test-{tenant_id.hex[:8]}",
                plan_type=PlanType.GROWTH,  # Growth plan has enough campaign limits
                status=TenantStatus.ACTIVE,
            )
            db.add(tenant)

            # Create User
            pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"camptest-{tenant_id.hex[:6]}@test.local",
                phone="+255700000002",
                password_hash=pwd.hash("testpass123"),
                role=UserRole.OWNER,
            )
            db.add(user)

            # Create Lead
            lead = Lead(
                id=lead_id,
                tenant_id=tenant_id,
                company_name="Mwanza Retailers Ltd",
                address="Mwanza, Tanzania",
                status=LeadStatus.NEW,
            )
            db.add(lead)
            await db.flush()

            # Create Lead Contact
            contact = LeadContact(
                tenant_id=tenant_id,
                lead_id=lead_id,
                first_name="John",
                last_name="Doe",
                whatsapp_number="+255712345678",
                is_decision_maker=True,
            )
            db.add(contact)
            await db.commit()
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    # Now run CampaignService to create a campaign
    async with get_db_context() as db:
        camp_svc = CampaignService(db, tenant_id)
        campaign_data = CampaignCreate(
            name="Test WhatsApp Outreach",
            campaign_type=CampaignType.OUTBOUND_SEQUENCE,
            target_criteria={},
            lead_pool=[lead_id],
            agent_configuration={"human_approval_required": True, "swahili_ratio": 0.5, "tone": "professional"},
            sequence_steps=[{"step_order": 1, "channel": "whatsapp", "delay_hours": 0}],
        )
        campaign = await camp_svc.create_campaign(campaign_data, user_id)
        await db.commit()
        campaign_id = campaign.id

    # Now execute the campaign
    with patch("app.agents.outreach_agent.send_whatsapp_message", new_callable=AsyncMock) as mock_send_whatsapp:
        mock_send_whatsapp.return_value = {"status": "sent", "delivery_id": "test-delivery-id"}
        
        await execute_campaign(job_id, tenant_id, campaign_id)

    # Verify campaign status and lead/interaction state after execution
    async with get_db_context() as db:
        camp_svc = CampaignService(db, tenant_id)
        updated_camp = await camp_svc.get_campaign(campaign_id)
        assert updated_camp is not None
        assert updated_camp.status == CampaignStatus.RUNNING
        assert updated_camp.contacted_count >= 1

        # Check that the interaction was saved (pending human approval since config has human_approval_required=True)
        from sqlalchemy import select
        from app.models.interaction import Interaction
        result = await db.execute(select(Interaction).where(Interaction.lead_id == lead_id))
        interactions = result.scalars().all()
        assert len(interactions) >= 1
        assert interactions[0].content == "Habari! Hii ni Kijani AI."
        assert interactions[0].human_approved is None


@pytest.mark.asyncio
async def test_fully_automated_campaign_execution(mock_groq_outreach):
    job_id = str(uuid.uuid4())
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    lead_id = uuid.uuid4()

    try:
        async with get_db_context() as db:
            # Create Tenant
            tenant = Tenant(
                id=tenant_id,
                name="Automated Campaign Tenant",
                slug=f"camp-auto-{tenant_id.hex[:8]}",
                plan_type=PlanType.GROWTH,
                status=TenantStatus.ACTIVE,
            )
            db.add(tenant)

            # Create User
            pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"campauto-{tenant_id.hex[:6]}@test.local",
                phone="+255700000003",
                password_hash=pwd.hash("testpass123"),
                role=UserRole.OWNER,
            )
            db.add(user)

            # Create Lead
            lead = Lead(
                id=lead_id,
                tenant_id=tenant_id,
                company_name="Lake Victoria Fish Co",
                address="Mwanza, Tanzania",
                status=LeadStatus.NEW,
            )
            db.add(lead)
            await db.flush()

            # Create Lead Contact
            contact = LeadContact(
                tenant_id=tenant_id,
                lead_id=lead_id,
                first_name="Jane",
                last_name="Doe",
                whatsapp_number="+255711223344",
                is_decision_maker=True,
            )
            db.add(contact)
            await db.commit()
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    # Create campaign with fully automated outreach (human_approval_required: False)
    async with get_db_context() as db:
        camp_svc = CampaignService(db, tenant_id)
        campaign_data = CampaignCreate(
            name="Test Auto WhatsApp Outreach",
            campaign_type=CampaignType.OUTBOUND_SEQUENCE,
            target_criteria={},
            lead_pool=[lead_id],
            agent_configuration={"human_approval_required": False, "swahili_ratio": 0.5, "tone": "professional"},
            sequence_steps=[{"step_order": 1, "channel": "whatsapp", "delay_hours": 0}],
        )
        campaign = await camp_svc.create_campaign(campaign_data, user_id)
        await db.commit()
        campaign_id = campaign.id

    # Execute and verify send_whatsapp_message was called and interaction is marked as approved
    with patch("app.agents.outreach_agent.send_whatsapp_message", new_callable=AsyncMock) as mock_send_whatsapp:
        mock_send_whatsapp.return_value = {"status": "sent", "delivery_id": "test-delivery-id"}
        
        await execute_campaign(job_id, tenant_id, campaign_id)
        
        # Verify WhatsApp dispatch was called with tenant_id string, phone, and text
        mock_send_whatsapp.assert_called_once_with(str(tenant_id), "+255711223344", "Habari! Hii ni Kijani AI.")

    # Verify campaign contacted count, lead status, and interaction human_approved state
    async with get_db_context() as db:
        camp_svc = CampaignService(db, tenant_id)
        updated_camp = await camp_svc.get_campaign(campaign_id)
        assert updated_camp is not None
        assert updated_camp.status == CampaignStatus.RUNNING
        assert updated_camp.contacted_count >= 1

        # Verify Lead Status became CONTACTED
        from app.services.lead_service import LeadService
        lead_svc = LeadService(db, tenant_id)
        updated_lead = await lead_svc.get_lead(lead_id)
        assert updated_lead is not None
        assert updated_lead.status == LeadStatus.CONTACTED

        # The interaction should be marked as automatically approved (True)
        from sqlalchemy import select
        from app.models.interaction import Interaction
        result = await db.execute(select(Interaction).where(Interaction.lead_id == lead_id))
        interactions = result.scalars().all()
        assert len(interactions) >= 1
        assert interactions[0].content == "Habari! Hii ni Kijani AI."
        assert interactions[0].human_approved is True
