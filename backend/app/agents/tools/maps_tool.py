"""
Google Maps business scraper using Playwright.

Discovers B2B leads based on user search query and location criteria.
"""

import logging
import os
import re
import time
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

FAKE_WEBSITE_HINTS = (
  "chat.whatsapp.com",
  "business.google.com/create",
  "maps.google.com",
  "support.google.com",
  "accounts.google.com",
  "google.com/travel",
  "google.com/aclk",
  "google.com/travel/clk",
  "/maps/place/",
  "/maps/search/",
)


def extract_coordinates(page_url: str) -> tuple[float, float] | None:
  """Parse latitude/longitude from Google Maps place URL."""
  match = re.search(r"/@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),", page_url)
  if match:
    return float(match.group(1)), float(match.group(2))
  match_alt = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", page_url)
  if match_alt:
    return float(match_alt.group(1)), float(match_alt.group(2))
  match_data = re.search(r"!3d(-?\d+(?:\.\d+)?)[^!]*!4d(-?\d+(?:\.\d+)?)", page_url)
  if match_data:
    return float(match_data.group(1)), float(match_data.group(2))
  return None


def _clean_phone(phone: str | None) -> str | None:
  """Clean and format phone numbers for Tanzanian standards."""
  if not phone:
    return None
  digits = re.sub(r"\D", "", phone)
  if digits.startswith("255"):
    return f"+{digits}"
  if digits.startswith("0") and len(digits) == 10:
    return f"+255{digits[1:]}"
  if (digits.startswith("7") or digits.startswith("6")) and len(digits) == 9:
    return f"+255{digits}"
  return phone


async def extract_current_details(
  page,
  place_url: str | None = None,
  target_name: str | None = None,
) -> dict[str, Any]:
  """Extract business details from the active Maps detail pane."""
  page_url = page.url
  detail_panes = page.locator("div[role='main']")
  container = page

  panes_count = await detail_panes.count()
  print(f"DEBUG: extract_current_details found {panes_count} detail panes")
  if panes_count > 0:
    found_container = False
    for idx in range(panes_count):
      pane = detail_panes.nth(idx)
      h1_loc = pane.locator("h1")
      h1_count = await h1_loc.count()
      for h_i in range(h1_count):
        h_text = (await h1_loc.nth(h_i).text_content() or "").strip()
        print(f"DEBUG: pane {idx} h1[{h_i}] text: '{h_text}'")
        if h_text:
          if target_name and (target_name.lower() in h_text.lower() or h_text.lower() in target_name.lower()):
            container = pane
            found_container = True
            print(f"DEBUG: matched target_name '{target_name}' at pane index {idx}")
            break
          elif not target_name and h_text != "Results" and not h_text.startswith("Results for"):
            container = pane
            found_container = True
            print(f"DEBUG: matched fallback pane index {idx}")
            break
      if found_container:
        break
    if not found_container:
      container = page
      print("DEBUG: fallback to page container")

  name_loc = container.locator("h1")
  name = target_name or "Unknown business"
  name_count = await name_loc.count()
  if name_count > 0:
    for i in range(name_count):
      text = (await name_loc.nth(i).text_content() or "").strip()
      if text and text != "Results" and not text.startswith("Results for"):
        name = text
        break

  category = ""
  cat_loc = container.locator("button[jsaction*='category']")
  if await cat_loc.count() > 0:
    category = (await cat_loc.first.text_content() or "").strip()
  if not category:
    cat_loc_alt = container.locator("div.fontBodyMedium button")
    if await cat_loc_alt.count() > 0:
      category = (await cat_loc_alt.first.text_content() or "").strip()

  rating = ""
  reviews_count = ""
  rating_container = container.locator("div.F7nice")
  if await rating_container.count() > 0:
    container_text = (await rating_container.first.text_content() or "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\((\d+[\d,]*)\))?", container_text)
    if match:
      rating = match.group(1)
      if match.group(2):
        reviews_count = match.group(2).replace(",", "")

  if not rating:
    rating_loc = container.locator("span[aria-label*='star'], span[aria-label*='Star']")
    for i in range(await rating_loc.count()):
      label = await rating_loc.nth(i).get_attribute("aria-label") or ""
      match = re.search(r"(\d+(?:\.\d+)?)\s*stars?", label, re.IGNORECASE)
      if match:
        rating = match.group(1)
        break

  if not reviews_count:
    reviews_loc = container.locator(
      "button[aria-label*='reviews'], span[aria-label*='reviews'], button[aria-label*='review'], span[aria-label*='review']"
    )
    for i in range(await reviews_loc.count()):
      label = await reviews_loc.nth(i).get_attribute("aria-label") or ""
      match = re.search(r"(\d+[\d,]*)\s*reviews?", label, re.IGNORECASE)
      if match:
        reviews_count = match.group(1).replace(",", "")
        break

  if not reviews_count:
    span_loc = container.locator("span")
    for i in range(await span_loc.count()):
      txt = (await span_loc.nth(i).text_content() or "").strip()
      match = re.match(r"^\((\d+[\d,]*)\)$", txt)
      if match:
        reviews_count = match.group(1).replace(",", "")
        break

  address = ""
  addr_loc = container.locator("button[data-item-id='address']")
  if await addr_loc.count() > 0:
    label = await addr_loc.first.get_attribute("aria-label") or ""
    if label.lower().startswith("address:"):
      address = label[len("address:") :].strip()
    else:
      address = (await addr_loc.first.text_content() or "").strip()
  else:
    addr_loc_alt = container.locator("button[aria-label^='Address:']")
    if await addr_loc_alt.count() > 0:
      label = await addr_loc_alt.first.get_attribute("aria-label") or ""
      address = label[len("address:") :].strip()

  city = ""
  country = ""
  address_lower = address.lower()
  page_url_lower = (page_url or "").lower()
  for token in ("tanzania", "kenya", "uganda", "nigeria", "ghana", "india", "south africa"):
    if token in address_lower or token in page_url_lower:
      country = token.title()
      break
  if not country:
    if any(
      keyword in address_lower or keyword in page_url_lower
      for keyword in ("dar es salaam", "dodoma", "arusha", "mwanza", "mbeya", "tanzania")
    ):
      country = "Tanzania"

  if address:
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if parts:
      for part in reversed(parts):
        part_clean = re.sub(r"\b\d{4,}\b", "", part).strip(" ,;")
        part_lower = part_clean.lower()
        if any(
          k_city in part_lower
          for k_city in (
            "dar es salaam",
            "dodoma",
            "arusha",
            "mwanza",
            "mbeya",
            "morogoro",
            "tanga",
            "kahama",
            "tabora",
            "zanzibar",
          )
        ):
          city = part_clean.title()
          break
      if not city:
        if len(parts) >= 2:
          if parts[-1].title() == country:
            city = re.sub(r"\b\d{4,}\b", "", parts[-2]).strip(" ,;").title()
          else:
            city = re.sub(r"\b\d{4,}\b", "", parts[-1]).strip(" ,;").title()
        else:
          if parts[0].title() != country:
            city = parts[0].title()

  phone = ""
  phone_loc = container.locator("button[data-item-id^='phone:tel:'], a[data-item-id^='phone:tel:']")
  if await phone_loc.count() > 0:
    label = await phone_loc.first.get_attribute("aria-label") or ""
    if label.lower().startswith("phone:"):
      phone = label[len("phone:") :].strip()
    else:
      phone = (await phone_loc.first.text_content() or "").strip()
  if not phone:
    tel_loc = container.locator("a[href^='tel:']")
    if await tel_loc.count() > 0:
      phone = (await tel_loc.first.get_attribute("href") or "").replace("tel:", "").strip()
    else:
      phone_loc_alt = container.locator("button[aria-label^='Phone:']")
      if await phone_loc_alt.count() > 0:
        label = await phone_loc_alt.first.get_attribute("aria-label") or ""
        phone = label[len("phone:") :].strip()

  website = ""
  web_loc = container.locator("a[data-item-id='authority']")
  if await web_loc.count() > 0:
    website = await web_loc.first.get_attribute("href") or ""
  if not website:
    web_loc_alt = container.locator(
      "a[aria-label^='Website:'], a[aria-label^='website:'], a[aria-label='Website'], a[aria-label='website']"
    )
    for i in range(await web_loc_alt.count()):
      href = await web_loc_alt.nth(i).get_attribute("href")
      if href and href.startswith("http") and not any(hint in href.lower() for hint in FAKE_WEBSITE_HINTS):
        if "google.com/aclk" not in href.lower() and "google.com/travel" not in href.lower():
          website = href
          break

  opening_hours = ""
  hours_loc = container.locator("div[data-item-id='oh'], button[data-item-id='oh']")
  if await hours_loc.count() > 0:
    label = await hours_loc.first.get_attribute("aria-label") or ""
    if label:
      opening_hours = label.strip()
    else:
      opening_hours = (await hours_loc.first.text_content() or "").strip()
  if not opening_hours:
    hours_loc_alt = container.locator("[aria-label*='Hours']")
    if await hours_loc_alt.count() > 0:
      opening_hours = await hours_loc_alt.first.get_attribute("aria-label") or ""

  socials = {"facebook": "", "instagram": "", "linkedin": ""}
  try:
    anchors = container.locator("a")
    links_count = min(await anchors.count(), 100)
    for a_idx in range(links_count):
      try:
        a = anchors.nth(a_idx)
        href = (await a.get_attribute("href") or "").strip()
        if "facebook.com" in href:
          socials["facebook"] = href
        elif "instagram.com" in href:
          socials["instagram"] = href
        elif "linkedin.com" in href:
          socials["linkedin"] = href
      except Exception:
        continue
  except Exception:
    pass

  coords = extract_coordinates(place_url or page_url)
  latitude = coords[0] if coords else None
  longitude = coords[1] if coords else None

  summary = name
  if category:
    summary += f" - {category}"
  if address:
    summary += f" located at {address}"

  return {
    "name": name,
    "category": category,
    "address": address,
    "city": city,
    "country": country,
    "phone": _clean_phone(phone),
    "website": website or None,
    "rating": rating,
    "reviews_count": reviews_count,
    "latitude": latitude,
    "longitude": longitude,
    "opening_hours": opening_hours,
    "socials": socials,
    "what_they_do": summary,
  }


async def scrape_google_maps(
  query: str,
  location: str = "Dar es Salaam, Tanzania",
  max_results: int = 20,
  job_id: str | None = None,
) -> list[dict[str, Any]]:
  """
  Scrape Google Maps for businesses matching query + location.

  Returns list of lead candidates with company_name, address, phone, coordinates.
  """
  results: list[dict[str, Any]] = []

  try:
    from playwright.async_api import async_playwright
  except ImportError:
    logger.error("Playwright not installed")
    return results

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
      locale="en-TZ",
      user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      viewport={"width": 1440, "height": 1100},
    )

    # Block heavy visual assets to speed up loading
    async def block_resources(route):
      request = route.request
      resource_type = request.resource_type
      url = request.url
      if (
        resource_type in ("image", "font", "media")
        or "google.com/maps/vt" in url
        or "googleusercontent.com" in url
        or "khms" in url
      ):
        await route.abort()
      else:
        await route.continue_()

    await context.route("**/*", block_resources)

    page = await context.new_page()

    try:
      encoded_query = urllib.parse.quote(f"{query} in {location}")
      search_url = f"https://www.google.com/maps/search/{encoded_query}"

      await page.goto(search_url, wait_until="domcontentloaded", timeout=120000)

      print(f"DEBUG: Loaded page URL: {page.url}")

      try:
        await page.wait_for_selector("div[role='article']", timeout=15000)
      except Exception as e:
        print(f"DEBUG: wait_for_selector failed: {e}")
        pass

      cards_count = await page.locator("div[role='article']").count()
      print(f"DEBUG: cards count: {cards_count}")

      # Handle single-result direct redirect
      has_cards = cards_count > 0
      if "/maps/place/" in page.url and not has_cards:
        try:
          await page.wait_for_selector("h1", timeout=15000)
          await page.wait_for_timeout(2000)
          
          target_name = None
          h1_first = page.locator("h1").first
          if await h1_first.count() > 0:
            target_name = (await h1_first.text_content() or "").strip()
            
          details = await extract_current_details(page, target_name=target_name)
          results.append({
            "company_name": details["name"],
            "address": details["address"],
            "phone": details["phone"],
            "website": details["website"],
            "location_lat": details["latitude"],
            "location_lng": details["longitude"],
            "facebook_url": details["socials"]["facebook"],
            "instagram_url": details["socials"]["instagram"],
            "linkedin_url": details["socials"]["linkedin"],
            "category": details["category"],
            "rating": details["rating"],
            "reviews_count": details["reviews_count"],
            "source": "google_maps",
            "search_query": query,
            "location": location,
            "opening_hours": details["opening_hours"],
          })
        except Exception as e:
          logger.error("Error extracting single direct business details: %s", e)
        return results

      # Scroll results sidebar feed - keep going until we have enough cards
      feed = page.locator("div[role='feed']")
      if await feed.count() > 0:
        last_count = 0
        no_change_iterations = 0
        while True:
          cards = page.locator("div[role='article']")
          current_count = await cards.count()
          print(f"DEBUG: scroll iteration, cards so far: {current_count}")
          if current_count >= max_results * 2:  # gather 2x to have buffer after filtering
            break
          await feed.first.evaluate("el => el.scrollBy(0, 10000)")
          await page.wait_for_timeout(2000)
          new_count = await page.locator("div[role='article']").count()
          if new_count == last_count:
            no_change_iterations += 1
            if no_change_iterations >= 8:
              break
          else:
            no_change_iterations = 0
          last_count = new_count

      cards = page.locator("div[role='article']")
      total_cards = await cards.count()
      
      # Step 1: Extract names and direct URLs of all cards first
      targets = []
      for index in range(total_cards):
        try:
          card = cards.nth(index)
          
          card_name = ""
          card_href = ""

          # Primary: a.hfpxzc (Maps result card link)
          link_loc = card.locator("a.hfpxzc").first
          if await link_loc.count() > 0:
            card_name = (await link_loc.get_attribute("aria-label") or "").strip()
            card_href = (await link_loc.get_attribute("href") or "").strip()

          # Fallback: any <a> pointing to google.com/maps/place
          if not card_href:
            all_links = card.locator("a")
            for li in range(await all_links.count()):
              href_try = (await all_links.nth(li).get_attribute("href") or "").strip()
              if "/maps/place/" in href_try:
                card_href = href_try
                label_try = (await all_links.nth(li).get_attribute("aria-label") or "").strip()
                if label_try:
                  card_name = label_try
                break

          # Fallback name: visible heading inside card
          if not card_name:
            for sel in ["div.fontHeadlineSmall", "div.qBF1Pd", "span.fontHeadlineSmall"]:
              title_loc = card.locator(sel).first
              if await title_loc.count() > 0:
                card_name = (await title_loc.text_content() or "").strip()
                if card_name:
                  break

          if not card_name or not card_href:
            continue

          if "sponsored" in card_name.lower() or card_name.lower().startswith("sponsored"):
            logger.debug("Skipping sponsored card: %s", card_name)
            continue
            
          if card_href and card_name:
            targets.append({"name": card_name, "href": card_href})
        except Exception as e:
          logger.error("Error gathering card at index %s: %s", index, e)
          continue
          
      print(f"DEBUG: Gathered {len(targets)} target URLs to scrape")

      import asyncio as _asyncio

      CONCURRENCY = 3  # parallel browser tabs
      semaphore = _asyncio.Semaphore(CONCURRENCY)
      results_lock = _asyncio.Lock()
      organic_count = 0

      async def scrape_one(idx: int, target: dict) -> None:
        nonlocal organic_count
        async with results_lock:
          if organic_count >= max_results:
            return
        card_name = target["name"]
        card_href = target["href"]
        async with semaphore:
          try:
            print(f"DEBUG: Scraping lead {idx + 1}/{min(len(targets), max_results)}: {card_name}")
            tab = await context.new_page()
            try:
              await tab.goto(card_href, wait_until="domcontentloaded", timeout=45000)
              # Wait for the place detail panel H1 to appear (up to 8 seconds)
              try:
                await tab.wait_for_selector("div[role='main'] h1", timeout=8000)
              except Exception:
                # H1 didn't appear — try waiting a bit more for full JS render
                await tab.wait_for_timeout(2000)
              details = await extract_current_details(tab, card_href, target_name=card_name)
              if details:
                # Accept the lead even if name fell back to target_name, as long as href is a Maps place URL
                lead_name = details.get("name", "")
                if "sponsored" in lead_name.lower():
                  return
                async with results_lock:
                  if organic_count < max_results:
                    results.append({
                      "company_name": details["name"],
                      "address": details["address"],
                      "phone": details["phone"],
                      "website": details["website"],
                      "location_lat": details["latitude"],
                      "location_lng": details["longitude"],
                      "facebook_url": details["socials"]["facebook"],
                      "instagram_url": details["socials"]["instagram"],
                      "linkedin_url": details["socials"]["linkedin"],
                      "category": details["category"],
                      "rating": details["rating"],
                      "reviews_count": details["reviews_count"],
                      "source": "google_maps",
                      "search_query": query,
                      "location": location,
                      "opening_hours": details["opening_hours"],
                    })
                    organic_count += 1
                    print(f"DEBUG: Saved lead {organic_count}/{max_results}: {details['name']}")
                    # Fire a live Redis progress event so the UI counter updates in real-time
                    if job_id:
                      try:
                        from app.services.job_progress import update_job
                        await update_job(
                          job_id,
                          "running",
                          data={
                            "step": "scouting",
                            "progress_pct": min(20, int(organic_count / max_results * 20)),
                            "saved_count": organic_count,
                            "total": max_results,
                          },
                          event=f"Found ✓ {details['name']}",
                        )
                      except Exception as _ev_err:
                        logger.debug("Progress event error: %s", _ev_err)
            finally:
              await tab.close()
          except Exception as e:
            logger.error("Error extracting business %s: %s", card_name, e)

      capped_targets = targets[:max_results + 10]  # extra buffer for filtering
      await _asyncio.gather(*[scrape_one(i, t) for i, t in enumerate(capped_targets)])

    except Exception as e:
      logger.error("Google Maps scrape failed: %s", e)
    finally:
      await browser.close()

  return results

