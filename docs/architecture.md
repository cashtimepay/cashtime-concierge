# Architecture — CashTime Brand Concierge

## High-level diagram

```
┌──────────────────────────┐
│       Brand UI           │  Next.js, Cloud Run, behind Cloud IAP
│  (brief form + SSE log)  │
└────────────┬─────────────┘
             │ POST /concierge/run
             ▼
┌──────────────────────────────────────────────────────────────┐
│                Concierge Agent (this repo)                   │
│  FastAPI + SSE → ADK Runner → root agent                     │
│                                                              │
│  Planner   : Gemini 2.5 Pro     (Vertex AI, europe-west6)    │
│  Workers   : Gemini 2.5 Flash   (Vertex AI, europe-west6)    │
│                                                              │
│  6 tools (MCP-wrapped):                                      │
│    ① research_brand    ② match_creators   ③ enrich_creator   │
│    ④ draft_outreach    ⑤ schedule_sequence ⑥ crm_upsert     │
└────┬─────────┬─────────┬─────────┬──────────┬────────┬───────┘
     │         │         │         │          │        │
     ▼         ▼         ▼         ▼          ▼        ▼
  AIBMR     AI-MM      CREN      AIBMO     AICROPS   Twenty
 (recon)  (matching) (enrich) (drafting) (sequencing) (CRM)

  ─────── existing CashTime production services ───────
  All called via the MCP gateway at mcp.cashtimepay.com
  (single trusted boundary, Bearer auth, allow-list per tool)
```

## Why this shape

- The Concierge agent itself is **net-new** for this submission. It is the
  only piece that lives in this repository.
- Every tool is a **thin MCP wrapper** over an already-running CashTime
  production service. We do not re-implement research / matching / outreach;
  we expose them through a single MCP boundary.
- This is the canonical way to ship an enterprise agent on GCP: ADK for the
  agent, MCP for the tool boundary, Cloud Run for hosting, Vertex AI for
  inference, Twenty for the system of record.

## Data flow (single brief, happy path)

1. Brand fills the brief form → POST `/concierge/run` (SSE response).
2. Runner starts an in-memory ADK session. The first event is a planning
   message from Gemini 2.5 Pro that decides to call `research_brand`.
3. `research_brand` calls AIBMR via Cloudflare Access; AIBMR runs its own
   Gemini Pro analysis of the brand domain and returns a structured profile.
4. Planner summarises the profile, then calls `match_creators` with the
   profile attached. AI-MM scores ~4.7k creators against the brief, returns
   the top 15.
5. For each of the top 15, planner calls `enrich_creator` (CREN refreshes
   contact + metrics). Independent calls run in parallel.
6. Planner calls `draft_outreach` per creator (AIBMO uses Gemini Flash to
   write personalised drafts in the brand tone-of-voice).
7. Planner calls `schedule_sequence` per creator (AICROPS picks send-times
   based on historical response curves).
8. Planner calls `crm_upsert` once with everything attached; Twenty receives
   a Company + Persons + Opportunity, linked to the existing Creator records.
9. SSE stream emits a final summary; UI renders the table + CRM link.

## Observability

- **OpenTelemetry → Cloud Trace.** `FastAPIInstrumentor` covers HTTP spans;
  `HTTPXClientInstrumentor` wraps every outbound call to AIBMR / AI-MM / etc.
  Each tool call from the agent is a child span; judges can replay the full
  trace in Cloud Trace.
- **Structured logs.** `structlog` JSON renderer → Cloud Logging. Each event
  carries `session_id`, `tool_name`, `tool_status`.
- **Demo mode.** `DEMO_MODE=true` shortcuts every tool to a deterministic
  stub payload so judges can replay the full flow without external auth.

## Security

- Inbound: Cloud IAP in front of both Brand UI and Concierge service. Judges
  get a dedicated tester account; everyone else is rejected.
- Outbound: Cloudflare Access service token `cashtime-agents` for every
  internal call (AIBMR / AIBMO / CREN / AICROPS). Twenty calls use a scoped
  API key from Secret Manager.
- No secrets in the image. All sensitive vars come from Secret Manager at
  Cloud Run revision time (see `deploy/cloudbuild.yaml`).
- Brand-facing confidentiality canon: agent never surfaces internal IDs,
  creator-side economics, or names of internal AI workers (system prompt
  enforces this; checked by automated lint on draft text).

## What lives where on GCP

| Resource | Project | Region |
|---|---|---|
| Concierge Cloud Run | `tools-cashtimepay-com` | `europe-west6` |
| Brand UI Cloud Run | `tools-cashtimepay-com` | `europe-west6` |
| Artifact Registry repo `cashtime` | `tools-cashtimepay-com` | `europe-west6` |
| Vertex AI (Gemini 2.5 Pro / Flash) | `tools-cashtimepay-com` | `europe-west6` |
| Secret Manager (`concierge-*`) | `tools-cashtimepay-com` | global |
| MCP gateway | `tools-cashtimepay-com` | `europe-west6` |
| Twenty CRM (existing) | `tools-cashtimepay-com` | `europe-west6` |
| AI-MM (existing) | `tools-cashtimepay-com` | `europe-west6` |

> Per the CashTime GCP canon, nothing in this submission touches
> `spheric-handler-487521-a5` (the consumer app) or `cashtime-pay-4ed26`
> (payments). Concierge is strictly a back-office agent.
