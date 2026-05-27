from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def enrich_creator(creator_id: str) -> dict[str, Any]:
    """Refresh creator contact + metrics via CREN.

    Args:
        creator_id: CashTime Twenty UUID for the creator.

    Returns:
        dict with ``creator_id``, ``email``, ``email_verified``,
        ``follower_count``, ``avg_views``, ``engagement_percent``,
        ``last_post_at``, ``biography``, ``platforms`` (list with per-platform
        handles), ``warnings`` (e.g. "no verified email").
    """
    settings = get_settings()
    if settings.demo_mode or not settings.cren_base_url:
        return _demo_payload(creator_id)

    async with internal_client(settings.cren_base_url) as http:
        resp = await http.get(f"/creators/{creator_id}/enrich")
        resp.raise_for_status()
        return resp.json()


def _demo_payload(creator_id: str) -> dict[str, Any]:
    return {
        "creator_id": creator_id,
        "email": "demo@example.com",
        "email_verified": True,
        "follower_count": 30_000,
        "avg_views": 12_500,
        "engagement_percent": 5.2,
        "last_post_at": "2026-05-20T10:00:00Z",
        "biography": "Independent fiction reviews. Berlin → London.",
        "platforms": [
            {"platform": "instagram", "handle": "@demo_handle"},
        ],
        "warnings": [],
    }
