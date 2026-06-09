from __future__ import annotations

import ipaddress
import re
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

from concierge.http_client import internal_client
from concierge.settings import get_settings


async def research_brand(brand_url: str, goal: str, budget_monthly_usd: float) -> dict[str, Any]:
    """Research a brand from its public homepage + goal.

    Fetches the brand's homepage and extracts a structured profile (name,
    description, domain) that downstream steps and the taxonomy-grounding step
    consume. Works for any real brand URL.

    Args:
        brand_url: Public-facing URL of the brand (homepage or landing page).
        goal: Plain-English marketing goal (e.g. "100 trial signups per month").
        budget_monthly_usd: Monthly creator budget the brand can commit, in USD.

    Returns:
        dict with keys: ``company`` (name/domain/description), ``icp``, ``geo``,
        ``tone_of_voice``, ``persons``, ``categories`` (left for the grounding
        step to fill with canonical niche enums), ``_source``.
    """
    settings = get_settings()

    # Curated showcase brand keeps a rich, book-themed profile for the demo preset.
    if "chapterhouse.demo" in brand_url:
        return _chapterhouse(brand_url, goal, budget_monthly_usd)

    # Optional live AIBMR backend.
    if settings.aibmr_base_url and not settings.demo_mode:
        async with internal_client(settings.aibmr_base_url) as http:
            resp = await http.post(
                "/recon",
                json={"brand_url": brand_url, "goal": goal, "budget_monthly_usd": budget_monthly_usd},
            )
            resp.raise_for_status()
            return resp.json()

    try:
        return await _fetch_profile(brand_url, goal, budget_monthly_usd)
    except Exception as exc:  # never hard-fail the pipeline
        return _minimal_profile(brand_url, goal, budget_monthly_usd, note=str(exc)[:120])


def _is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    for info in infos:
        ip = info[4][0]
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return False
    return True


async def _fetch_profile(brand_url: str, goal: str, budget: float) -> dict[str, Any]:
    parsed = urlparse(brand_url if "://" in brand_url else "https://" + brand_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("unsupported URL")
    if not _is_public_host(parsed.hostname):  # SSRF guard
        raise ValueError("non-public host blocked")

    url = parsed.geturl()
    async with httpx.AsyncClient(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; cashtime-concierge/1.0)"},
    ) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        html = resp.text[:200_000]

    def meta(prop: str) -> str | None:
        for pat in (
            rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{prop}["\']',
        ):
            m = re.search(pat, html, re.I)
            if m:
                return _clean(m.group(1))
        return None

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = _clean(title_m.group(1)) if title_m else None
    title_head = re.split(r"\s[|–—·:\-]\s", title)[0].strip() if title else None
    name = meta("og:site_name") or title_head \
        or parsed.hostname.replace("www.", "").split(".")[0].title()
    description = (
        meta("og:description")
        or meta("description")
        or meta("twitter:description")
        or _first_text(html)
        or title
        or name
    )

    return {
        "company": {
            "name": name,
            "domain": f"{parsed.scheme}://{parsed.hostname}",
            "description": description,
        },
        "icp": {"audience": "", "psychographics": [], "geo_priority": []},
        "geo": [],
        "tone_of_voice": "",
        "persons": [],
        "categories": [],  # filled by the taxonomy-grounding step
        "_source": {"kind": "live_fetch", "url": url, "goal": goal, "budget_monthly_usd": budget},
    }


def _minimal_profile(brand_url: str, goal: str, budget: float, note: str = "") -> dict[str, Any]:
    parsed = urlparse(brand_url if "://" in brand_url else "https://" + brand_url)
    host = parsed.hostname or brand_url
    name = host.replace("www.", "").split(".")[0].title()
    return {
        "company": {"name": name, "domain": brand_url,
                    "description": f"{name} — {goal}".strip(" —")},
        "icp": {"audience": "", "psychographics": [], "geo_priority": []},
        "geo": [],
        "tone_of_voice": "",
        "persons": [],
        "categories": [],
        "_source": {"kind": "minimal", "note": note, "goal": goal},
    }


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:600]


def _first_text(html: str) -> str | None:
    body = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html)
    text = _clean(body)
    return text[:400] if len(text) > 60 else None


def _chapterhouse(brand_url: str, goal: str, budget: float) -> dict[str, Any]:
    return {
        "company": {
            "name": "Chapterhouse",
            "domain": brand_url,
            "description": (
                "Curated indie-fiction audiobook subscription, $15/mo. Founded 2025, "
                "based in Berlin. Catalog of ~120 independent novels narrated by their "
                "authors. Strong design-led brand. Distribution: web + iOS + Android."
            ),
            "pricing_model": "subscription",
            "monthly_price_usd": 15,
        },
        "icp": {
            "audience": "adult fiction readers, 25–45",
            "psychographics": ["values craft", "anti-bestseller fatigue", "design-conscious"],
            "geo_priority": ["US", "GB", "DE"],
        },
        "geo": ["US", "GB", "DE"],
        "tone_of_voice": "literary, warm, slightly bookish, never hype",
        "persons": [
            {"name": "Demo Founder", "role": "CEO", "email": "founder@chapterhouse.demo", "verified": True},
        ],
        "categories": ["BOOKS_LITERATURE", "ART_DESIGN"],
        "_source": {"kind": "showcase", "goal": goal, "budget_monthly_usd": budget},
    }
