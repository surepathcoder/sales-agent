"""BRELA Online Registration System lookup."""

import httpx
from bs4 import BeautifulSoup


class BRELAORSClient:
  BASE_URL = "https://ors.brela.go.tz"

  async def lookup_company(self, reg_number: str) -> dict | None:
    """
    Lookup company by registration number.
    MVP: HTTP scrape — production should use official API if available.
    """
    try:
      async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
          f"{self.BASE_URL}/orsreg/searchbusinesspublic",
          params={"regNo": reg_number},
        )
        if resp.status_code != 200:
          return None
        soup = BeautifulSoup(resp.text, "lxml")
        name_el = soup.select_one(".company-name, h2, .business-name")
        if not name_el:
          return {"reg_number": reg_number, "verified": False}
        return {
          "reg_number": reg_number,
          "company_name": name_el.get_text(strip=True),
          "verified": True,
          "source": "brela_ors",
        }
    except Exception:
      return None
