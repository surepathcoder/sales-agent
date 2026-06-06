"""
Groq LLM wrapper for Swahili-English Tanzanian B2B sales context.

Primary: llama-3.1-70b-versatile | Fast: llama-3.1-8b-instant
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
    swahili_ratio: float = 0.5,
    tone: str = "professional",
    tenant_id: str = "system",
  ) -> str:
    prompt = f"""Write a WhatsApp outreach message for {contact_name} at {company_name}.
Tone: {tone}. Swahili ratio: {swahili_ratio} (0=English only, 1=Swahili only).
Keep it under 300 characters. Start with appropriate greeting."""
    return await self.chat([{"role": "user", "content": prompt}], tenant_id=tenant_id)

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
