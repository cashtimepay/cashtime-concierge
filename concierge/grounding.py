"""Taxonomy grounding for the research sub-agent (Vertex AI Search + RAG).

`ground_taxonomy` is an ADK tool. Given a free-text query describing a brand /
product, it returns the closest **canonical CashTime taxonomy entries** (niches,
platforms, tone descriptors) so the research agent can only ever emit enum
values that actually exist in our taxonomy — no hallucinated niches.

Two backends, selected at runtime:

* **Vertex AI Search** (Discovery Engine) — used when
  ``settings.vertex_search_datastore`` is set and we are not in demo mode. This
  is the production grounding path; the data store is indexed from
  ``data/taxonomy_corpus.json``.
* **Local corpus** — a deterministic keyword retriever over the bundled
  ``data/taxonomy_corpus.json``. Used offline, in tests and in demo mode so the
  full pipeline runs without any GCP auth.

This module deliberately does NOT import ADK or google-genai so it can be unit
tested in isolation.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from concierge.settings import get_settings

_CORPUS_PATH = Path(__file__).parent / "data" / "taxonomy_corpus.json"
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@lru_cache
def _load_corpus() -> list[dict[str, Any]]:
    data = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    return data.get("documents", [])


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _score(query_tokens: set[str], doc: dict[str, Any]) -> float:
    """Weighted keyword overlap between a query and a taxonomy document.

    Deterministic, dependency-free; good enough for grounding over a small
    curated corpus and stable for tests.
    """
    if not query_tokens:
        return 0.0
    kw = _tokenize(" ".join(doc.get("keywords", [])))
    sub = _tokenize(" ".join(doc.get("sub_niches", [])))
    title = _tokenize(doc.get("title", ""))
    body = _tokenize(doc.get("text", ""))
    enum = _tokenize(doc.get("enum", ""))

    score = (
        3.0 * len(query_tokens & kw)
        + 2.5 * len(query_tokens & enum)
        + 2.0 * len(query_tokens & sub)
        + 2.0 * len(query_tokens & title)
        + 1.0 * len(query_tokens & body)
    )
    # Normalise by query size so long queries don't dominate.
    return score / (len(query_tokens) ** 0.5)


def _local_search(query: str, top_k: int) -> list[dict[str, Any]]:
    qt = _tokenize(query)
    scored = []
    for doc in _load_corpus():
        s = _score(qt, doc)
        if s > 0:
            scored.append((s, doc))
    scored.sort(key=lambda x: (x[0], x[1]["enum"]), reverse=True)
    out = []
    for s, doc in scored[:top_k]:
        out.append(
            {
                "enum": doc["enum"],
                "type": doc["type"],
                "title": doc["title"],
                "snippet": doc.get("text", ""),
                "score": round(s, 4),
                "doc_id": doc["id"],
            }
        )
    return out


def _vertex_search(query: str, top_k: int) -> list[dict[str, Any]]:
    """Query the Vertex AI Search (Discovery Engine) data store.

    Imported lazily so the local path never needs the client library.
    """
    from google.cloud import discoveryengine_v1 as de

    settings = get_settings()
    client = de.SearchServiceClient()
    serving_config = (
        f"projects/{settings.google_cloud_project}"
        f"/locations/{settings.vertex_search_location}"
        f"/collections/default_collection"
        f"/dataStores/{settings.vertex_search_datastore}"
        f"/servingConfigs/default_search"
    )
    request = de.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=top_k,
    )
    results: list[dict[str, Any]] = []
    for item in client.search(request).results:
        doc = item.document
        struct = dict(doc.struct_data) if doc.struct_data else {}
        results.append(
            {
                "enum": struct.get("enum", doc.id),
                "type": struct.get("type", "unknown"),
                "title": struct.get("title", ""),
                "snippet": struct.get("text", ""),
                "score": None,
                "doc_id": doc.id,
            }
        )
    return results


async def ground_taxonomy(query: str, top_k: int = 6) -> dict[str, Any]:
    """Ground a brand/product description against CashTime's canonical taxonomy.

    Retrieves the closest canonical niche, platform and tone entries from the
    taxonomy index (Vertex AI Search in production, a bundled corpus offline).
    Use the returned ``categories`` as the brand's canonical niche enums — do
    not invent niche names.

    Args:
        query: A short free-text description of the brand and its product, e.g.
            "indie fiction audiobook subscription, design-led, adult readers".
        top_k: Number of taxonomy entries to retrieve (capped at 12).

    Returns:
        dict with:
        ``backend`` ("vertex_ai_search" or "local_corpus"),
        ``results`` (list of {enum, type, title, snippet, score, doc_id}),
        ``categories`` (canonical niche enums among the results, best first),
        ``platforms`` (canonical platform enums among the results),
        ``tones`` (canonical tone enums among the results),
        ``citations`` (doc ids backing the grounding).
    """
    settings = get_settings()
    top_k = max(1, min(int(top_k), 12))

    backend = "local_corpus"
    results: list[dict[str, Any]] = []
    if settings.vertex_search_datastore and not settings.demo_mode:
        try:
            results = _vertex_search(query, top_k)
            backend = "vertex_ai_search"
        except Exception:
            # Grounding must never hard-fail the pipeline — fall back locally.
            results = _local_search(query, top_k)
            backend = "local_corpus_fallback"
    else:
        results = _local_search(query, top_k)

    categories = [r["enum"] for r in results if r["type"] == "niche"]
    platforms = [r["enum"] for r in results if r["type"] == "platform"]
    tones = [r["enum"] for r in results if r["type"] == "tone"]

    return {
        "backend": backend,
        "query": query,
        "results": results,
        "categories": categories,
        "platforms": platforms,
        "tones": tones,
        "citations": [r["doc_id"] for r in results],
    }
