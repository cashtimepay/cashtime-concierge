from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def match_creators(
    brand_profile: dict[str, Any],
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Match creators to a brand profile via the existing AI-MM service.

    Args:
        brand_profile: Output of ``research_brand``. Must include ``categories``,
            ``geo``, ``tone_of_voice``.
        limit: Number of top creators to return. Capped at 25.

    Returns:
        A list of creators ordered by fit score (descending). Each item has:
        ``creator_id`` (Twenty UUID), ``handle``, ``platform``, ``niche``,
        ``follower_count``, ``engagement_percent``, ``geo``, ``fit_score``
        (0..1), ``fit_reasons`` (list of short strings).
    """
    settings = get_settings()
    limit = max(1, min(limit, 25))

    if settings.demo_mode or not settings.aimm_base_url:
        return _demo_payload(limit)

    async with internal_client(settings.aimm_base_url) as http:
        resp = await http.post(
            "/match",
            json={"brand_profile": brand_profile, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json().get("creators", [])


def _demo_payload(limit: int) -> list[dict[str, Any]]:
    base = [
        {"handle": "@quietreader", "platform": "instagram", "niche": "BOOKS_LITERATURE",
         "follower_count": 48_200, "engagement_percent": 4.7, "geo": "US",
         "fit_score": 0.93, "fit_reasons": ["literary fiction focus", "high engagement", "US audience"]},
        {"handle": "@inkandvellum", "platform": "youtube", "niche": "BOOKS_LITERATURE",
         "follower_count": 31_500, "engagement_percent": 6.1, "geo": "UK",
         "fit_score": 0.91, "fit_reasons": ["indie-publisher coverage", "UK audience"]},
        {"handle": "@lesemorgen", "platform": "instagram", "niche": "BOOKS_LITERATURE",
         "follower_count": 22_800, "engagement_percent": 5.4, "geo": "DE",
         "fit_score": 0.88, "fit_reasons": ["DE BookTok", "design-led aesthetic"]},
    ]
    return base[:limit]
