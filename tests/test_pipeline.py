import os

os.environ.setdefault("DEMO_MODE", "true")

import pytest

from concierge.grounding import ground_taxonomy
from concierge.pipeline import run_pipeline, stream_pipeline


@pytest.mark.asyncio
async def test_grounding_maps_books_brand_to_canonical_niche():
    g = await ground_taxonomy("indie fiction audiobook subscription, design-led, adult readers")
    assert g["backend"] in {"local_corpus", "gemini_enterprise_search", "local_corpus_fallback"}
    # Top canonical niche for an indie-fiction brand must be BOOKS_LITERATURE.
    assert g["categories"][0] == "BOOKS_LITERATURE"
    # Every returned enum must be a real taxonomy entry (no hallucination).
    assert all(r["doc_id"] for r in g["results"])


@pytest.mark.asyncio
async def test_stream_pipeline_emits_tools_in_order():
    events = [
        ev
        async for ev in stream_pipeline(
            "https://chapterhouse.demo", "100 trial signups per month", 5000, creator_limit=3
        )
    ]

    # Collect tool-call names in emission order.
    called = []
    for ev in events:
        for tc in ev.get("tool_calls") or []:
            called.append(tc["name"])

    # Canonical order: research → ground → match → (enrich×3) → (draft+schedule)×3 → crm.
    assert called[0] == "research_brand"
    assert called[1] == "ground_taxonomy"
    assert called[2] == "match_creators"
    assert called.count("enrich_creator") == 3
    assert called.count("draft_outreach") == 3
    assert called.count("schedule_sequence") == 3
    assert called[-1] == "crm_upsert"

    # A final structured summary must be emitted.
    summary = next(ev["data"] for ev in events if ev.get("type") == "summary_data")
    assert summary["brand"] == "Chapterhouse"
    assert summary["drafts_ready"] == 3
    assert len(summary["creators"]) == 3
    # Demo CRM record is synthetic - not written to production.
    assert summary["crm"]["written"] is False
    assert summary["crm"]["company_name"] == "Chapterhouse"
    assert "BOOKS_LITERATURE" in summary["categories"]


@pytest.mark.asyncio
async def test_run_pipeline_returns_summary():
    summary = await run_pipeline(
        "https://chapterhouse.demo", "100 trial signups per month", 5000, creator_limit=2
    )
    assert summary["brand"] == "Chapterhouse"
    assert summary["drafts_ready"] == 2
