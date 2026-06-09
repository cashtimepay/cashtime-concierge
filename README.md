# CashTime Brand Concierge

> Multi-agent system that turns a brand brief into a working creator outreach
> pipeline in one streamed conversation. Submission for the
> [Google for Startups AI Agents Challenge 2026](https://devpost.team/google-cloud-for-startups/hackathons/3197)
> by **CashTime Pay AG** (Zug, Switzerland).

## What it does

A brand owner pastes a homepage URL, a goal, and a monthly budget. A **planner
agent** delegates to three specialist sub-agents and writes the result to the
CRM - all streamed live:

1. **research** - researches the brand (description, ICP, geo, tone-of-voice,
   decision-makers) and **grounds** it against CashTime's canonical taxonomy via
   Gemini Enterprise Search, so the brand maps to real niche enums (no hallucination),
2. **matching** - matches 10-15 creators from the CashTime database and
   refreshes each one's contact + audience metrics,
3. **outreach** - drafts a personalised first message per creator and schedules
   a 3-step sequence (initial + 2 follow-ups),
4. **crm_upsert** (planner tool) - upserts the brand, contacts, and the campaign
   into the CashTime CRM.

What used to take a CashTime account manager 2-3 days now happens in minutes.

## Agent design

```
planner  (Gemini 3.1 Pro Preview)
  ├── research_agent  (Gemini 3.5 Flash)  research_brand · ground_taxonomy [Gemini Enterprise Search RAG]
  ├── matching_agent  (Gemini 3.5 Flash)  match_creators · enrich_creator
  ├── outreach_agent  (Gemini 3.5 Flash)  draft_outreach · schedule_sequence
  └── crm_upsert       (planner-level tool)
```

A `DEMO_MODE=true` deterministic twin (`concierge/pipeline.py`) runs the exact
same tool sequence with no LLM, emitting an identical event stream - for offline
judge replay and tests.

## Track and theme

- **Track 1 - Build (Net-New Agents)**
- Built net-new for the hackathon, on top of existing CashTime production services
  exposed as MCP tools.

## Stack

| Layer | Choice |
|---|---|
| Agent framework | Google Agent Development Kit (ADK), Python |
| Agent design | Planner + 3 sub-agents (research / matching / outreach), agent-to-agent collaboration via `AgentTool` |
| Planner LLM | Gemini 3.1 Pro Preview |
| Worker LLM | Gemini 3.5 Flash |
| Inference | Gemini Enterprise Agents Platform (region `global`) |
| Grounding / RAG | Gemini Enterprise Search (Discovery Engine) over the canonical taxonomy, with a bundled local-corpus fallback |
| Tools | Model Context Protocol (MCP) over `mcp.cashtimepay.com` |
| Backend | FastAPI + SSE on Cloud Run |
| UI | Next.js, Cloud Run, behind Cloud IAP for judges |
| Observability | OpenTelemetry → Cloud Trace, structlog JSON logs |
| CI/CD | Cloud Build (`deploy/cloudbuild.yaml`, `deploy/cloudbuild.ui.yaml`) |
| CRM | Twenty (self-hosted at `crm.cashtimepay.com`) |
| Project | `tools-cashtimepay-com` (per CashTime GCP routing canon) |

## Project layout

```
cashtime-concierge/
├── concierge/                  # Agent stack + FastAPI server
│   ├── agents/                 # Multi-agent stack
│   │   ├── planner.py          # Root planner (3 sub-agents as tools + crm_upsert)
│   │   ├── research.py         # research sub-agent
│   │   ├── matching.py         # matching sub-agent
│   │   └── outreach.py         # outreach sub-agent
│   ├── agent.py                # Re-exports root_agent (ADK discovery)
│   ├── prompts.py              # Planner + per-sub-agent instructions
│   ├── grounding.py            # ground_taxonomy (Gemini Enterprise Search + local fallback)
│   ├── pipeline.py             # Deterministic demo orchestrator (no LLM)
│   ├── server.py               # FastAPI + SSE (demo → pipeline, live → ADK)
│   ├── settings.py             # pydantic-settings
│   ├── observability.py        # OTel → Cloud Trace
│   ├── http_client.py          # Shared httpx clients
│   ├── data/taxonomy_corpus.json  # Canonical taxonomy (grounding corpus)
│   └── tools/                  # MCP-wrapped tools
│       ├── aibmr.py            # research_brand
│       ├── aimm.py             # match_creators
│       ├── cren.py             # enrich_creator
│       ├── aicrops.py          # draft_outreach + schedule_sequence (AICROPS)
│       └── twenty.py           # crm_upsert
├── ui/                         # Next.js brand UI (brief form + live SSE log)
├── deploy/
│   ├── cloudbuild.yaml         # concierge service build/deploy
│   ├── cloudbuild.ui.yaml      # Brand UI build/deploy
│   ├── deploy.sh               # one-shot: preflight | infra | api | ui | all
│   ├── provision_grounding.sh  # create + populate the grounding index
│   └── iap_setup.md            # Cloud IAP wiring for judges
├── docs/                       # Submission artefacts
├── tests/                      # Pytest (tools + pipeline + grounding)
├── Dockerfile
└── pyproject.toml
```

## Local development

```bash
# Python 3.11+
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# either fill MCP / Twenty credentials, or keep DEMO_MODE=true to run with stub data

uvicorn concierge.server:app --reload --port 8080
# POST a brief
curl -N -X POST http://localhost:8080/concierge/run \
  -H 'Content-Type: application/json' \
  -d '{"brand_url":"https://chapterhouse.demo","goal":"100 trial signups/mo","budget_monthly_usd":5000}'
```

Tests:

```bash
DEMO_MODE=true pytest -q
```

## Deploy to Cloud Run

One-shot, idempotent (targets `tools-cashtimepay-com` / `europe-west6`):

```bash
./deploy/deploy.sh preflight   # check auth/project/APIs, create nothing
./deploy/deploy.sh infra       # APIs + Artifact Registry + SA + secrets + Gemini Enterprise Search index
# populate Secret Manager values, then:
./deploy/deploy.sh api         # build + deploy concierge service
./deploy/deploy.sh ui          # build + deploy Brand UI
```

`deploy/iap_setup.md` wires Cloud IAP + an HTTPS load balancer so judges sign in
with one Google account. The deploy step needs a service account with
`run.developer` + `iam.serviceAccountUser` on `cashtime-concierge@`.

## Submission artefacts

See `docs/`:
- `devpost_submission.md` - copy-ready text for every devpost field
- `architecture.md` - full system diagram
- `judges_access.md` - login + walkthrough for judges

## Licence

Proprietary © 2026 CashTime Pay AG. Submission code shared with hackathon
judges under the standard Devpost terms. Production CashTime services exposed
via MCP remain CashTime IP.

## Contact

Dmitry Radionov - CRO, CashTime Pay AG - dmitry@cashtimepay.com
