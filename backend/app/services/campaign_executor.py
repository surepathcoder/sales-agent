"""Execute campaign outreach sequences on lead pools."""

import asyncio
import logging
import uuid

from app.agents.supervisor import _update_job_status, run_outreach_for_lead
from app.models.enums import CampaignStatus, LeadStatus
from app.services.campaign_service import CampaignService
from app.services.lead_service import LeadService

logger = logging.getLogger(__name__)


async def execute_campaign(
  job_id: str,
  tenant_id: uuid.UUID,
  campaign_id: uuid.UUID,
) -> None:
  """Run outreach sequence for each lead in campaign lead_pool."""
  await _update_job_status(
    job_id,
    "running",
    {"campaign_id": str(campaign_id)},
    event="Starting campaign outreach...",
    event_sw="Inaanza kampeni...",
  )

  from app.database import get_db_context

  try:
    async with get_db_context() as db:
      campaign_svc = CampaignService(db, tenant_id)
      campaign = await campaign_svc.get_campaign(campaign_id)
      if not campaign:
        await _update_job_status(job_id, "failed", {"error": "Campaign not found"})
        return

      campaign.status = CampaignStatus.RUNNING
      agent_cfg = campaign.agent_configuration or {}
      human_approval = agent_cfg.get("human_approval_required", True)
      sequence_steps = sorted(
        campaign.sequence_steps or [{"step_order": 1, "channel": "whatsapp", "delay_hours": 0}],
        key=lambda s: s.get("step_order", 1),
      )

      lead_ids = campaign.lead_pool or []
      if not lead_ids:
        await _update_job_status(
          job_id,
          "completed",
          {"contacted": 0, "warning": "Campaign has no leads in lead_pool"},
          event="No leads in campaign",
          event_sw="Hakuna wateja kwenye kampeni",
        )
        return

      contacted = 0
      errors: list[str] = []
      lead_svc = LeadService(db, tenant_id)

      for step_idx, step in enumerate(sequence_steps):
        delay_hours = step.get("delay_hours", 0)
        if step_idx > 0 and delay_hours > 0:
          wait_secs = min(delay_hours * 60, 120)  # MVP: max 2 min between steps
          await _update_job_status(
            job_id,
            "running",
            {"step": f"waiting_{step_idx}", "delay_hours": delay_hours},
            event=f"Waiting before step {step_idx + 1}...",
            event_sw=f"Inasubiri hatua {step_idx + 1}...",
          )
          await asyncio.sleep(wait_secs)

        step_config = {
          "swahili_ratio": agent_cfg.get("swahili_ratio", 0.5),
          "tone": agent_cfg.get("tone", "professional"),
          "channel": step.get("channel", "whatsapp"),
          "template_id": step.get("template_id"),
        }

        for lid in lead_ids:
          try:
            result = await run_outreach_for_lead(
              db,
              tenant_id,
              lid,
              campaign_id=campaign_id,
              human_approval_required=human_approval,
              step_config=step_config,
            )
            if result.get("error"):
              errors.append(f"{lid}: {result['error']}")
            else:
              contacted += 1
              lead = await lead_svc.get_lead(lid)
              if lead and not human_approval:
                lead.status = LeadStatus.CONTACTED
          except Exception as e:
            logger.error("Campaign outreach failed for %s: %s", lid, e)
            errors.append(f"{lid}: {e}")

      campaign.contacted_count = campaign.contacted_count + contacted
      campaign.total_leads = max(campaign.total_leads, len(lead_ids))

      await _update_job_status(
        job_id,
        "completed",
        {
          "campaign_id": str(campaign_id),
          "contacted": contacted,
          "total": len(lead_ids),
          "steps_run": len(sequence_steps),
          "errors": errors,
        },
        event=f"Campaign done — {contacted} messages prepared",
        event_sw=f"Kampeni imekamilika — ujumbe {contacted}",
      )
  except Exception as e:
    logger.exception("Campaign execution failed: %s", e)
    await _update_job_status(job_id, "failed", {"error": str(e)})
