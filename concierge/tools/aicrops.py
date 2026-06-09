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


def _brand_name(brand: dict[str, Any]) -> str | None:
    """A clean, real brand name, or None if we don't have one (never 'our')."""
    n = ((brand.get("company") or {}).get("name") or "").strip()
    for sep in (" - ", " | ", " : ", ": ", " – ", " — "):
        n = n.split(sep)[0].strip()
    if not n or n.lower() in {"our brand", "our", "the brand", "brand", "n/a"}:
        return None
    return n[:48]


def _niche_phrase(creator: dict[str, Any]) -> str:
    niche = (creator.get("niche") or "").replace("_", " ").lower().strip()
    return f"your {niche} content" if niche else "your content"


def _compose_messages(name: str | None, niche_phrase: str) -> list[dict[str, Any]]:
    """Three distinct creator-outreach emails, AICROPS-style.

    DM1 = intro + one value angle. DM2 = reuse DM1 subject (same thread, no
    "Re:"), reduce friction, a new angle, never "circling back". DM3 = a fresh
    subject (no "Re:"), another facet, door stays open (not a goodbye). Short,
    plain, one light concrete CTA each.
    """
    at_brand = f" at {name}" if name else ""
    signoff = f"The {name} team" if name else "Talk soon,\nThe partnerships team"
    s1 = f"{name} collaboration" if name else "A collaboration idea"
    s3 = f"Still keen, {name}" if name and len(name) < 24 else "Still keen to collaborate"

    dm1 = (
        "Hi,\n\n"
        f"We've been following {niche_phrase} and there's a genuine fit with what "
        f"we're building{at_brand}. We'd love to explore a short collaboration with you.\n\n"
        "Could I send over a quick overview of what we have in mind?\n\n"
        f"{signoff}"
    )
    dm2 = (
        "Hi,\n\n"
        "No big commitment on your side - we can start with a single piece and see "
        "how it lands with your audience. We handle the brief and the product; you "
        "keep full creative control over how it fits your style.\n\n"
        "Want me to drop a short outline of how a first collaboration could look?\n\n"
        f"{signoff}"
    )
    dm3 = (
        "Hi,\n\n"
        f"Your audience is exactly who we're hoping to reach, which is why we keep "
        f"coming back to {niche_phrase}. Whenever the timing works for you, the offer "
        "stands - no rush.\n\n"
        "Happy to shape the idea around whatever format you enjoy making most. "
        "Want a couple of concrete examples?\n\n"
        f"{signoff}"
    )
    return [
        {"step": 1, "subject": s1, "body_markdown": dm1},
        {"step": 2, "subject": s1, "body_markdown": dm2},  # same thread, subject repeated
        {"step": 3, "subject": s3, "body_markdown": dm3},  # fresh subject, not "Re:"
    ]


def _draft_demo(brand: dict[str, Any], creator: dict[str, Any]) -> dict[str, Any]:
    # Greeting is a neutral "Hi" with no name (handles are channel/page names,
    # not first names) - AICROPS canon. AICROPS drafts all three messages here;
    # schedule_sequence then assigns the send-times.
    messages = _compose_messages(_brand_name(brand), _niche_phrase(creator))
    return {
        "subject": messages[0]["subject"],
        "body_markdown": messages[0]["body_markdown"],
        "messages": messages,
        "estimated_response_rate": 0.21,
        "personalisation_signals": ["niche match", "audience fit", "creative control"],
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


_SEND_DATES = [
    "2026-06-08T09:00:00Z", "2026-06-11T09:00:00Z",
    "2026-06-16T09:00:00Z", "2026-06-22T09:00:00Z",
]


def _sequence_demo(creator_id: str, initial: dict[str, Any], follow_ups: int) -> dict[str, Any]:
    # Prefer the three messages drafted by draft_outreach. If they did not come
    # through (e.g. the agent passed only the first draft), rebuild distinct
    # follow-ups from the brand name in the subject - never a templated nudge.
    messages = initial.get("messages")
    if not messages:
        subject = initial.get("subject", "") or "A collaboration idea"
        name = subject.replace("collaboration", "").strip() or None
        if name and name.lower() in {"a", "our", "the"}:
            name = None
        messages = _compose_messages(name, "your content")
        messages[0]["subject"] = subject
        messages[0]["body_markdown"] = initial.get("body_markdown") or messages[0]["body_markdown"]

    wanted = 1 + max(0, min(follow_ups, len(messages) - 1))
    steps = []
    for i, m in enumerate(messages[:wanted]):
        steps.append({
            "step": m.get("step", i + 1),
            "scheduled_at": _SEND_DATES[min(i, len(_SEND_DATES) - 1)],
            "subject": m.get("subject"),
            "body_markdown": m.get("body_markdown"),
        })
    return {
        "sequence_id": f"seq-{creator_id[:8]}",
        "steps": steps,
        "total_messages": len(steps),
    }
