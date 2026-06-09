from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings
from concierge.tools.aimm import _creator_id, _sample


async def enrich_creator(creator_id: str) -> dict[str, Any]:
    """Refresh a creator's public metrics from the CashTime network.

    Args:
        creator_id: The ``creator_id`` returned by ``match_creators``.

    Returns:
        dict with ``creator_id``, ``handle``, ``platform``, ``follower_count``,
        ``engagement_percent``, ``geo``, ``language``, ``warnings``.
    """
    settings = get_settings()
    if settings.cren_base_url and not settings.demo_mode:
        async with internal_client(settings.cren_base_url) as http:
            resp = await http.get(f"/creators/{creator_id}/enrich")
            resp.raise_for_status()
            return resp.json()

    for c in _sample():
        if _creator_id(c.get("handle", ""), c.get("niche", "")) == creator_id:
            warnings = [] if (c.get("follower_count") or 0) else ["no follower data"]
            return {
                "creator_id": creator_id,
                "handle": c.get("handle"),
                "platform": c.get("platform"),
                "niche": c.get("niche"),
                "follower_count": c.get("follower_count"),
                "engagement_percent": c.get("engagement_percent"),
                "geo": c.get("geo"),
                "language": c.get("language"),
                "warnings": warnings,
            }

    return {"creator_id": creator_id, "follower_count": None, "warnings": ["creator not found"]}
