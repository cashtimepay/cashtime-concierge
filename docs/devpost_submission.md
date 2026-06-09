# Devpost submission - copy-ready text

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
manager 2-3 days per campaign: shortlist across IG/YouTube/Substack/
BookTok, verify emails, write 15 non-templated first messages, schedule
follow-ups, then re-enter everything into a CRM. Influencer agencies do
this for $5-15k and keep the creator relationship to themselves. Clean
opening for an AI agent to compress days into minutes and hand the
relationship straight to the brand.

## Our solution

CashTime Brand Concierge is an ADK multi-agent system. A planner (Gemini
3.1 Pro Preview) takes URL + goal + budget, and orchestrates three
sub-agents plus a CRM tool:

1. **Research sub-agent** - RAG-grounded via Gemini Enterprise Search over
   CashTime's canonical taxonomies and the brand homepage; outputs
   product, ICP, geo, tone-of-voice, decision-makers.
2. **Matching sub-agent** - ranks 10-15 creators from CashTime's ~4.7k
   database against the brand profile.
3. **Outreach sub-agent** - refreshes each shortlisted creator, drafts a
   tone-matched first email, schedules a 3-step sequence (initial + 2
   follow-ups) timed against historical response curves.
4. `crm_upsert` - planner-level tool: upserts the brand into Twenty CRM
   as Company + Persons + Opportunity with creators linked.

Streamed end-to-end over SSE; the Next.js UI gives each sub-agent its own
live tab - Research (grounded profile), Match (creator table), Outreach
(drafts + schedules), CRM (the record) - so a judge sees exactly what each
agent does. Agents collaborate via MCP over one secured gateway. A human
approves every message; the agent drafts and schedules but never sends.

## Technologies used

- **Gemini 3.1 Pro Preview** - planner LLM.
- **Gemini 3.5 Flash** - sub-agent LLM for drafts/summaries.
- **Google Agent Development Kit (ADK)** - planner + 3 sub-agents.
- **Gemini Enterprise Agents Platform** - Gemini serving, in-project (global endpoint), authenticated
  by the Cloud Run service account (IAM) - no API key, no external gateway.
- **Gemini Enterprise Search** - RAG grounding for the research sub-agent.
- **Model Context Protocol (MCP)** - single trusted tool boundary.
- **Cloud Run** - Concierge service + Next.js Brand UI.
- **Cloud IAP** - judges-only access.
- **Cloud Build + Artifact Registry + Secret Manager** - CI/CD + secrets.
- **OpenTelemetry → Cloud Trace + Cloud Logging** - full waterfall.
- **FastAPI + sse-starlette + Next.js 15** - streaming UI.
- **Twenty CRM** - system of record.

## Data sources

CashTime internal:
- **Creator database** - ~4,785 vetted creators × 40 niches with per-
  platform handles, follower counts, engagement, verified emails, content
  language, last-post timestamps.
- **Canonical taxonomies** - 40-niche enum, 10-platform map, 40×10×7
  keyword dictionary (~2,800 bins), language + country refs, 468-entry
  niche→sub-niche map, tone-of-voice dictionary, MCN-domain registry.
- **Anonymised response curves** (niche × platform × step).
- **Twenty CRM** (`crm.cashtimepay.com`) - system of record.

External APIs (licensing in Third-party integrations): YouTube Data API v3
(channel stats), Substack public API (publication metadata), Spotify Web
API + Apple Podcasts iTunes Lookup (podcasters), GitHub REST API (OSS
repos), Influencer's Club Discovery + Enrichment (creator discovery +
contacts), Hunter.io + NeverBounce (email verification), public brand
homepage (research sub-agent).

Demo brand "Chapterhouse" is synthetic. Planner, sub-agents, MCP
wrappers, Gemini Enterprise Search index, and Brand UI are net-new in the Contest
Period; CashTime backends act as third-party tool endpoints.

## Findings and learnings

- **MCP is the win.** Concierge stays small because heavy lifting lives
  behind one MCP boundary; new capability = one tool registration.
- **Multi-agent ≠ multi-call.** Making each step a real sub-agent (not
  just a sequential tool call) lets each carry its own grounding and model
  tier - planner on Gemini 3.1 Pro Preview for orchestration, sub-agents on
  cheaper 3.5 Flash - and isolates failures to one step.
- **Grounding over our own taxonomies.** Pointing Gemini Enterprise Search at
  CashTime's canonical niche dictionary stops the agent inventing niches -
  it can only emit enum values that exist in our taxonomy.
- **Demo mode pays for itself.** A deterministic twin of the pipeline
  (same tool order, same event stream, no LLM) let the UI ship before live
  wrappers and lets judges replay the full flow with zero auth or quota.
- **Real for any brand, safe by construction.** The public demo researches
  any brand URL live and matches against a curated, public-safe sample of the
  real creator network (handles/niches/followers only) - judges get genuine
  output without exposing contact data, economics, or the full database.

## Third-party integrations

- **GCP** (Cloud ToS): Gemini Enterprise Agent Platform, Gemini Enterprise Search,
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

## Live demo / testing access (no login)

Deployed on Cloud Run (`tools-cashtimepay-com`, europe-west6), demo mode,
synthetic "Chapterhouse" brand - no login, no real data, no emails sent,
nothing written to the production CRM.

- **Brand UI:** https://cashtime-concierge-ui-455884480848.europe-west6.run.app
- **API health:** https://cashtime-concierge-455884480848.europe-west6.run.app/health
- **API / Swagger:** https://cashtime-concierge-455884480848.europe-west6.run.app/docs

Open the UI → click **"Run the Chapterhouse demo"** → watch the four agent tabs
fill in live.

## Submission form checklist

- [x] Code (public): github.com/cashtimepay/cashtime-concierge
- [x] Deployed live demo (URLs above)
- [x] Architecture diagram: `docs/architecture.png`
- [x] Multi-agent + Gemini Enterprise Search grounding shipped
- [x] Region: EMEA (Switzerland)
- [x] Track: Build (Net-New Agents)
- [x] Mandatory tech: Gemini, ADK, MCP
- [ ] **Video** (≤2 min, English, no third-party logos on screen) - TODO
- [ ] Paste this text into the Devpost project page + EMEA regional flag
