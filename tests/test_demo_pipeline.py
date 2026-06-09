import os

os.environ.setdefault("DEMO_MODE", "true")

import pytest

from concierge.tools import (
    crm_upsert,
    draft_outreach,
    enrich_creator,
    match_creators,
    research_brand,
    schedule_sequence,
)


@pytest.mark.asyncio
async def test_full_demo_pipeline():
    profile = await research_brand(
        brand_url="https://chapterhouse.demo",
        goal="100 trial signups per month",
        budget_monthly_usd=5000,
    )
    assert profile["company"]["name"] == "Chapterhouse"
    assert "BOOKS_LITERATURE" in profile["categories"]

    creators = await match_creators(profile, limit=3)
    assert 1 <= len(creators) <= 3
    assert all(c["fit_score"] > 0 for c in creators)

    enriched = await enrich_creator(creator_id="demo-uuid")
    assert enriched["email_verified"] is True

    draft = await draft_outreach(profile, creators[0])
    assert "Chapterhouse" in draft["subject"]

    sequence = await schedule_sequence(creator_id="demo-uuid", initial_draft=draft, follow_up_count=2)
    assert sequence["total_messages"] == 3

    crm = await crm_upsert(brand_profile=profile, creators=creators, sequences=[sequence])
    assert crm["creators_linked"] == len(creators)
    # Demo mode must never claim a production write.
    assert crm["written"] is False
    assert crm["crm_url"] is None
    assert crm["company_name"] == "Chapterhouse"
