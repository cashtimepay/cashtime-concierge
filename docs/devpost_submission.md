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

- **CashTime creator database** — ~4,785 vetted creators across 40 niche
  categories, sourced and enriched by CashTime's existing pipelines from
  public platform data (Instagram, YouTube, Substack, TikTok). Used by
  `match_creators` and `enrich_creator`.
- **Public brand homepage** — read by `research_brand` to extract product
  description, ICP, geo, and tone-of-voice signals.
- **Twenty CRM** (`crm.cashtimepay.com`) — used by `crm_upsert` as the system
  of record. Read for de-duplication on company domain; written for new
  Companies / Persons / Opportunities.
- **CashTime historical response curves** — anonymised aggregate response
  rates used by `schedule_sequence` to pick send timings. No per-creator PII
  surfaces to the agent.

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

- **Twenty CRM** — open-source CRM (AGPL), self-hosted by CashTime.
  No third-party data shared with Twenty.
- **Cloudflare Access** — zero-trust auth in front of all internal CashTime
  services. The agent uses a service token `cashtime-agents`.

No external creator data is purchased or imported during the submission demo;
the creator database is CashTime's own asset, sourced under our standard
public-data terms and the creator consent flow at signup. We confirm rights
and authorisation for every data source used.

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
