"""Initial schema — all tables with tenant isolation and pgvector.

Revision ID: 001
Revises:
Create Date: 2026-06-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Enums created implicitly by SQLAlchemy on table creation
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column(
            "plan_type",
            sa.Enum("free", "starter", "growth", "enterprise", name="plan_type"),
            nullable=False,
        ),
        sa.Column("industry_vertical", sa.String(100), nullable=False),
        sa.Column("billing_currency", sa.String(3), nullable=False, server_default="TZS"),
        sa.Column("m_pesa_phone", sa.String(20), nullable=True),
        sa.Column("tigo_pesa_phone", sa.String(20), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "cancelled", name="tenant_status"),
            nullable=False,
        ),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tenants_name", "tenants", ["name"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "super_admin", "admin", "sales_manager", "sales_rep", "viewer",
                name="user_role",
            ),
            nullable=False,
        ),
        sa.Column("nida_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("nida_number", sa.String(512), nullable=True),
        sa.Column(
            "language_preference",
            sa.Enum("sw", "en", "both", name="language_preference"),
            nullable=False,
        ),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "brela_verified", "manual", "web_scraped", "imported", "referral", "ai_discovered",
                name="lead_source",
            ),
            nullable=False,
        ),
        sa.Column("brela_reg_number", sa.String(50), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("trading_name", sa.String(255), nullable=True),
        sa.Column("industry_code", sa.String(20), nullable=False),
        sa.Column(
            "company_size",
            sa.Enum("micro", "small", "medium", "large", "enterprise", name="company_size"),
            nullable=False,
        ),
        sa.Column("annual_revenue_estimate", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "new", "researching", "contacted", "engaged", "qualified", "proposal",
                "negotiating", "closed_won", "closed_lost", "nurture",
                name="lead_status",
            ),
            nullable=False,
        ),
        sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "priority",
            sa.Enum("hot", "warm", "cold", name="lead_priority"),
            nullable=False,
        ),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("custom_fields", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ai_insights", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "next_action_type",
            sa.Enum("call", "whatsapp", "email", "meeting", "follow_up", name="next_action_type"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_leads_tenant_id", "leads", ["tenant_id"])
    op.create_index("ix_leads_company_name", "leads", ["company_name"])
    op.create_index("ix_leads_brela_reg_number", "leads", ["brela_reg_number"])
    op.create_index("ix_leads_status", "leads", ["status"])

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "campaign_type",
            sa.Enum(
                "outbound_sequence", "inbound_qualification", "reactivation", "upsell",
                name="campaign_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "scheduled", "running", "paused", "completed", "archived", name="campaign_status"),
            nullable=False,
        ),
        sa.Column("target_criteria", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("lead_pool", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("agent_configuration", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("sequence_steps", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engaged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("converted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("budget_allocated", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("spend_to_date", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("roi_estimate", sa.Numeric(10, 4), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.create_table(
        "lead_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "contact_type",
            sa.Enum(
                "owner", "director", "manager", "procurement", "finance", "operations", "gatekeeper",
                name="contact_type",
            ),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(150), nullable=True),
        sa.Column("gender", sa.Enum("male", "female", "unknown", name="gender"), nullable=False),
        sa.Column("email", sa.String(512), nullable=True),
        sa.Column("phone", sa.String(512), nullable=True),
        sa.Column("whatsapp_number", sa.String(20), nullable=False),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("is_decision_maker", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "influence_level",
            sa.Enum("primary", "secondary", "influencer", "blocker", name="influence_level"),
            nullable=False,
        ),
        sa.Column(
            "language_preference",
            sa.Enum("sw", "en", "both", name="contact_language_preference"),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Africa/Dar_es_Salaam"),
        sa.Column("best_contact_time", sa.String(100), nullable=True),
        sa.Column(
            "verification_status",
            sa.Enum(
                "unverified", "phone_verified", "whatsapp_verified", "email_verified", "fully_verified",
                name="verification_status",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_contacts_lead_id", "lead_contacts", ["lead_id"])
    op.create_index("ix_lead_contacts_tenant_id", "lead_contacts", ["tenant_id"])
    op.create_index("ix_lead_contacts_whatsapp_number", "lead_contacts", ["whatsapp_number"])

    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "channel",
            sa.Enum("whatsapp", "email", "sms", "phone_call", "linkedin", "meeting", "note", name="interaction_channel"),
            nullable=False,
        ),
        sa.Column(
            "direction",
            sa.Enum("outbound", "inbound", name="interaction_direction"),
            nullable=False,
        ),
        sa.Column(
            "initiated_by",
            sa.Enum("ai_agent", "human_user", "system", "lead", name="interaction_initiator"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_vector", Vector(1536), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ai_model_version", sa.String(100), nullable=True),
        sa.Column("human_approved", sa.Boolean(), nullable=True),
        sa.Column(
            "sentiment",
            sa.Enum("very_positive", "positive", "neutral", "negative", "very_negative", name="sentiment"),
            nullable=True,
        ),
        sa.Column(
            "intent_detected",
            sa.Enum(
                "interest", "objection", "question", "complaint", "referral", "unsubscribe",
                "meeting_request", "purchase_ready",
                name="intent_detected",
            ),
            nullable=True,
        ),
        sa.Column(
            "language_used",
            sa.Enum("sw", "en", "both", name="interaction_language"),
            nullable=True,
        ),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("follow_up_action", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interactions_tenant_id", "interactions", ["tenant_id"])
    op.create_index("ix_interactions_lead_id", "interactions", ["lead_id"])
    op.create_index("ix_interactions_contact_id", "interactions", ["contact_id"])
    op.create_index("ix_interactions_campaign_id", "interactions", ["campaign_id"])

    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deal_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="TZS"),
        sa.Column("probability", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "stage",
            sa.Enum(
                "prospecting", "qualification", "proposal", "negotiation",
                "verbal_commit", "closed_won", "closed_lost",
                name="deal_stage",
            ),
            nullable=False,
        ),
        sa.Column("expected_close_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("loss_reason", sa.String(500), nullable=True),
        sa.Column("competitor_mentioned", sa.String(255), nullable=True),
        sa.Column("products_services", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column(
            "payment_terms",
            sa.Enum("cash", "30_days", "60_days", "90_days", "lpo", "milestone", name="payment_terms"),
            nullable=False,
        ),
        sa.Column("commission_earned", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "ai_forecast_category",
            sa.Enum("commit", "best_case", "pipeline", "upside", name="forecast_category"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_deals_tenant_id", "deals", ["tenant_id"])
    op.create_index("ix_deals_lead_id", "deals", ["lead_id"])
    op.create_index("ix_deals_stage", "deals", ["stage"])

    op.create_table(
        "billing_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "transaction_type",
            sa.Enum(
                "lead_purchase", "subscription_renewal", "success_fee", "top_up", "refund", "commission_payout",
                name="transaction_type",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="TZS"),
        sa.Column(
            "payment_method",
            sa.Enum(
                "m_pesa", "tigo_pesa", "airtel_money", "halopesa", "bank_transfer", "card",
                name="payment_method",
            ),
            nullable=False,
        ),
        sa.Column("payment_reference", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "completed", "failed", "refunded", name="transaction_status"),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_billing_transactions_tenant_id", "billing_transactions", ["tenant_id"])
    op.create_index("ix_billing_transactions_payment_reference", "billing_transactions", ["payment_reference"])
    op.create_index("ix_billing_transactions_status", "billing_transactions", ["status"])

    op.create_table(
        "agent_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "agent_type",
            sa.Enum("scout", "researcher", "outreach", "closer", name="agent_type"),
            nullable=False,
        ),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_contacts.id", ondelete="CASCADE"), nullable=True),
        sa.Column(
            "memory_type",
            sa.Enum("fact", "preference", "relationship", "objection", "insight", "task", name="memory_type"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_vector", Vector(1536), nullable=True),
        sa.Column("confidence_score", sa.Numeric(3, 2), nullable=False, server_default="0.80"),
        sa.Column("source_interaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_memories_tenant_id", "agent_memories", ["tenant_id"])
    op.create_index("ix_agent_memories_agent_type", "agent_memories", ["agent_type"])
    op.create_index("ix_agent_memories_lead_id", "agent_memories", ["lead_id"])


def downgrade() -> None:
    op.drop_table("agent_memories")
    op.drop_table("billing_transactions")
    op.drop_table("deals")
    op.drop_table("interactions")
    op.drop_table("lead_contacts")
    op.drop_table("campaigns")
    op.drop_table("leads")
    op.drop_table("users")
    op.drop_table("tenants")

    for enum_name in [
        "memory_type", "agent_type", "transaction_status", "payment_method", "transaction_type",
        "forecast_category", "payment_terms", "deal_stage", "interaction_language", "intent_detected",
        "sentiment", "interaction_initiator", "interaction_direction", "interaction_channel",
        "verification_status", "contact_language_preference", "influence_level", "gender",
        "contact_type", "campaign_status", "campaign_type", "next_action_type", "lead_priority",
        "lead_status", "company_size", "lead_source", "language_preference", "user_role",
        "tenant_status", "plan_type",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
