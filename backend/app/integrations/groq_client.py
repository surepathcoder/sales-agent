"""
Groq LLM wrapper for Swahili-English Tanzanian B2B sales context.

Primary: llama-3.3-70b-versatile | Fast: llama-3.1-8b-instant
Falls back to Ollama when rate limited.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator

import httpx
from groq import Groq, RateLimitError

from app.config import get_settings

logger = logging.getLogger(__name__)

TZ_B2B_SYSTEM_PROMPT = """You are a professional sales assistant for Tanzanian B2B businesses.
You communicate in Swahili and English as appropriate.
You understand Tanzanian business culture: relationship-first, respect hierarchy,
use appropriate greetings (Shikamoo for elders, Habari for peers).
You never hard-sell. You build trust first.
You know local payment terms: cash, 30/60/90 days, LPO, milestone-based.
You adapt formality based on contact's title and company size."""


class GroqClient:
  def __init__(self) -> None:
    settings = get_settings()
    self.settings = settings
    self._client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None
    self._token_usage: dict[str, int] = {}

  def _track_tokens(self, tenant_id: str, tokens: int) -> None:
    self._token_usage[tenant_id] = self._token_usage.get(tenant_id, 0) + tokens

  async def _ollama_fallback(self, messages: list[dict], json_mode: bool = False) -> str:
    """Fallback to local Ollama when Groq is rate limited."""
    url = f"{self.settings.ollama_base_url}/api/chat"
    payload: dict[str, Any] = {
      "model": "llama3.1",
      "messages": messages,
      "stream": False,
    }
    if json_mode:
      payload["format"] = "json"
    async with httpx.AsyncClient(timeout=60) as client:
      resp = await client.post(url, json=payload)
      resp.raise_for_status()
      return resp.json()["message"]["content"]

  async def chat(
    self,
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    json_mode: bool = False,
    tenant_id: str = "system",
    max_retries: int = 3,
  ) -> str:
    model = model or self.settings.groq_model_primary
    full_messages = [{"role": "system", "content": TZ_B2B_SYSTEM_PROMPT}, *messages]

    if not self._client:
      return await self._ollama_fallback(full_messages, json_mode)

    for attempt in range(max_retries):
      try:
        kwargs: dict[str, Any] = {
          "model": model,
          "messages": full_messages,
        }
        if json_mode:
          kwargs["response_format"] = {"type": "json_object"}

        response = await asyncio.to_thread(
          self._client.chat.completions.create, **kwargs
        )
        content = response.choices[0].message.content or ""
        if response.usage:
          self._track_tokens(tenant_id, response.usage.total_tokens)
        return content
      except RateLimitError:
        wait = 2**attempt
        logger.warning("Groq rate limited, retry in %ss", wait)
        await asyncio.sleep(wait)
      except Exception as e:
        logger.error("Groq error: %s, falling back to Ollama", e)
        try:
          return await self._ollama_fallback(full_messages, json_mode)
        except Exception:
          if json_mode:
            return '{"score": 50, "priority": "warm", "reasoning": "offline default"}'
          return ""

    try:
      return await self._ollama_fallback(full_messages, json_mode)
    except Exception:
      if json_mode:
        return '{"score": 50, "priority": "warm", "reasoning": "offline default"}'
      return ""

  async def chat_stream(
    self, messages: list[dict[str, str]], tenant_id: str = "system"
  ) -> AsyncIterator[str]:
    if not self._client:
      text = await self._ollama_fallback(
        [{"role": "system", "content": TZ_B2B_SYSTEM_PROMPT}, *messages]
      )
      yield text
      return

    stream = await asyncio.to_thread(
      self._client.chat.completions.create,
      model=self.settings.groq_model_primary,
      messages=[{"role": "system", "content": TZ_B2B_SYSTEM_PROMPT}, *messages],
      stream=True,
    )
    for chunk in stream:
      delta = chunk.choices[0].delta.content
      if delta:
        yield delta

  async def classify(self, text: str, tenant_id: str = "system") -> dict[str, Any]:
    prompt = f"""Classify this message. Return JSON with: sentiment, intent, language (sw/en/mixed).
Message: {text}"""
    result = await self.chat(
      [{"role": "user", "content": prompt}],
      model=self.settings.groq_model_fast,
      json_mode=True,
      tenant_id=tenant_id,
    )
    try:
      return json.loads(result)
    except json.JSONDecodeError:
      return {"sentiment": "neutral", "intent": "question", "language": "mixed"}

  async def generate_outreach_message(
    self,
    company_name: str,
    contact_name: str,
    *,
    channel: str = "whatsapp",
    research_report: dict[str, Any] | None = None,
    sequence_step: int = 0,
    swahili_ratio: float = 0.5,
    tone: str = "professional",
    tenant_id: str = "system",
  ) -> str:
    # Build detailed context from the Phase 3 research report if available
    research_context = ""
    if research_report:
      summary = research_report.get("summary", "")
      pain_points = ", ".join(research_report.get("pain_points", []))
      sales_angle = ", ".join(research_report.get("sales_angle", []))
      research_context = f"""
Additional lead context from research:
- Business Summary: {summary}
- Potential Pain Points: {pain_points}
- Personalization Angles: {sales_angle}"""

    # Customize based on initial or follow-up sequence step
    sequence_context = ""
    if sequence_step > 0:
      sequence_context = f"This is follow-up step #{sequence_step}. Refer to the previous message or outreach attempt respectfully, but keep it fresh and focus on providing value or answering questions."
    else:
      sequence_context = "This is the initial outreach message. Keep it welcoming, establish trust, and highlight why we are reaching out."

    prompt = f"""Generate a personalized B2B outreach message for a Tanzanian business lead.
Recipient: {contact_name}
Company: {company_name}
Channel: {channel}
Tone: {tone}
Swahili ratio: {swahili_ratio} (0.0 = English only, 1.0 = Swahili only, 0.5 = natural Tanzanian code-switching/bilingual mixture).
{sequence_context}{research_context}

Output Guidelines:
- WhatsApp: Write a highly personalized, friendly message under 400 characters using local Tanzanian greetings. Return a JSON object with a single key "message".
- SMS: Write a concise message under 160 characters. Return a JSON object with a single key "message".
- Email: Write a professional email. Return a JSON object with keys "subject" and "body".
- Voice Note: Write a spoken script meant to be read as a Swahili/English voice message. Keep it conversational and brief. Return a JSON object with a single key "voice_script".

Return ONLY a JSON object matching the requested format:
For whatsapp/sms: {{"message": "..."}}
For email: {{"subject": "...", "body": "..."}}
For voice_note: {{"voice_script": "..."}}"""

    result = await self.chat(
      [{"role": "user", "content": prompt}],
      model=self.settings.groq_model_primary,
      json_mode=True,
      tenant_id=tenant_id,
    )
    try:
      # Verify it's valid JSON
      json.loads(result)
      return result
    except Exception:
      # Safe fallback JSON
      if channel == "email":
        return json.dumps({
          "subject": f"Regarding {company_name}",
          "body": f"Habari {contact_name},\n\nWe would love to connect with {company_name} regarding our AI services. Let us know when you are free."
        })
      elif channel == "voice_note":
        return json.dumps({
          "voice_script": f"Habari {contact_name}, naitwa Kijani AI. Ningependa kufahamu kama mtakuwa na nafasi ya kuongea."
        })
      else:
        return json.dumps({
          "message": f"Habari {contact_name} kutoka {company_name}. Ningependa kuwasiliana nanyi kuhusu huduma zetu."
        })

  async def generate_reply_draft(
    self, context: str, tenant_id: str = "system"
  ) -> str:
    prompt = f"""Draft a professional reply to this message. Bilingual Swahili/English as appropriate.
Original: {context}"""
    return await self.chat([{"role": "user", "content": prompt}], tenant_id=tenant_id)

  async def score_lead(self, lead_data: dict[str, Any], tenant_id: str = "system") -> dict:
    prompt = f"""Score this B2B lead 0-100. Return JSON: score, priority (hot/warm/cold), reasoning.
Lead data: {json.dumps(lead_data)}"""
    result = await self.chat(
      [{"role": "user", "content": prompt}],
      model=self.settings.groq_model_fast,
      json_mode=True,
      tenant_id=tenant_id,
    )
    try:
      return json.loads(result)
    except json.JSONDecodeError:
      return {"score": 50, "priority": "warm", "reasoning": "Default score"}

  async def research_lead(self, lead_data: dict[str, Any], tenant_id: str = "system") -> dict[str, Any]:
    prompt = f"""Analyze this lead data and generate a detailed B2B research report.
Lead Data: {json.dumps(lead_data)}

Return a JSON object with the following fields:
1. "summary": A concise, premium description of the business, its services, location, and overall profile.
2. "pain_points": A list of potential business inefficiencies, technology gaps, or challenges they may face in the Tanzanian market.
3. "sales_angle": A list of personalized sales approaches, hooks, or AI solutions that would appeal to them.
4. "best_contact_method": The most effective channel to reach them, strictly one of: "whatsapp", "email", or "phone".

JSON Format:
{{
  "summary": "...",
  "pain_points": ["...", "..."],
  "sales_angle": ["...", "..."],
  "best_contact_method": "whatsapp"
}}"""
    result = await self.chat(
      [{"role": "user", "content": prompt}],
      model=self.settings.groq_model_primary,
      json_mode=True,
      tenant_id=tenant_id,
    )
    try:
      data = json.loads(result)
      # Ensure required keys exist and have correct types
      if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")
      return {
        "summary": str(data.get("summary", "No summary available.")),
        "pain_points": [str(x) for x in data.get("pain_points", []) if x] if isinstance(data.get("pain_points"), list) else [],
        "sales_angle": [str(x) for x in data.get("sales_angle", []) if x] if isinstance(data.get("sales_angle"), list) else [],
        "best_contact_method": str(data.get("best_contact_method", "whatsapp")).lower()
      }
    except Exception as e:
      logger.error("Failed to parse research_lead JSON response: %s", e)
      return {
        "summary": "No summary available.",
        "pain_points": [],
        "sales_angle": [],
        "best_contact_method": "whatsapp",
      }

  async def generate_conversational_reply(
    self,
    conversation_history: list[dict[str, str]],
    tenant_name: str,
    tenant_industry: str,
    lead_name: str,
    lead_research: dict[str, Any] | None = None,
    tenant_id: str = "system",
  ) -> dict[str, Any]:
    history_str = ""
    for msg in conversation_history:
      role = msg.get("role", "user")
      content = msg.get("content", "")
      history_str += f"{role.capitalize()}: {content}\n"

    research_context = ""
    if lead_research:
      summary = lead_research.get("summary", "")
      pain_points = ", ".join(lead_research.get("pain_points", []))
      sales_angle = ", ".join(lead_research.get("sales_angle", []))
      research_context = f"""
Lead Profile Context:
- Summary: {summary}
- Key Pain Points: {pain_points}
- Target Sales Solutions: {sales_angle}"""

    prompt = f"""You are the AI conversation assistant representing the business "{tenant_name}" (Industry: {tenant_industry}).
You are chatting with a contact named "{lead_name}".
Your goal is to build relationships, answer questions (FAQ), qualify their business needs, and hand over to a human agent when they are ready or if they request a human takeover/meeting.

{research_context}

Conversation History:
{history_str}

Please analyze the customer's last message (which is the last "User:" message in the conversation history), and output a JSON object with the following fields:
1. "reply": A natural, friendly, bilingual Swahili/English reply. Keep it under 400 characters, use appropriate local greetings (Habari, Shikamoo), and never hard sell. If they ask a question, answer it based on the business profile. If they want to meet or speak to a manager, acknowledge it and say a human representative will reach out shortly.
2. "intent": Classify the customer's intent: "question" (asking details), "schedule" (wants to meet/call/schedule), "positive" (agrees/interested), "negative" (not interested), "neutral", or "takeover" (explicitly asks to speak to a person/human).
3. "is_qualified": Set to true if the customer has expressed solid interest in your services, shared their pain points, or confirmed they want a demo/proposal/meeting.
4. "requires_takeover": Set to true if the customer wants to schedule a meeting, asks for pricing, asks to speak to a person/manager, or is qualified and ready for human handoff. NOTE: If the customer's message contains requests like "ongea na mtu", "ongea na mtu wenu", "panga ratiba", "panga mkutano", "fanya demo", "demo", "ongea na meneja/mtaalamu/mhusika", "tupigie simu" or any request to talk to a human or schedule a call/demo/meeting, "requires_takeover" MUST be true and "intent" must be "takeover" or "schedule".
5. "reasoning": A brief internal explanation of your classification and action selection.

JSON Format:
{{
  "reply": "...",
  "intent": "question",
  "is_qualified": false,
  "requires_takeover": false,
  "reasoning": "..."
}}"""

    try:
      result = await self.chat(
        [{"role": "user", "content": prompt}],
        model=self.settings.groq_model_primary,
        json_mode=True,
        tenant_id=tenant_id,
      )
      data = json.loads(result)
      return {
        "reply": str(data.get("reply", "")),
        "intent": str(data.get("intent", "question")),
        "is_qualified": bool(data.get("is_qualified", False)),
        "requires_takeover": bool(data.get("requires_takeover", False)),
        "reasoning": str(data.get("reasoning", "")),
      }
    except Exception as e:
      logger.error("Failed to generate conversational reply: %s", e)
      return {
        "reply": "Asante kwa ujumbe wako. Mmoja wa wataalamu wetu atawasiliana nawe hivi karibuni. / Thank you for your message. One of our representatives will contact you shortly.",
        "intent": "neutral",
        "is_qualified": False,
        "requires_takeover": True,
        "reasoning": f"Fallback due to error: {e}",
      }

  async def parse_discovery_intent(
    self, prompt: str, tenant_id: str = "system"
  ) -> dict[str, Any]:
    sys_prompt = """Parse the following natural language request for B2B lead discovery into structured criteria.
Extract the location (city/region), industry, target number of leads (max_results), and category if specified.
Default max_results to 50 if not specified. Default location to 'Dar es Salaam' if not specified.
Return ONLY valid JSON matching this schema:
{
  "location": "string",
  "industry": "string",
  "category": "string",
  "max_results": number
}"""
    try:
      result = await self.chat(
        [
          {"role": "system", "content": sys_prompt},
          {"role": "user", "content": prompt}
        ],
        model=self.settings.groq_model_fast,
        json_mode=True,
        tenant_id=tenant_id,
      )
      data = json.loads(result)
      return {
        "location": data.get("location", "Tanzania"),
        "industry": data.get("industry", "general"),
        "category": data.get("category", ""),
        "max_results": int(data.get("max_results", 50))
      }
    except Exception as e:
      logger.error("Failed to parse discovery intent: %s", e)
      return {
        "location": "Tanzania",
        "industry": "general",
        "category": "",
        "max_results": 50
      }
