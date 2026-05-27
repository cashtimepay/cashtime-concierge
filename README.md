# CashTime Brand Concierge

> Single-conversation AI agent that turns a brand brief into a working creator
> outreach pipeline. Submission for the
> [Google for Startups AI Agents Challenge 2026](https://devpost.team/google-cloud-for-startups/hackathons/3197)
> by **CashTime Pay AG** (Zug, Switzerland).

## What it does

A brand owner pastes a homepage URL, a goal, and a monthly budget. Within one
streamed conversation, the Concierge agent:

1. researches the brand (description, ICP, geo, tone-of-voice, decision-makers),
2. matches 10–15 creators from the CashTime database,
3. enriches each shortlisted creator (contact, latest metrics),
4. drafts a personalised first outreach for every match,
5. schedules a 3-step sequence (initial + 2 follow-ups),
6. upserts the brand, contacts, and the campaign into the CashTime CRM.

What used to take a CashTime account manager 2–3 days now happens in minutes.

## Track and theme

- **Track 1 — Build (Net-New Agents)**
- Built net-new for the hackathon, on top of existing CashTime production services
  exposed as MCP tools.

## Stack

| Layer | Choice |
|---|---|
| Agent framework | Google Agent Development Kit (ADK), Python |
| Planner LLM | Gemini 3.1 Pro Preview |
| Worker LLM | Gemini 3.5 Flash |
| Inference | Gemini Enterprise Agent Platform (region `europe-west6`) |
| Tools | Model Context Protocol (MCP) over `mcp.cashtimepay.com` |
| Backend | FastAPI + SSE on Cloud Run |
| UI | Next.js, Cloud Run, behind Cloud IAP for judges |
| Observability | OpenTelemetry → Cloud Trace, structlog JSON logs |
| CI/CD | Cloud Build (`deploy/cloudbuild.yaml`) |
| CRM | Twenty (self-hosted at `crm.cashtimepay.com`) |
| Project | `tools-cashtimepay-com` (per CashTime GCP routing canon) |

## Project layout

```
cashtime-concierge/
├── concierge/                  # Agent + FastAPI server
│   ├── agent.py                # ADK root agent
│   ├── prompts.py              # System instruction
│   ├── server.py               # FastAPI + SSE
│   ├── settings.py             # pydantic-settings
│   ├── observability.py        # OTel → Cloud Trace
│   ├── http_client.py          # Shared httpx clients
│   └── tools/                  # MCP-wrapped tools
│       ├── aibmr.py            # research_brand
│       ├── aimm.py             # match_creators
│       ├── cren.py             # enrich_creator
│       ├── aibmo.py            # draft_outreach
│       ├── aicrops.py          # schedule_sequence
│       └── twenty.py           # crm_upsert
├── ui/                         # Next.js brand UI (added Day 3)
├── deploy/cloudbuild.yaml      # Cloud Build pipeline
├── docs/                       # Submission artefacts
├── tests/                      # Pytest smoke tests
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

```bash
gcloud builds submit --config deploy/cloudbuild.yaml \
  --project tools-cashtimepay-com .
```

Trigger from GitHub on push to `main`: configured separately via Cloud Build
trigger (deploy step requires a service account with `run.developer` +
`iam.serviceAccountUser` on `cashtime-concierge@`).

## Submission artefacts

See `docs/`:
- `devpost_submission.md` — copy-ready text for every devpost field
- `architecture.md` — full system diagram
- `judges_access.md` — login + walkthrough for judges
- `demo_script.md` — 3-minute video script

## Licence

Proprietary © 2026 CashTime Pay AG. Submission code shared with hackathon
judges under the standard Devpost terms. Production CashTime services exposed
via MCP remain CashTime IP.

## Contact

Dmitry Radionov — CRO, CashTime Pay AG — dmitry@cashtimepay.com
