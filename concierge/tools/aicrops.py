from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def draft_outreach(
    brand_profile: dict[str, Any],
    creator: dict[str, Any],
) -> dict[str, Any]:
    """Draft a personalised first outreach message for a creator via AICROPS.

    AICROPS is the creator-outreach engine: it both writes the draft (here) and
    schedules the follow-up sequence (``schedule_sequence``). Tone-of-voice is
    taken from the brand profile and matched against the creator's niche. Never
    sends; only drafts.

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
    if settings.demo_mode or not settings.aicrops_base_url:
        return _draft_demo(brand_profile, creator)

    async with internal_client(settings.aicrops_base_url) as http:
        resp = await http.post(
            "/draft",
            json={"brand_profile": brand_profile, "creator": creator},
        )
        resp.raise_for_status()
        return resp.json()


def _draft_demo(brand: dict[str, Any], creator: dict[str, Any]) -> dict[str, Any]:
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


async def schedule_sequence(
    creator_id: str,
    initial_draft: dict[str, Any],
    follow_up_count: int = 2,
) -> dict[str, Any]:
    """Schedule a 3-step outreach sequence for a creator via AICROPS.

    The sequence consists of the initial message (drafted by ``draft_outreach``,
    also AICROPS), plus ``follow_up_count`` follow-ups generated with timing
    offsets that AICROPS picks based on historical CashTime response curves.

    Args:
        creator_id: Twenty UUID of the target creator.
        initial_draft: Output of ``draft_outreach`` - subject/body for the
            first message.
        follow_up_count: Number of follow-ups (0..3). Default 2.

    Returns:
        dict with ``sequence_id``, ``steps`` (list of {step, scheduled_at,
        subject, body_markdown}), ``total_messages``.
    """
    settings = get_settings()
    follow_up_count = max(0, min(follow_up_count, 3))

    if settings.demo_mode or not settings.aicrops_base_url:
        return _sequence_demo(creator_id, initial_draft, follow_up_count)

    async with internal_client(settings.aicrops_base_url) as http:
        resp = await http.post(
            "/sequences",
            json={
                "creator_id": creator_id,
                "initial_draft": initial_draft,
                "follow_up_count": follow_up_count,
            },
        )
        resp.raise_for_status()
        return resp.json()


def _sequence_demo(creator_id: str, initial: dict[str, Any], follow_ups: int) -> dict[str, Any]:
    steps = [
        {"step": 1, "scheduled_at": "2026-06-06T09:00:00Z",
         "subject": initial.get("subject"), "body_markdown": initial.get("body_markdown")},
    ]
    for i in range(follow_ups):
        steps.append({
            "step": i + 2,
            "scheduled_at": f"2026-06-{12 + i * 6:02d}T09:00:00Z",
            "subject": f"Re: {initial.get('subject', '')}",
            "body_markdown": "Quick nudge - happy to share more if useful.",
        })
    return {
        "sequence_id": f"demo-seq-{creator_id[:8]}",
        "steps": steps,
        "total_messages": len(steps),
    }
