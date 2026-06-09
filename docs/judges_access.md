# Testing access for hackathon judges

> This page is rendered into the **Testing access** field of the devpost form
> on submission day. Filled out on Day 9.

## Deployed URLs

- **Brand UI (judges entry point):** `https://concierge.cashtimepay.com/`
  *(behind Cloud IAP — credentials below)*
- **Health probe (no auth):** `https://concierge-api.cashtimepay.com/healthz`
- **Open API spec:** `https://concierge-api.cashtimepay.com/docs`

## Judges credentials

A single tester account is provisioned for the judging window
(2026-06-11 → 2026-06-22). Credentials are sent privately on the devpost
submission form, not committed to this repo.

The account has read-only access to:
- The Brand UI (can submit briefs, see live runs)
- A scoped CashTime CRM tenant (read-only, populated only with the
  synthetic "Chapterhouse" demo data)
- The Cloud Trace dashboard for the Concierge service (link below)

After 2026-06-22 the account is revoked automatically.

## Quick walkthrough (90 seconds)

1. Sign in to `https://concierge.cashtimepay.com/` with the provided
   Google account.
2. On the landing page, click **"Run the Chapterhouse demo"** (a one-click
   preset that loads the synthetic brand).
3. Watch the streamed tool-call log on the right. The planner delegates to
   three sub-agents and the tools fire in order:
   `research_brand` → `ground_taxonomy` (Vertex AI Search RAG) →
   `match_creators` → `enrich_creator` (×N) → `draft_outreach` (×N) →
   `schedule_sequence` (×N) → `crm_upsert`.
4. When the run completes, click **"Open in CRM"** to see the Company,
   Persons, and Opportunity that the agent just created.
5. Optionally, click **"View trace"** to see the full OpenTelemetry trace
   in Cloud Trace, including every Gemini call and every outbound HTTP
   request to the MCP tools.

## Submit your own brief

Replace the demo preset with any homepage URL, a goal, and a monthly budget.
The agent will treat it as a new brief end-to-end. Note: brands outside the
synthetic demo path will use the live CashTime creator database; please be
mindful and limit yourselves to one or two custom runs per day during
judging (we will not be billed, but the database is shared with our
production pipelines).

## Local replay (no auth required)

If you want to run everything locally with deterministic stub data, no GCP
credentials needed:

```bash
git clone https://github.com/cashtimepay/cashtime-concierge.git
cd cashtime-concierge
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DEMO_MODE=true uvicorn concierge.server:app --port 8080

# in another terminal
curl -N -X POST http://localhost:8080/concierge/run \
  -H 'Content-Type: application/json' \
  -d '{"brand_url":"https://chapterhouse.demo","goal":"100 trial signups/mo","budget_monthly_usd":5000}'
```

`DEMO_MODE=true` runs the full pipeline through a **deterministic orchestrator**
(no LLM, no external auth) that fires the exact same tool sequence and emits the
exact same event stream as the live model-driven run — so judges get an
identical, reproducible end-to-end demo offline. The live run (no `DEMO_MODE`)
drives the same pipeline with the ADK multi-agent planner + Gemini and the
Vertex AI Search grounding backend.

To run the Brand UI locally against it:

```bash
cd ui && npm install
NEXT_PUBLIC_CONCIERGE_API=http://localhost:8080 npm run dev   # → http://localhost:3000
```
