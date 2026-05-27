from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def research_brand(brand_url: str, goal: str, budget_monthly_usd: float) -> dict[str, Any]:
    """Run brand reconnaissance via the existing AIBMR service.

    Given a public brand URL and a marketing goal, returns a structured brand
    profile that downstream steps will consume.

    Args:
        brand_url: Public-facing URL of the brand (homepage or landing page).
        goal: Plain-English marketing goal (e.g. "100 trial signups per month").
        budget_monthly_usd: Monthly creator budget the brand can commit, in USD.

    Returns:
        dict with keys: ``company``, ``icp``, ``geo``, ``tone_of_voice``,
        ``persons``, ``categories``. ``persons`` is a list of decision-makers
        with verified emails. ``categories`` is a list of CashTime niche
        enum values that map to the brand's product.
    """
    settings = get_settings()
    if settings.demo_mode or not settings.aibmr_base_url:
        return _demo_payload(brand_url, goal, budget_monthly_usd)

    async with internal_client(settings.aibmr_base_url) as http:
        resp = await http.post(
            "/recon",
            json={
                "brand_url": brand_url,
                "goal": goal,
                "budget_monthly_usd": budget_monthly_usd,
            },
        )
        resp.raise_for_status()
        return resp.json()


def _demo_payload(brand_url: str, goal: str, budget: float) -> dict[str, Any]:
    return {
        "company": {
            "name": "Chapterhouse",
            "domain": brand_url,
            "description": (
                "Curated indie-fiction audiobook subscription, $15/mo. Founded 2025, "
                "based in Berlin. Catalog of ~120 independent novels narrated by their "
                "authors. Strong design-led brand. Distribution: web + iOS + Android."
            ),
            "pricing_model": "subscription",
            "monthly_price_usd": 15,
        },
        "icp": {
            "audience": "adult fiction readers, 25–45",
            "psychographics": ["values craft", "anti-bestseller fatigue", "design-conscious"],
            "geo_priority": ["US", "UK", "DE"],
        },
        "geo": ["US", "UK", "DE"],
        "tone_of_voice": "literary, warm, slightly bookish, never hype",
        "persons": [
            {"name": "Demo Founder", "role": "CEO", "email": "founder@chapterhouse.demo", "verified": True},
        ],
        "categories": ["BOOKS_LITERATURE", "ART_DESIGN", "SPIRITUALITY_MINDFULNESS"],
        "_meta": {"source": "demo", "goal": goal, "budget_monthly_usd": budget},
    }
