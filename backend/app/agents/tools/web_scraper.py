"""
Web, Facebook, and Instagram scrapers using Playwright.

Scrapes based on user-provided search queries and target criteria.
"""

import logging
import re
from typing import Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


async def scrape_web(
  query: str,
  location: str = "Tanzania",
  max_results: int = 15,
) -> list[dict[str, Any]]:
  """General web search via Google for B2B businesses."""
  results: list[dict[str, Any]] = []

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    return results

  search_q = f"{query} business {location} contact"
  url = f"https://www.google.com/search?q={quote_plus(search_q)}"

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    try:
      await page.goto(url, wait_until="domcontentloaded", timeout=30000)
      await page.wait_for_timeout(2000)

      snippets = page.locator("div.g")
      count = await snippets.count()

      for i in range(min(count, max_results)):
        try:
          title_el = snippets.nth(i).locator("h3")
          link_el = snippets.nth(i).locator("a").first
          snippet_el = snippets.nth(i).locator("div[data-sncf], span")

          title = await title_el.inner_text() if await title_el.count() else None
          link = await link_el.get_attribute("href") if await link_el.count() else None
          snippet = ""
          if await snippet_el.count():
            snippet = (await snippet_el.first.inner_text())[:500]

          if title and link:
            phone = _extract_phone(snippet)
            results.append({
              "company_name": title,
              "website": link,
              "description": snippet,
              "phone": phone,
              "source": "web_scraped",
              "search_query": query,
            })
        except Exception:
          continue
    except Exception as e:
      logger.error("Web scrape failed: %s", e)
    finally:
      await browser.close()

  return results


async def scrape_facebook(
  query: str,
  location: str = "Dar es Salaam",
  max_results: int = 10,
) -> list[dict[str, Any]]:
  """
  Scrape Facebook business pages matching query.

  Note: Facebook may block automated access; results vary.
  """
  results: list[dict[str, Any]] = []

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    return results

  search_url = (
    f"https://www.facebook.com/search/pages?q={quote_plus(query + ' ' + location)}"
  )

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
      user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
    )
    page = await context.new_page()
    try:
      await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
      await page.wait_for_timeout(4000)

      # Facebook DOM changes frequently — use multiple selectors
      cards = page.locator('div[role="article"], a[href*="/pages/"]')
      count = await cards.count()

      seen: set[str] = set()
      for i in range(min(count, max_results * 2)):
        try:
          card = cards.nth(i)
          text = (await card.inner_text())[:300]
          href = await card.get_attribute("href") if await card.evaluate("el => el.tagName") == "A" else None

          lines = [l.strip() for l in text.split("\n") if l.strip()]
          name = lines[0] if lines else None
          if not name or name in seen:
            continue
          seen.add(name)

          results.append({
            "company_name": name,
            "facebook_url": href or f"https://www.facebook.com/search/pages?q={quote_plus(name)}",
            "description": text,
            "source": "web_scraped",
            "platform": "facebook",
            "search_query": query,
            "location": location,
          })
          if len(results) >= max_results:
            break
        except Exception:
          continue
    except Exception as e:
      logger.error("Facebook scrape failed: %s", e)
    finally:
      await browser.close()

  return results


async def scrape_instagram(
  query: str,
  location: str = "Dar es Salaam",
  max_results: int = 10,
) -> list[dict[str, Any]]:
  """
  Scrape Instagram business profiles via hashtag/location search.
  """
  results: list[dict[str, Any]] = []

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    return results

  hashtag = re.sub(r"[^a-zA-Z0-9]", "", query.replace(" ", ""))[:30]
  search_url = f"https://www.instagram.com/explore/tags/{hashtag}/"

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
      user_agent=(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
      ),
    )
    page = await context.new_page()
    try:
      await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
      await page.wait_for_timeout(4000)

      links = page.locator('a[href*="/p/"], a[href*="/reel/"]')
      count = await links.count()

      for i in range(min(count, max_results)):
        try:
          href = await links.nth(i).get_attribute("href")
          if href:
            results.append({
              "company_name": f"{query} (Instagram)",
              "instagram_url": f"https://www.instagram.com{href}",
              "source": "web_scraped",
              "platform": "instagram",
              "search_query": query,
              "location": location,
              "hashtag": hashtag,
            })
        except Exception:
          continue
    except Exception as e:
      logger.error("Instagram scrape failed: %s", e)
    finally:
      await browser.close()

  return results


def _extract_phone(text: str) -> str | None:
  patterns = [
    r"\+255\d{9}",
    r"0\d{9}",
    r"255\d{9}",
  ]
  for pat in patterns:
    m = re.search(pat, text.replace(" ", ""))
    if m:
      return m.group(0)
  return None
