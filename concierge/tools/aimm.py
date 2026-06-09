from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from concierge.http_client import internal_client
from concierge.settings import get_settings

_SAMPLE_PATH = Path(__file__).parent.parent / "data" / "creator_sample.json"


@lru_cache
def _sample() -> list[dict[str, Any]]:
    return json.loads(_SAMPLE_PATH.read_text(encoding="utf-8")).get("creators", [])


def _creator_id(handle: str, niche: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", handle.lower()).strip("-")[:32]
    return f"smp-{niche.lower()}-{slug}" if slug else f"smp-{niche.lower()}"


async def match_creators(
    brand_profile: dict[str, Any],
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Match creators to a brand profile from the CashTime creator network.

    Ranks creators whose niche matches the brand's grounded categories, by
    follower reach and geo/niche fit. The pool is a curated, public-safe sample
    of real CashTime creators (handle / niche / followers / geo only - no
    contact details or economics).

    Args:
        brand_profile: Output of ``research_brand`` (after taxonomy grounding).
            Uses ``categories`` (canonical niche enums) and ``geo``.
        limit: Number of top creators to return. Capped at 25.

    Returns:
        A list of creators ordered by fit, each with ``creator_id``, ``handle``,
        ``platform``, ``niche``, ``follower_count``, ``engagement_percent``,
        ``geo``, ``fit_score`` (0..1), ``fit_reasons``.
    """
    settings = get_settings()
    limit = max(1, min(limit, 25))

    # Optional: a live AI-MM backend can override the sample if configured.
    if settings.aimm_base_url and not settings.demo_mode:
        async with internal_client(settings.aimm_base_url) as http:
            resp = await http.post("/match", json={"brand_profile": brand_profile, "limit": limit})
            resp.raise_for_status()
            return resp.json().get("creators", [])

    cats = [c for c in (brand_profile.get("categories") or []) if c]
    geos = [g for g in (brand_profile.get("geo") or []) if g]
    pool = _sample()

    matched = [c for c in pool if c.get("niche") in cats] if cats else []
    if not matched:  # no niche hit → widen to the whole network so we never return empty
        matched = pool

    def fit(c: dict[str, Any]) -> float:
        s = 0.55
        niche = c.get("niche")
        if cats and niche == cats[0]:
            s += 0.25
        elif niche in cats:
            s += 0.15
        if geos and c.get("geo") in geos:
            s += 0.08
        s += min(0.12, math.log10(max(c.get("follower_count") or 1, 10)) / 100)
        return round(min(s, 0.99), 2)

    def reasons(c: dict[str, Any]) -> list[str]:
        r = []
        if c.get("niche") in cats:
            r.append(f"{c['niche'].replace('_', ' ').title()} niche match")
        if geos and c.get("geo") in geos:
            r.append(f"{c['geo']} audience")
        if (c.get("follower_count") or 0) >= 100_000:
            r.append("high reach")
        return r or ["network fit"]

    ranked = sorted(matched, key=lambda x: x.get("follower_count") or 0, reverse=True)[:limit]
    return [
        {
            "creator_id": _creator_id(c.get("handle", ""), c.get("niche", "")),
            "handle": c.get("handle"),
            "platform": c.get("platform"),
            "niche": c.get("niche"),
            "follower_count": c.get("follower_count"),
            "engagement_percent": c.get("engagement_percent"),
            "geo": c.get("geo"),
            "fit_score": fit(c),
            "fit_reasons": reasons(c),
        }
        for c in ranked
    ]
