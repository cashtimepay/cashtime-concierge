# Devpost submission — copy-ready text

> Hard cap: 5000 characters across the six descriptive fields combined.
> All copy is brand-facing safe (no internal IDs, no real client names, no
> creator-side economics). Demo brand "Chapterhouse" is synthetic.

---

## Project name

**CashTime Brand Concierge**

## Tagline (one line)

Turn a brand brief into a working creator outreach pipeline in one conversation.

---

## Problem to solve

D2C brands know creator marketing works, but turning "we have a product"
into "15 creators are negotiating with us" takes a junior marketing
manager 2–3 days per campaign: shortlist across IG/YouTube/Substack/
BookTok, verify emails, write 15 non-templated first messages, schedule
follow-ups, then re-enter everything into a CRM. Influencer agencies do
this for $5–15k and keep the creator relationship to themselves. Clean
opening for an AI agent to compress days into minutes and hand the
relationship straight to the brand.

## Our solution

CashTime Brand Concierge is an ADK multi-agent system. A planner (Gemini
3.1 Pro Preview) takes URL + goal + budget, and orchestrates three
sub-agents plus a CRM tool:

1. **Research sub-agent** — RAG-grounded via Vertex AI Search over
   CashTime's canonical taxonomies and the brand homepage; outputs
   product, ICP, geo, tone-of-voice, decision-makers.
2. **Matching sub-agent** — ranks 10–15 creators from CashTime's ~4.7k
   database against the brand profile.
3. **Outreach sub-agent** — refreshes each shortlisted creator, drafts a
   tone-matched first email, schedules a 3-step sequence (initial + 2
   follow-ups) timed against historical response curves.
4. `crm_upsert` — planner-level tool: upserts the brand into Twenty CRM
   as Company + Persons + Opportunity with creators linked.

Streamed end-to-end; the Next.js UI renders each sub-agent's tool calls
live via SSE, ending in a creator table, expandable drafts, and a CRM
deep link. Agents collaborate via MCP over one secured gateway.

## Technologies used

- **Gemini 3.1 Pro Preview** — planner LLM.
- **Gemini 3.5 Flash** — sub-agent LLM for drafts/summaries.
- **Google Agent Development Kit (ADK)** — planner + 3 sub-agents.
- **Gemini Enterprise Agent Platform** — model serving (europe-west6).
- **Vertex AI Search** — RAG grounding for the research sub-agent.
- **Model Context Protocol (MCP)** — single trusted tool boundary.
- **Cloud Run** — Concierge service + Next.js Brand UI.
- **Cloud IAP** — judges-only access.
- **Cloud Build + Artifact Registry + Secret Manager** — CI/CD + secrets.
- **OpenTelemetry → Cloud Trace + Cloud Logging** — full waterfall.
- **FastAPI + sse-starlette + Next.js 14** — streaming UI.
- **Twenty CRM** — system of record.

## Data sources

CashTime internal:
- **Creator database** — ~4,785 vetted creators × 40 niches with per-
  platform handles, follower counts, engagement, verified emails, content
  language, last-post timestamps.
- **Canonical taxonomies** — 40-niche enum, 10-platform map, 40×10×7
  keyword dictionary (~2,800 bins), language + country refs, 468-entry
  niche→sub-niche map, tone-of-voice dictionary, MCN-domain registry.
- **Anonymised response curves** (niche × platform × step).
- **Twenty CRM** (`crm.cashtimepay.com`) — system of record.

External APIs (licensing in Third-party integrations): YouTube Data API v3
(channel stats), Substack public API (publication metadata), Spotify Web
API + Apple Podcasts iTunes Lookup (podcasters), GitHub REST API (OSS
repos), Influencer's Club Discovery + Enrichment (creator discovery +
contacts), Hunter.io + NeverBounce (email verification), public brand
homepage (research sub-agent).

Demo brand "Chapterhouse" is synthetic. Planner, sub-agents, MCP
wrappers, Vertex AI Search index, and Brand UI are net-new in the Contest
Period; CashTime backends act as third-party tool endpoints.

## Findings and learnings

- **MCP is the win.** Concierge stays small because heavy lifting lives
  behind one MCP boundary; new capability = one tool registration.
- **Multi-agent ≠ multi-call.** Sub-agents (not just sequential tool
  calls) let each carry its own grounding and model — planner on Gemini
  3.1 Pro Preview, sub-agents on 3.5 Flash. Latency dropped ~38%.
- **Grounding over our own taxonomies.** Pointing Vertex AI Search at
  CashTime's canonical dictionaries gave bigger draft-quality gains than
  any prompt edit.
- **Demo mode pays for itself.** Stubbing every tool let the UI ship
  before live wrappers, and judges replay deterministically without
  burning paid-API quota.

## Third-party integrations

- **GCP** (Cloud ToS): Gemini Enterprise Agent Platform, Vertex AI Search,
  Cloud Run, Cloud Build, Artifact Registry, Secret Manager, Cloud Trace,
  Cloud Logging, Cloud IAP, Compute Engine. ADK is Apache-2.0, used as
  published.
- **Cloudflare Access** (Enterprise) fronts internal services; agent uses
  service token `cashtime-agents`.
- **Twenty CRM** (AGPL-3.0), self-hosted on a Compute Engine VM.
- **Paid contracts** (active, within rate limits): Hunter.io, NeverBounce,
  Influencer's Club Discovery + Enrichment API.
- **Public APIs** under each provider's ToS: YouTube Data API v3, Substack
  (robots.txt respected), Spotify Web API, Apple Podcasts iTunes Lookup,
  GitHub REST API.

No data scraped against ToS. The creator database is CashTime's own asset,
sourced from the APIs above + the signup consent flow. Rights and
authorisation confirmed for every source.

---

## Submission form checklist

- [ ] Project page filled in
- [ ] Code: github.com/cashtimepay/cashtime-concierge (judges as collaborators)
- [ ] Video: YouTube unlisted, 3 min
- [ ] Architecture diagram: `docs/architecture.md` rendered as PNG
- [ ] Testing access: deployed URL + Cloud IAP credentials (one-time-use,
      expire 2026-06-22)
- [ ] Region: EMEA (Switzerland)
- [ ] Track: Build (Net-New Agents)
- [ ] Mandatory tech: Gemini ✅, ADK ✅, MCP ✅
