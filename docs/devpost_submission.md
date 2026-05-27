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

CashTime Brand Concierge is a customer-facing ADK agent. The brand owner
gives it a homepage URL, a goal, and a monthly budget; in one streamed
conversation it runs six tools:

1. `research_brand` — extracts description, ICP, geo, tone-of-voice,
   decision-makers from the homepage.
2. `match_creators` — ranks 10–15 creators from CashTime's ~4.7k database.
3. `enrich_creator` — refreshes contact and metrics per shortlist.
4. `draft_outreach` — tone-matched first email per creator.
5. `schedule_sequence` — 3-step sequence (initial + 2 follow-ups) timed
   against historical response curves.
6. `crm_upsert` — Twenty CRM upsert: Company + Persons + Opportunity,
   creators linked.

SSE-streamed; the Next.js UI renders each tool call live, ending in a
creator table, expandable drafts, and a CRM deep link. The six tools are
thin MCP wrappers over existing CashTime services behind one MCP gateway.

## Technologies used

- **Gemini 3.1 Pro Preview** — planner LLM.
- **Gemini 3.5 Flash** — worker LLM for drafts/summaries.
- **Google Agent Development Kit (ADK)** — agent + tool routing.
- **Gemini Enterprise Agent Platform** — model serving (europe-west6).
- **Model Context Protocol (MCP)** — single trusted tool boundary.
- **Cloud Run** — Concierge service + Next.js Brand UI.
- **Cloud IAP** — judges-only access.
- **Cloud Build + Artifact Registry + Secret Manager** — CI/CD + secrets.
- **OpenTelemetry → Cloud Trace + Cloud Logging** — full waterfall per session.
- **FastAPI + sse-starlette** — streaming server.
- **Twenty CRM** — system of record.

## Data sources

CashTime internal:
- **Creator database** — ~4,785 vetted creators × 40 niches, with per-
  platform handles, follower counts, engagement, verified emails, content
  language, last-post timestamps.
- **Canonical taxonomies** — 40-niche enum; 10-platform map (YT, IG,
  TikTok, X, Substack, Patreon, Ko-fi, Spotify, Apple Podcasts, LinkedIn);
  40×10×7 keyword dictionary (~2,800 bins); language and country refs;
  468-entry niche→sub-niche map; tone-of-voice dictionary; 8-domain MCN
  registry for manager-email detection.
- **Anonymised response curves** (niche × platform × step).
- **Twenty CRM** (`crm.cashtimepay.com`) — system of record.

External APIs:
- **YouTube Data API v3** — channel statistics.
- **Substack public API** — publication metadata, post cadence.
- **Spotify Web API** + **Apple Podcasts iTunes Lookup** — podcaster metadata.
- **GitHub REST API** — OSS-creator repo statistics.
- **Influencer's Club Discovery + Enrichment API** — creator discovery +
  contact enrichment across 11 platforms.
- **Hunter.io** + **NeverBounce** — email discovery + verification fallback.
- **Public brand homepage** — read by `research_brand`.

Demo brand "Chapterhouse" is synthetic.

## Findings and learnings

- **MCP is the win.** Concierge stays small because the heavy lifting
  lives behind one MCP boundary; new capability = one tool registration.
- **Planner separation matters.** Splitting Gemini 3.1 Pro Preview
  (planner) from Gemini 3.5 Flash (workers) cut average end-to-end
  latency ~38% in smoke tests without quality loss.
- **Demo mode pays for itself.** `DEMO_MODE=true` stubs every tool — UI
  shipped before live wrappers, judges replay without burning quota.
- **Tone-of-voice is the lever.** Biggest draft-quality jump came from
  passing `research_brand`'s tone-of-voice string verbatim into
  `draft_outreach`, not from prompt engineering the drafter.

## Third-party integrations

- **GCP** (Cloud ToS): Gemini Enterprise Agent Platform, Cloud Run, Cloud
  Build, Artifact Registry, Secret Manager, Cloud Trace, Cloud Logging,
  Cloud IAP, Compute Engine. ADK is Apache-2.0, used as published.
- **Cloudflare Access** (Enterprise) fronts internal services; agent uses
  service token `cashtime-agents`.
- **Twenty CRM** (AGPL-3.0), self-hosted on a Compute Engine VM.
- **Paid contracts** (active subscriptions, within rate limits):
  **Hunter.io**, **NeverBounce**, **Influencer's Club Discovery +
  Enrichment API**.
- **Public APIs under each provider's ToS**: YouTube Data API v3 (project
  key, quota-compliant), Substack (public endpoints, robots.txt respected),
  Spotify Web API (dev credentials, podcast metadata only), Apple Podcasts
  iTunes Lookup (open public), GitHub REST API (public + token).

No data scraped against ToS. The creator database is CashTime's own asset,
sourced from the platform APIs above and the signup consent flow. Rights
and authorisation confirmed for every source used.

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
