"""
Google Maps business scraper using Playwright.

Discovers B2B leads based on user search query and location criteria.
"""

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


async def scrape_google_maps(
  query: str,
  location: str = "Dar es Salaam, Tanzania",
  max_results: int = 20,
) -> list[dict[str, Any]]:
  """
  Scrape Google Maps for businesses matching query + location.

  Returns list of lead candidates with company_name, address, phone, lat/lng.
  """
  results: list[dict[str, Any]] = []

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    logger.error("Playwright not installed")
    return results

  search_url = (
    f"https://www.google.com/maps/search/{query.replace(' ', '+')}+in+"
    f"{location.replace(' ', '+')}"
  )

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
      locale="en-TZ",
      user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
    )
    page = await context.new_page()

    try:
      await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
      await page.wait_for_timeout(3000)

      # Scroll feed to load more results
      feed = page.locator('div[role="feed"]')
      if await feed.count() > 0:
        for _ in range(min(5, max_results // 4)):
          await feed.evaluate("el => el.scrollTop = el.scrollHeight")
          await page.wait_for_timeout(1500)

      items = page.locator('div[role="feed"] > div > div > a')
      count = await items.count()

      for i in range(min(count, max_results)):
        try:
          await items.nth(i).click(timeout=5000)
          await page.wait_for_timeout(2000)

          name = await _text(page, "h1")
          address = await _text(page, 'button[data-item-id="address"]')
          phone = await _text(page, 'button[data-item-id^="phone"]')
          website = await _href(page, 'a[data-item-id="authority"]')

          coords = _parse_coords(page.url)

          if name:
            results.append({
              "company_name": name,
              "address": address,
              "phone": _clean_phone(phone),
              "website": website,
              "location_lat": coords[0] if coords else None,
              "location_lng": coords[1] if coords else None,
              "source": "google_maps",
              "search_query": query,
              "location": location,
            })
        except Exception as e:
          logger.debug("Maps item %s failed: %s", i, e)
          continue

    except Exception as e:
      logger.error("Google Maps scrape failed: %s", e)
    finally:
      await browser.close()

  return results


async def _text(page, selector: str) -> str | None:
  el = page.locator(selector).first
  if await el.count() > 0:
    return (await el.inner_text()).strip()
  return None


async def _href(page, selector: str) -> str | None:
  el = page.locator(selector).first
  if await el.count() > 0:
    return await el.get_attribute("href")
  return None


def _parse_coords(url: str) -> tuple[float, float] | None:
  match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
  if match:
    return float(match.group(1)), float(match.group(2))
  return None


def _clean_phone(phone: str | None) -> str | None:
  if not phone:
    return None
  digits = re.sub(r"\D", "", phone)
  if digits.startswith("255"):
    return f"+{digits}"
  if digits.startswith("0") and len(digits) == 10:
    return f"+255{digits[1:]}"
  return phone
