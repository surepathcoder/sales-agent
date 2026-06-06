"""PostgreSQL enum types for Kijani AI domain models."""

import enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=enum.Enum)


class PgEnumType(SAEnum):
    """Persist enum .value (e.g. 'free') not .name ('FREE') to PostgreSQL."""

    def bind_processor(self, dialect: object):
        def process(value: E | str | None) -> str | None:
            if value is None:
                return None
            if isinstance(value, enum.Enum):
                return value.value
            return value

        return process

    def result_processor(self, dialect: object, coltype: object):
        enum_cls = self.enum_class

        def process(value: str | None) -> E | None:
            if value is None:
                return None
            return enum_cls(value)

        return process


def pg_enum(enum_cls: type[E], name: str) -> PgEnumType:
    return PgEnumType(
        enum_cls,
        name=name,
        create_constraint=True,
        values_callable=lambda x: [e.value for e in x],
    )


class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SALES_MANAGER = "sales_manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class LanguagePreference(str, enum.Enum):
    SW = "sw"
    EN = "en"
    BOTH = "both"


class LeadSource(str, enum.Enum):
    BRELA_VERIFIED = "brela_verified"
    MANUAL = "manual"
    WEB_SCRAPED = "web_scraped"
    IMPORTED = "imported"
    REFERRAL = "referral"
    AI_DISCOVERED = "ai_discovered"


class CompanySize(str, enum.Enum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    RESEARCHING = "researching"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURE = "nurture"


class LeadPriority(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class NextActionType(str, enum.Enum):
    CALL = "call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    MEETING = "meeting"
    FOLLOW_UP = "follow_up"


class ContactType(str, enum.Enum):
    OWNER = "owner"
    DIRECTOR = "director"
    MANAGER = "manager"
    PROCUREMENT = "procurement"
    FINANCE = "finance"
    OPERATIONS = "operations"
    GATEKEEPER = "gatekeeper"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class InfluenceLevel(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    INFLUENCER = "influencer"
    BLOCKER = "blocker"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PHONE_VERIFIED = "phone_verified"
    WHATSAPP_VERIFIED = "whatsapp_verified"
    EMAIL_VERIFIED = "email_verified"
    FULLY_VERIFIED = "fully_verified"


class CampaignType(str, enum.Enum):
    OUTBOUND_SEQUENCE = "outbound_sequence"
    INBOUND_QUALIFICATION = "inbound_qualification"
    REACTIVATION = "reactivation"
    UPSELL = "upsell"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class InteractionChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    LINKEDIN = "linkedin"
    MEETING = "meeting"
    NOTE = "note"


class InteractionDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class InteractionInitiator(str, enum.Enum):
    AI_AGENT = "ai_agent"
    HUMAN_USER = "human_user"
    SYSTEM = "system"
    LEAD = "lead"


class Sentiment(str, enum.Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class IntentDetected(str, enum.Enum):
    INTEREST = "interest"
    OBJECTION = "objection"
    QUESTION = "question"
    COMPLAINT = "complaint"
    REFERRAL = "referral"
    UNSUBSCRIBE = "unsubscribe"
    MEETING_REQUEST = "meeting_request"
    PURCHASE_READY = "purchase_ready"


class DealStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    VERBAL_COMMIT = "verbal_commit"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class PaymentTerms(str, enum.Enum):
    CASH = "cash"
    DAYS_30 = "30_days"
    DAYS_60 = "60_days"
    DAYS_90 = "90_days"
    LPO = "lpo"
    MILESTONE = "milestone"


class ForecastCategory(str, enum.Enum):
    COMMIT = "commit"
    BEST_CASE = "best_case"
    PIPELINE = "pipeline"
    UPSIDE = "upside"


class TransactionType(str, enum.Enum):
    LEAD_PURCHASE = "lead_purchase"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SUCCESS_FEE = "success_fee"
    TOP_UP = "top_up"
    REFUND = "refund"
    COMMISSION_PAYOUT = "commission_payout"


class PaymentMethod(str, enum.Enum):
    M_PESA = "m_pesa"
    TIGO_PESA = "tigo_pesa"
    AIRTEL_MONEY = "airtel_money"
    HALOPESA = "halopesa"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class AgentType(str, enum.Enum):
    SCOUT = "scout"
    RESEARCHER = "researcher"
    OUTREACH = "outreach"
    CLOSER = "closer"


class MemoryType(str, enum.Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    RELATIONSHIP = "relationship"
    OBJECTION = "objection"
    INSIGHT = "insight"
    TASK = "task"
