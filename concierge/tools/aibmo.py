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
    company = brand.get("company", {})
    name = (company.get("name") or "our brand").split(" ")[0]
    niche = (creator.get("niche") or "").replace("_", " ").lower()
    niche_phrase = f"your {niche} content" if niche else "your content"
    # Subject: short (AICROPS canon: 2-5 words, no "Re:", no templated lines).
    # Greeting: real first names are not known (handles are channel/page names),
    # so we open with a neutral "Hi" and no name (AICROPS canon).
    return {
        "subject": f"{name} collaboration",
        "body_markdown": (
            "Hi,\n\n"
            f"We've been following {niche_phrase} and think it lines up with what "
            f"we're building at {name}. Would you be open to a short collaboration? "
            "Happy to share details.\n\n"
            f"The {name} team"
        ),
        "estimated_response_rate": 0.21,
        "personalisation_signals": ["niche match", "audience fit", "geo match"],
    }
