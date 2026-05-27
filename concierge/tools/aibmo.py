from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def draft_outreach(
    brand_profile: dict[str, Any],
    creator: dict[str, Any],
) -> dict[str, Any]:
    """Draft a personalised first outreach email via AIBMO.

    Tone-of-voice is taken from the brand profile and matched against the
    creator's niche. Never sends; only drafts.

    Args:
        brand_profile: Output of ``research_brand``.
        creator: A single creator from ``match_creators`` (post-enrichment is
            preferred but not required).

    Returns:
        dict with ``subject``, ``body_markdown``, ``estimated_response_rate``
        (0..1, based on historical CashTime data for similar pairs),
        ``personalisation_signals`` (list of strings the draft leans on).
    """
    settings = get_settings()
    if settings.demo_mode or not settings.aibmo_base_url:
        return _demo_payload(brand_profile, creator)

    async with internal_client(settings.aibmo_base_url) as http:
        resp = await http.post(
            "/draft",
            json={"brand_profile": brand_profile, "creator": creator},
        )
        resp.raise_for_status()
        return resp.json()


def _demo_payload(brand: dict[str, Any], creator: dict[str, Any]) -> dict[str, Any]:
    handle = creator.get("handle", "@creator")
    return {
        "subject": f"Chapterhouse × {handle} — a quiet collaboration idea",
        "body_markdown": (
            f"Hi {handle},\n\n"
            "We've followed your reviews for a while — your tone matches what we're "
            "building at Chapterhouse, an indie-fiction audiobook subscription.\n\n"
            "Would you be open to a one-month trial in exchange for an honest review?\n\n"
            "— Demo Founder"
        ),
        "estimated_response_rate": 0.21,
        "personalisation_signals": ["niche match", "tone match", "geo match"],
    }
