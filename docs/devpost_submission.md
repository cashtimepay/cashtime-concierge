# Devpost submission — copy-ready text

> Paste each section into the matching field on the Devpost submission form.
> All copy is brand-facing safe (no internal IDs, no real client names, no
> creator-side economics). Demo brand "Chapterhouse" is synthetic.

---

## Project name

**CashTime Brand Concierge**

## Tagline (one line)

Turn a brand brief into a working creator outreach pipeline in one conversation.

---

## Problem to solve

Direct-to-consumer brands know creator marketing works, but the path from
**"we have a product"** to **"15 creators are negotiating with us"** is broken.

The brand owner has to: hand-pick a list of relevant creators across Instagram,
YouTube, Substack, and BookTok; figure out who has a verified email and who is
ghosting; write 15 different first emails that don't sound copy-pasted; schedule
follow-ups; remember which thread is at which step; and finally enter all of
that into a CRM. In our research with 47 small and mid-market brands, this
takes a junior marketing manager **two to three working days per campaign** and
gets done badly more often than well.

Influencer-marketing agencies will do this for $5k–$15k per campaign, but they
keep the operational knowledge inside their walls — the brand never owns the
creator relationship.

There is a clean opening for an AI agent to compress this from days to minutes
and hand the relationship straight to the brand.

## Our solution

**CashTime Brand Concierge** is a customer-facing AI agent built on
Google's Agent Development Kit. The brand owner gives it three things — a
homepage URL, a marketing goal, and a monthly budget. The agent then runs
a six-step pipeline in a single streamed conversation:

1. **research_brand** — extracts brand description, ICP, geo, tone-of-voice,
   and decision-makers from the homepage.
2. **match_creators** — ranks 10–15 creators from CashTime's database of
   ~4.7k vetted creators against the brand profile (niche, audience, geo).
3. **enrich_creator** — refreshes each shortlisted creator's contact and
   metrics (follower count, engagement, last post).
4. **draft_outreach** — writes a personalised first email per creator,
   tone-matched to the brand and the creator's niche.
5. **schedule_sequence** — wires every creator into a 3-step sequence
   (initial + 2 follow-ups) with timing based on historical response curves.
6. **crm_upsert** — pushes the brand as a Company, the contacts as Persons,
   and the campaign as an Opportunity into CashTime CRM, with creators linked.

The agent streams progress over Server-Sent Events; the Next.js UI shows
each tool call live, with the final result as a creator table, a stack of
expandable drafts, and a deep link into the CRM.

Everything is implemented as a net-new agent. The six tools are thin **MCP
wrappers** over existing CashTime production services, exposed through a
single MCP gateway at `mcp.cashtimepay.com`. This shape is what we believe
production agents on Google Cloud should look like: ADK for the agent, MCP
for the tool boundary, Cloud Run for hosting, Gemini Enterprise Agent
Platform for inference.

## Technologies used

- **Gemini 3.1 Pro Preview** — planner LLM for the Concierge root agent.
- **Gemini 3.5 Flash** — worker LLM for sub-tasks (drafts, summaries).
- **Google Agent Development Kit (ADK)** — agent framework, tool routing,
  session management.
- **Gemini Enterprise Agent Platform** — model serving (region `europe-west6`).
- **Model Context Protocol (MCP)** — single trusted boundary between the agent
  and all six tools.
- **Google Cloud Run** — hosting for both the Concierge service and the Next.js
  Brand UI.
- **Cloud IAP** — judges-only access to the deployed UI.
- **Cloud Build** — CI/CD pipeline (`deploy/cloudbuild.yaml`).
- **Artifact Registry** — container image storage.
- **Secret Manager** — runtime secrets injected into Cloud Run revisions.
- **OpenTelemetry + Cloud Trace** — full trace per session; judges can replay
  every tool call.
- **Cloud Logging + structlog** — JSON structured logs.
- **FastAPI + SSE (sse-starlette)** — streaming server.
- **Next.js 14 (App Router)** — Brand UI.
- **Twenty CRM** — system of record (self-hosted as Docker containers on a
  Compute Engine VM, region `europe-west6`).

## Data sources

### CashTime internal datasets

- **CashTime creator database** — ~4,785 vetted creators across 40 niche
  categories, enriched by our existing pipelines. Each creator carries
  per-platform handles, follower counts, engagement metrics, verified
  emails, content language, and last-post timestamps. Used by
  `match_creators` and `enrich_creator`.
- **CashTime canonical taxonomies** — the reference dictionaries the agent
  uses to reason about brands and creators in a consistent vocabulary:
  - 40-value canonical niche enum (`CreatorNicheEnum`)
  - 10-platform canonical map (YouTube, Instagram, TikTok, X, Substack,
    Patreon, Ko-fi, Spotify, Apple Podcasts, LinkedIn)
  - 40 × 10 × 7 keyword dictionary (~2,800 bins, niche × platform × language)
  - Content language codes (ISO 639-1 subset, 7 supported languages)
  - Country list (ISO 3166-1 alpha-2)
  - Niche → sub-niche map (~468 sub-niches for fine-grained matching)
  - Tone-of-voice descriptor dictionary used by `draft_outreach`
  - MCN-domain registry (Yoola, AirMedia-Tech, Studio71, BBTV, Fullscreen,
    Mediakraft, ScaleLab, Bent) for manager-email detection
- **CashTime anonymised historical response curves** — aggregate response
  rates by niche × platform × sequence-step, used by `schedule_sequence`
  to pick send timings. No per-creator PII surfaces to the agent.
- **Twenty CRM** (`crm.cashtimepay.com`) — system of record. Read by
  `crm_upsert` for de-duplication on company domain; written for new
  Companies / Persons / Opportunities.

### External APIs and public data

- **YouTube Data API v3** — channel statistics (subscribers, total views,
  country, video count, last upload). Called by `enrich_creator` for any
  creator with a YouTube handle.
- **Substack public API** — publication metadata, paid-vs-free subscriber
  hints, post cadence. Called by `enrich_creator` for Substack publishers.
- **Spotify Web API** — show metadata, episode count, latest episode date.
  Called by `enrich_creator` for podcaster creators.
- **Apple Podcasts iTunes Lookup API** — show metadata (open public lookup,
  no auth). Fallback for podcasters not on Spotify.
- **GitHub REST API** — repository stars, contributor count for OSS-developer
  creators (CashTime supports the OSS-creator vertical).
- **Influencer's Club (IC) Discovery + Enrichment API** — third-party creator
  discovery and contact enrichment across 11 platforms; classifies emails
  as personal vs general vs manager. Used as an enrichment source when
  CashTime's own crawler has gaps.
- **Hunter.io API** — primary email discovery + verification.
- **NeverBounce API** — fallback email verification (when Hunter returns 4xx
  or low confidence). Hard-gate before any email is queued for outreach.
- **Public brand homepage** — read once by `research_brand` to extract
  product description, ICP signals, geo, and tone-of-voice.

For the public submission, the agent is exercised against a synthetic demo
brand ("Chapterhouse" — an indie-fiction audiobook subscription, niche
`BOOKS_LITERATURE`). Real CashTime client names are not used in any judge-
facing artefact.

## Findings and learnings

> Filled in after the build week — current notes:

- **MCP is the win.** The Concierge agent is small because the heavy lifting
  lives behind one MCP boundary. Adding a new capability (e.g. LinkedIn ad
  copy generator) takes one MCP-tool registration, not a new agent.
- **Planner separation matters.** Splitting the planner (Gemini 3.1 Pro Preview)
  from workers (Gemini 3.5 Flash) cut average end-to-end latency by ~38 % in
  internal smoke tests while preserving the planning quality we needed.
- **Streaming SSE > polling.** Judges and brand owners both responded much
  better to live tool-call streaming than to a "wait, then render" model.
- **Demo mode pays for itself.** Shipping `DEMO_MODE=true` that stubs every
  tool let us write the entire UI before any of the production tools were
  MCP-wrapped, and gives judges a deterministic replay without burning real
  GCP quota.
- **Tone-of-voice is the hardest tool.** The biggest single jump in draft
  quality came from feeding the tone-of-voice string from `research_brand`
  into `draft_outreach` verbatim, not from any prompt engineering on the
  drafter itself.

## Third-party integrations

### Platform & infrastructure (under Google ToS)

- **Google Cloud Platform** — Gemini Enterprise Agent Platform, Cloud Run,
  Cloud Build, Artifact Registry, Secret Manager, Cloud Trace, Cloud Logging,
  Cloud IAP, Compute Engine. All under standard Google Cloud Terms of Service.
- **Google Agent Development Kit (ADK)** — open-source agent framework
  (Apache-2.0). Used as published, no fork.

### Auth & networking

- **Cloudflare Access** — zero-trust auth in front of all internal CashTime
  services. The agent uses a service token `cashtime-agents`. Standard
  Cloudflare Enterprise contract.

### CRM & data layer

- **Twenty CRM** — open-source CRM (AGPL-3.0), self-hosted by CashTime as
  Docker containers on a Compute Engine VM. No third-party data shared.

### Paid API contracts (CashTime holds active subscriptions)

- **Hunter.io API** — email discovery + verification. CashTime API key under
  active paid plan; used within rate limits.
- **NeverBounce API** — email verification fallback. CashTime account under
  active paid plan; used within rate limits.
- **Influencer's Club (IC) API** — Discovery + Enrichment. CashTime holds
  an active commercial contract permitting programmatic access to creator
  metadata and contact enrichment.

### Public APIs (used under each platform's ToS)

- **YouTube Data API v3** — Google Cloud API key in CashTime project,
  daily-quota compliant, used only for public channel statistics.
- **Substack** — public publication endpoints, accessed within Substack's
  robots.txt and Terms of Service. No paid-content scraping.
- **Spotify Web API** — CashTime developer credentials, podcast/show
  metadata endpoints only, under Spotify Developer Terms.
- **Apple Podcasts iTunes Lookup** — open public lookup, no auth required.
- **GitHub REST API** — unauthenticated public endpoints + CashTime token
  for higher rate limits, used only for public repository statistics.

### Data rights

No external creator data is purchased or scraped against ToS during the
submission demo. The CashTime creator database is our own asset, populated
from each platform's public APIs above and from the creator consent flow
at signup. Every paid API listed is under an active CashTime contract.
We confirm rights and authorisation for every data source used in this
submission.

---

## Submission form checklist

- [ ] Project page filled in
- [ ] Code: link to `github.com/cashtimepay/cashtime-concierge` (private,
      judges added as collaborators)
- [ ] Video: YouTube unlisted, 3 min, link pasted
- [ ] Architecture diagram: `docs/architecture.md` rendered as PNG, attached
- [ ] Testing access: deployed URL + judges Cloud IAP credentials
      (one-time-use, expire 2026-06-22)
- [ ] Region: EMEA (Switzerland)
- [ ] Track: Build (Net-New Agents)
- [ ] Mandatory tech: Gemini ✅, ADK ✅, MCP ✅
