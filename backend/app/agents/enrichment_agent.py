"""
Enrichment Agent — find contacts, emails, phones, social profiles.

Sits between Researcher and Outreach in the pipeline:
  Scout → Researcher → **Enrichment** → Outreach → Qualification → Closer

Uses Playwright-based enricher_tool for website crawling and Groq LLM
for intelligent contact role classification and deduplication.
"""

import json
import logging
from typing import Any

from app.agents.state import AgentState
from app.config import get_settings
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)


async def _crawl_website(website: str) -> dict[str, Any]:
    """Extract contact details from a website using Playwright."""
    try:
        from app.agents.tools.enricher_tool import extract_contact_details
        return await extract_contact_details(website)
    except Exception as e:
        logger.error("Enrichment website crawl failed for %s: %s", website, e)
        return {}


async def _classify_contacts(
    contacts_raw: list[dict[str, Any]],
    company_name: str,
    tenant_id: str,
) -> list[dict[str, Any]]:
    """Use LLM to classify contact roles and pick decision-makers."""
    if not contacts_raw:
        return []

    groq = GroqClient()
    prompt = (
        f"You are a B2B sales intelligence agent for the Tanzanian market.\n"
        f"Company: {company_name}\n\n"
        f"Contacts found:\n{json.dumps(contacts_raw, indent=2)}\n\n"
        f"For each contact, classify their role as one of: "
        f"owner, director, manager, procurement, finance, operations, gatekeeper.\n"
        f"Also determine if they are likely a decision-maker (true/false).\n"
        f"Return a JSON array of objects with: name, email, phone, role, is_decision_maker, confidence.\n"
        f"Only return the JSON array, no extra text."
    )

    try:
        raw = await groq.chat(
            [{"role": "user", "content": prompt}],
            json_mode=True,
            tenant_id=tenant_id,
        )
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "contacts" in result:
            return result["contacts"]
        return []
    except Exception as e:
        logger.warning("Contact classification failed: %s", e)
        return contacts_raw


async def _deduplicate_contacts(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge new contacts with existing, deduplicating by email/phone."""
    seen_emails: set[str] = set()
    seen_phones: set[str] = set()
    merged: list[dict[str, Any]] = []

    for c in existing:
        email = (c.get("email") or "").lower().strip()
        phone = (c.get("phone") or c.get("whatsapp_number") or "").strip()
        if email:
            seen_emails.add(email)
        if phone:
            seen_phones.add(phone)
        merged.append(c)

    for c in new:
        email = (c.get("email") or "").lower().strip()
        phone = (c.get("phone") or "").strip()
        if email and email in seen_emails:
            continue
        if phone and phone in seen_phones:
            continue
        if email:
            seen_emails.add(email)
        if phone:
            seen_phones.add(phone)
        merged.append(c)

    return merged


async def enrichment_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: enrich a lead with contacts, emails, phones, and socials.

    Reads enriched_lead from Researcher, crawls websites, classifies contacts,
    and outputs enrichment_data + updated contacts on the lead.
    """
    tenant = state.get("tenant", {})
    tenant_id = tenant.get("tenant_id", "system")
    lead = state.get("lead", {})
    enriched = state.get("enriched_lead", {})
    company = lead.get("company_name", enriched.get("company_name", "Unknown"))
    settings = get_settings()

    # Collect all known data points
    all_emails: list[str] = []
    all_phones: list[str] = []
    socials: dict[str, str] = {}
    website_data: dict[str, Any] = {}

    # 1) Check website from lead or enriched data
    website = (
        lead.get("custom_fields", {}).get("website")
        or lead.get("website")
        or enriched.get("custom_fields", {}).get("website")
        or enriched.get("website")
        or ""
    )

    if website and not settings.use_mock_scraper:
        logger.info("Enrichment: crawling website %s for %s", website, company)
        website_data = await _crawl_website(website)
        all_emails.extend(website_data.get("emails", []))
        all_phones.extend(website_data.get("phones", []))
        socials = {
            "facebook": website_data.get("facebook", ""),
            "linkedin": website_data.get("linkedin", ""),
            "instagram": website_data.get("instagram", ""),
        }

    # 2) Merge data from researcher's website_enriched if present
    researcher_enriched = enriched.get("website_enriched", {})
    if researcher_enriched:
        all_emails.extend(researcher_enriched.get("emails", []))
        all_phones.extend(researcher_enriched.get("phones", []))
        if not socials.get("facebook"):
            socials["facebook"] = researcher_enriched.get("facebook", "")
        if not socials.get("linkedin"):
            socials["linkedin"] = researcher_enriched.get("linkedin", "")
        if not socials.get("instagram"):
            socials["instagram"] = researcher_enriched.get("instagram", "")

    # 3) Extract from lead's custom_fields
    custom = lead.get("custom_fields", {})
    if custom.get("phone"):
        all_phones.append(custom["phone"])
    if custom.get("email"):
        all_emails.append(custom["email"])
    for social_key in ("facebook_url", "instagram_url", "linkedin_url"):
        val = custom.get(social_key)
        if val and not socials.get(social_key.replace("_url", "")):
            socials[social_key.replace("_url", "")] = val

    # Deduplicate
    all_emails = list(dict.fromkeys(e.strip().lower() for e in all_emails if e))
    all_phones = list(dict.fromkeys(p.strip() for p in all_phones if p))

    # 4) Build raw contact list for classification
    contacts_raw: list[dict[str, Any]] = []
    existing_contacts = lead.get("contacts", [])

    for email in all_emails:
        contacts_raw.append({"email": email, "phone": "", "name": ""})
    for phone in all_phones:
        if not any(c.get("phone") == phone for c in contacts_raw):
            contacts_raw.append({"email": "", "phone": phone, "name": ""})

    # 5) LLM contact classification
    classified = await _classify_contacts(contacts_raw, company, tenant_id)

    # 6) Merge with existing contacts
    merged_contacts = await _deduplicate_contacts(existing_contacts, classified)

    # Calculate enrichment confidence
    confidence = 0.3  # base
    if all_emails:
        confidence += 0.2
    if all_phones:
        confidence += 0.15
    if any(socials.values()):
        confidence += 0.15
    if website_data.get("about_text"):
        confidence += 0.1
    if classified:
        confidence += 0.1
    confidence = min(confidence, 1.0)

    enrichment_result = {
        "emails": all_emails,
        "phones": all_phones,
        "socials": socials,
        "website_data": {
            "about_text": website_data.get("about_text", ""),
            "services": website_data.get("services", ""),
            "contact_page": website_data.get("contact_page", ""),
        },
        "classified_contacts": classified,
        "contacts_count": len(merged_contacts),
        "decision_makers": [c for c in classified if c.get("is_decision_maker")],
    }

    # Update lead contacts in state
    updated_lead = dict(lead)
    updated_lead["contacts"] = merged_contacts

    return {
        "enrichment_data": enrichment_result,
        "enrichment_confidence": confidence,
        "lead": updated_lead,
        "current_agent": "enrichment",
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"Enrichment complete for {company}: "
                    f"{len(all_emails)} emails, {len(all_phones)} phones, "
                    f"{len(classified)} classified contacts "
                    f"(confidence: {confidence:.0%})"
                ),
            }
        ],
    }
