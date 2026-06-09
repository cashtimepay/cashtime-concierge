# Testing access for hackathon judges

> This page is rendered into the **Testing access** field of the devpost form.

## Live demo (public, no login)

Deployed on Cloud Run in `tools-cashtimepay-com` / `europe-west6`, running in
**demo mode** with the synthetic **Chapterhouse** brand only — no login, no real
data, no production calls. Open the UI and click **"Run the Chapterhouse demo"**:

- **Brand UI (judges entry point):**
  `https://cashtime-concierge-ui-455884480848.europe-west6.run.app/`
- **Concierge API health (no auth):**
  `https://cashtime-concierge-455884480848.europe-west6.run.app/health`
- **OpenAPI spec / Swagger:**
  `https://cashtime-concierge-455884480848.europe-west6.run.app/docs`

> **Enter any real brand URL** — the research step genuinely fetches and
> analyses it and grounds it to real CashTime niches; creator matching draws
> from a curated, public-safe sample of the real creator network (handle /
> niche / followers only — no contact data or economics). Toggle **Live** for
> the real ADK + Gemini multi-agent run, or **Fast** for the instant
> deterministic replay. No emails are sent; the CRM step writes nothing to
> production.

## Hardened access (custom domains + IAP)

For production we front both services with a custom domain + Cloud IAP
(`concierge.cashtimepay.com`, `concierge-api.cashtimepay.com`) so a single tester
account governs access during the judging window (2026-06-11 → 2026-06-22), with
read-only entry to the Brand UI and a scoped CRM tenant holding only the
synthetic Chapterhouse data. Wiring is in `deploy/iap_setup.md`. The public
run.app demo above needs no such account.

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
