"""Mock lead data for development when Playwright sources are blocked."""

from typing import Any


async def mock_scrape_leads(
    query: str,
    location: str = "Dar es Salaam, Tanzania",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Return realistic Tanzanian B2B sample leads for testing."""
    industries = query or "business"
    samples = [
        ("Mwanza Hardware Ltd", "+255712345678", "Sinza, Dar es Salaam"),
        ("Kilimanjaro Supplies Co", "+255723456789", "Arusha Road, Arusha"),
        ("Coastal Builders TZ", "+255734567890", "Kariakoo, Dar es Salaam"),
        ("Lakeview Trading", "+255745678901", "Mwanza City Centre"),
        ("Serengeti Industrial", "+255756789012", "Industrial Area, Dodoma"),
        ("Ubungo Wholesale", "+255767890123", "Ubungo, Dar es Salaam"),
        ("Zanzibar Exports Ltd", "+255778901234", "Stone Town, Zanzibar"),
        ("Morogoro Agro Supply", "+255789012345", "Morogoro Town"),
    ]
    results: list[dict[str, Any]] = []
    for i, (name, phone, address) in enumerate(samples[:max_results]):
        results.append({
            "company_name": f"{name} ({industries})",
            "address": f"{address}, {location}",
            "phone": phone,
            "website": f"https://example.co.tz/{i + 1}",
            "source": "mock_scraper",
            "search_query": query,
            "location": location,
        })
    return results
