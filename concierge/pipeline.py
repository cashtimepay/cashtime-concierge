"""Deterministic pipeline orchestrator (demo / offline replay).

The live product path is the ADK multi-agent stack in ``concierge.agents``,
driven by Gemini. That path needs Gemini Enterprise Agents Platform credentials and a model call per
step, which judges cannot run locally.

This module is the **deterministic twin**: it executes the exact same six-tool
pipeline (research → ground → match → enrich → draft → schedule → crm) in a
fixed order, with no LLM in the loop, emitting the *same* event shape the ADK
server emits. It powers:

* ``DEMO_MODE=true`` local replay (``judges_access.md`` quick-start),
* the integration test,
* a reliable fallback if the model path is unavailable.

Every step streams a ``tool_call`` event then a ``tool_result`` event, plus a
short human-readable ``text`` narration line, so the Brand UI renders identical
output whether the run is model-driven or deterministic.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from concierge.grounding import ground_taxonomy
from concierge.tools.aibmo import draft_outreach
from concierge.tools.aibmr import research_brand
from concierge.tools.aicrops import schedule_sequence
from concierge.tools.aimm import match_creators
from concierge.tools.cren import enrich_creator
from concierge.tools.twenty import crm_upsert


def _event(kind: str, *, text: str | None = None, tool_calls=None, tool_results=None) -> dict:
    return {
        "type": kind,
        "text": text,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
    }


def _call(name: str, args: dict) -> dict:
    return _event("tool_call", tool_calls=[{"name": name, "args": args}])


def _result(name: str, response: Any) -> dict:
    payload = response if isinstance(response, dict) else {"value": response}
    return _event("tool_result", tool_results=[{"name": name, "response": payload}])


def _grounding_query(profile: dict[str, Any]) -> str:
    company = profile.get("company", {})
    icp = profile.get("icp", {})
    parts = [
        company.get("name", ""),
        company.get("description", ""),
        company.get("pricing_model", ""),
        icp.get("audience", ""),
        " ".join(icp.get("psychographics", []) or []),
        profile.get("tone_of_voice", ""),
    ]
    return ", ".join(p for p in parts if p).strip()


async def stream_pipeline(
    brand_url: str,
    goal: str,
    budget_monthly_usd: float,
    *,
    creator_limit: int = 15,
) -> AsyncGenerator[dict, None]:
    """Run the full pipeline deterministically, yielding UI events in order."""

    yield _event("text", text=f"Brief received for {brand_url}. Running the pipeline…")

    # 1) Research --------------------------------------------------------------
    yield _call("research_brand", {"brand_url": brand_url, "goal": goal,
                                   "budget_monthly_usd": budget_monthly_usd})
    profile = await research_brand(brand_url, goal, budget_monthly_usd)
    yield _result("research_brand", profile)
    company = profile.get("company", {})
    yield _event("text", text=(
        f"Researched {company.get('name', 'the brand')} - "
        f"{company.get('pricing_model', 'n/a')} model, "
        f"target geo {', '.join(profile.get('geo', []) or [])}."
    ))

    # 1b) Grounding (RAG over canonical taxonomy) ------------------------------
    gquery = _grounding_query(profile)
    yield _call("ground_taxonomy", {"query": gquery})
    grounding = await ground_taxonomy(gquery)
    yield _result("ground_taxonomy", grounding)
    if grounding.get("categories"):
        profile["categories"] = grounding["categories"]
    profile["grounding_backend"] = grounding.get("backend")
    profile["grounding_citations"] = grounding.get("citations", [])
    yield _event("text", text=(
        f"Grounded against the canonical taxonomy ({grounding.get('backend')}): "
        f"maps to {', '.join(profile['categories'][:3])}."
    ))

    # 2) Match -----------------------------------------------------------------
    yield _call("match_creators", {"categories": profile.get("categories"),
                                   "limit": creator_limit})
    creators = await match_creators(profile, limit=creator_limit)
    yield _result("match_creators", {"creators": creators, "count": len(creators)})
    geos = sorted({c.get("geo") for c in creators if c.get("geo")})
    yield _event("text", text=(
        f"Matched {len(creators)} creators across {', '.join(geos) or 'n/a'}."
    ))

    # 3) Enrich each -----------------------------------------------------------
    enriched: list[dict[str, Any]] = []
    for creator in creators:
        cid = creator.get("creator_id") or f"demo-{creator.get('handle', 'creator')}"
        yield _call("enrich_creator", {"creator_id": cid})
        info = await enrich_creator(cid)
        merged = {**creator, **{k: v for k, v in info.items() if v not in (None, "", [])}}
        merged["creator_id"] = cid
        enriched.append(merged)
        yield _result("enrich_creator", info)
    yield _event("text", text=f"Refreshed contact + audience data for {len(enriched)} creators.")

    # 4) Draft + 5) Schedule per creator --------------------------------------
    sequences: list[dict[str, Any]] = []
    for creator in enriched:
        cid = creator["creator_id"]
        yield _call("draft_outreach", {"creator_id": cid, "handle": creator.get("handle")})
        draft = await draft_outreach(profile, creator)
        # Carry the creator identity into the result so the UI can group drafts.
        yield _result("draft_outreach", {**draft, "creator_id": cid, "handle": creator.get("handle")})

        yield _call("schedule_sequence", {"creator_id": cid, "follow_up_count": 2})
        seq = await schedule_sequence(cid, draft, follow_up_count=2)
        seq["creator_id"] = cid
        sequences.append(seq)
        yield _result("schedule_sequence", seq)
    yield _event("text", text=(
        f"Drafted {len(sequences)} personalised first-touch messages and scheduled "
        f"3-step sequences - all awaiting human approval."
    ))

    # 6) CRM upsert ------------------------------------------------------------
    yield _call("crm_upsert", {"company": company.get("name"),
                               "creators": len(enriched)})
    crm = await crm_upsert(brand_profile=profile, creators=enriched, sequences=sequences)
    yield _result("crm_upsert", crm)

    # Final summary ------------------------------------------------------------
    summary = {
        "brand": company.get("name"),
        "categories": profile.get("categories"),
        "geo": profile.get("geo"),
        "grounding_backend": profile.get("grounding_backend"),
        "creators": [
            {
                "handle": c.get("handle"),
                "niche": c.get("niche"),
                "follower_count": c.get("follower_count"),
                "fit_score": c.get("fit_score"),
                "geo": c.get("geo"),
            }
            for c in enriched
        ],
        "drafts_ready": len(sequences),
        "crm": crm,
        "crm_url": crm.get("crm_url"),
    }
    yield _event("summary", text=(
        f"Done. {len(enriched)} creators sourced for {company.get('name')}, "
        f"{len(sequences)} outreach sequences ready for approval. "
        f"CRM record: {crm.get('crm_url')}"
    ))
    yield {"type": "summary_data", "text": None, "tool_calls": None,
           "tool_results": None, "data": summary}


async def run_pipeline(
    brand_url: str,
    goal: str,
    budget_monthly_usd: float,
    *,
    creator_limit: int = 15,
) -> dict[str, Any]:
    """Collect the full deterministic run and return just the final summary."""
    summary: dict[str, Any] = {}
    async for ev in stream_pipeline(brand_url, goal, budget_monthly_usd,
                                    creator_limit=creator_limit):
        if ev.get("type") == "summary_data":
            summary = ev["data"]
    return summary
