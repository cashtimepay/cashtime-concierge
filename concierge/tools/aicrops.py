from __future__ import annotations

from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def schedule_sequence(
    creator_id: str,
    initial_draft: dict[str, Any],
    follow_up_count: int = 2,
) -> dict[str, Any]:
    """Schedule a 3-step outreach sequence for a creator via AICROPS.

    The sequence consists of the initial message (already drafted by AIBMO),
    plus ``follow_up_count`` follow-ups generated with timing offsets that
    AICROPS picks based on historical CashTime response curves.

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
        return _demo_payload(creator_id, initial_draft, follow_up_count)

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


def _demo_payload(creator_id: str, initial: dict[str, Any], follow_ups: int) -> dict[str, Any]:
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
