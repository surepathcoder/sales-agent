"""
Website Enrichment Tool using Playwright.

Crawls lead websites to discover emails, phones, socials, and contact page content.
"""

import logging
import os
import re
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?[0-9][0-9\s().-]{7,}[0-9]")
CONTACT_HINTS = ("contact", "about", "team", "company", "profile", "reach", "support")


def _normalize_url(value: str) -> str:
  value = (value or "").strip()
  if not value:
    return ""
  if value.startswith("http://") or value.startswith("https://"):
    return value
  return f"https://{value}"


async def _extract_socials(page) -> dict[str, str]:
  socials = {"facebook": "", "linkedin": "", "instagram": ""}
  try:
    hrefs = []
    anchors = page.locator("a")
    anchors_count = await anchors.count()
    for idx in range(anchors_count):
      try:
        anchor = anchors.nth(idx)
        href = (await anchor.get_attribute("href") or "").strip()
        if href:
          hrefs.append(href)
      except Exception:
        continue

    for href in hrefs:
      href_lower = href.lower()
      if any(
        p in href_lower
        for p in (
          "/sharer",
          "/share",
          "/intent",
          "/plugins",
          "/embed",
          "/tr/",
          "/policies",
          "/developer",
          "/p/",
          "facebook.com/sharer",
          "linkedin.com/share",
        )
      ):
        continue

      if "facebook.com" in href_lower and not socials["facebook"]:
        socials["facebook"] = href
      elif "linkedin.com" in href_lower and not socials["linkedin"]:
        socials["linkedin"] = href
      elif "instagram.com" in href_lower and not socials["instagram"]:
        socials["instagram"] = href
  except Exception:
    pass
  return socials


async def _extract_emails_from_page(page, body_text: str) -> list[str]:
  raw_matches = EMAIL_RE.findall(body_text)

  html_matches = []
  try:
    html_content = await page.content() or ""
    html_matches = EMAIL_RE.findall(html_content)
  except Exception:
    pass

  obfuscated_text = (
    body_text.replace(" [at] ", "@")
    .replace(" (at) ", "@")
    .replace("[at]", "@")
    .replace("(at)", "@")
    .replace(" [dot] ", ".")
    .replace(" (dot) ", ".")
    .replace("[dot]", ".")
    .replace("(dot)", ".")
  )
  cleaned_matches = EMAIL_RE.findall(obfuscated_text)

  mailto_matches = []
  try:
    mailto_anchors = page.locator('a[href^="mailto:"]')
    mailto_count = await mailto_anchors.count()
    for idx in range(mailto_count):
      try:
        anchor = mailto_anchors.nth(idx)
        href = (await anchor.get_attribute("href") or "").strip()
        if href.lower().startswith("mailto:"):
          email_val = href[7:].split("?")[0].strip()
          if "@" in email_val and "." in email_val:
            mailto_matches.append(email_val)
      except Exception:
        continue
  except Exception:
    pass

  seen = {}
  for email in raw_matches + html_matches + cleaned_matches + mailto_matches:
    try:
      email = urllib.parse.unquote(email)
    except Exception:
      pass
    email_clean = email.strip().strip(".").lower()
    if EMAIL_RE.match(email_clean) and email_clean not in seen:
      seen[email_clean] = email.strip()
  return list(seen.values())


async def _extract_contact_page(page) -> str:
  try:
    anchors = page.locator("a")
    anchors_count = min(await anchors.count(), 80)
    for idx in range(anchors_count):
      try:
        anchor = anchors.nth(idx)
        href = (await anchor.get_attribute("href") or "").strip()
        text = (await anchor.inner_text(timeout=5000) or "").strip().lower()
        if not href or not text:
          continue
        if any(token in text for token in CONTACT_HINTS) or any(
          token in href.lower() for token in CONTACT_HINTS
        ):
          return _normalize_url(href)
      except Exception:
        continue
  except Exception:
    pass
  return ""


async def extract_contact_details(website: str) -> dict[str, Any]:
  """Extract socials, emails, phones, and about/services from a website."""
  default = {
    "emails": [],
    "phones": [],
    "email": "",
    "facebook": "",
    "linkedin": "",
    "instagram": "",
    "contact_page": "",
    "about_text": "",
    "services": "",
    "about_company": "",
  }
  if not website:
    return default

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    logger.error("Playwright not installed")
    return default

  proxy_settings = None
  proxy_server = os.environ.get("PROXY_SERVER")
  if proxy_server:
    proxy_settings = {"server": proxy_server}
    proxy_user = os.environ.get("PROXY_USER")
    proxy_pass = os.environ.get("PROXY_PASS")
    if proxy_user and proxy_pass:
      proxy_settings["username"] = proxy_user
      proxy_settings["password"] = proxy_pass

  async with async_playwright() as p:
    try:
      browser = await p.chromium.launch(
        headless=True,
        proxy=proxy_settings,
        args=[
          "--disable-blink-features=AutomationControlled",
          "--no-sandbox",
          "--disable-setuid-sandbox",
        ],
      )
      context = await browser.new_context(
        user_agent=(
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
      )
      page = await context.new_page()
      await page.goto(_normalize_url(website), wait_until="domcontentloaded", timeout=60000)
      await page.wait_for_timeout(4000)

      body_loc = page.locator("body")
      text = await body_loc.inner_text(timeout=30000)

      emails = await _extract_emails_from_page(page, text)
      phones = list(dict.fromkeys([item.strip() for item in PHONE_RE.findall(text)]))
      socials = await _extract_socials(page)
      contact_page = await _extract_contact_page(page)
      about_text = " ".join(text.splitlines())[:800]
      services = " ".join(text.splitlines()[:8])[:200]
      about_company = about_text

      if contact_page:
        try:
          await page.goto(contact_page, wait_until="domcontentloaded", timeout=45000)
          await page.wait_for_timeout(3000)
          contact_text = await page.locator("body").inner_text(timeout=30000)
          contact_emails = await _extract_emails_from_page(page, contact_text)
          contact_phones = list(
            dict.fromkeys([item.strip() for item in PHONE_RE.findall(contact_text)])
          )
          emails = list(dict.fromkeys(emails + contact_emails))
          phones = list(dict.fromkeys(phones + contact_phones))
        except Exception:
          pass

      await browser.close()

      return {
        "emails": emails,
        "phones": phones,
        "email": emails[0] if emails else "",
        "facebook": socials["facebook"],
        "linkedin": socials["linkedin"],
        "instagram": socials["instagram"],
        "contact_page": contact_page,
        "about_text": about_text,
        "services": services,
        "about_company": about_company,
      }
    except Exception as e:
      logger.error("Enricher failed for website %s: %s", website, e)
      return default
