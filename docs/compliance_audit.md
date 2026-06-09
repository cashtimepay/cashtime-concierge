# Compliance audit - Google for Startups AI Agents Challenge Official Rules

> Audit done 2026-05-27 against the official Rules PDF. Each line maps a
> rule clause to our current status and the action that closes the gap.

## Eligibility (Rules §3)

| Requirement | Our status | Action |
|---|---|---|
| Entrant must be 18+ (20+ in Taiwan) | Dmitry Radionov, 18+ | none |
| Not a resident of IT / QC / Crimea / CU / IR / SY / KP / SD / BY / RU | Resident of Ukraine | OK |
| Not under US export controls / sanctions | None | OK |
| Has internet access as of 2026-04-20 | Yes | OK |
| Not an employee of Google / Devpost / sponsor affiliates | None | OK |
| Acting on behalf of CashTime Pay AG, with company consent | CRO with authority | OK |

## Contest Period (Rules §4)

- Submission: 2026-04-22 09:00 PT → **2026-06-05 17:00 PT**
- Judging: **2026-06-11 → 2026-06-18 17:00 PT** (Rules §8 has a typo
  showing 6/4-6/11; §4 governs)
- Winners: 2026-06-22 ~10:00 PT
- Our internal deadline: **2026-06-04** (buffer day on 06-05).

## Mandatory Technologies (Rules §6)

| Layer | Required | Our stack | Status |
|---|---|---|---|
| Intelligence | Gemini API or 3rd-party LLM via Gemini Enterprise Agents Platform | Gemini 3.1 Pro Preview + Gemini 3.5 Flash via Gemini Enterprise Agent Platform | ✅ |
| Orchestration | ADK / LangChain / CrewAI | Google ADK (Python) | ✅ |
| Infrastructure | Agent Engine / Cloud Run / GKE | Cloud Run, `europe-west6` | ✅ |

## Track-1 specifics (Rules §6)

- Must use MCP to securely connect to external tools - ✅ MCP gateway at
  `mcp.cashtimepay.com`.
- Show declarative intent, autonomous task execution - ✅ planner runs the
  six-tool pipeline autonomously.

## Submission Requirements (Rules §6)

| Requirement | Status | Action / owner |
|---|---|---|
| Text description (features, tech, data sources, arch diagram, findings) | Drafted in `docs/devpost_submission.md` (4979 chars) | finalise Day 7-9 |
| Architecture diagram | ASCII in `docs/architecture.md` | render to PNG on Day 7 |
| **1-2 min demo video, English or English-subtitled** | Rewrote `docs/demo_script.md` from 3 min → 2 min (this commit) | record on Day 8 |
| **Public code repository URL** | `github.com/cashtimepay/cashtime-concierge` is **private** - must flip public | Day 9 morning: audit repo for secrets / internal naming, then make public |
| Testing access (live URL or test build, with login if private) | Cloud IAP plan in `docs/judges_access.md`; tester account expires 2026-06-22 | Day 5 |
| Track selection | **Track 1 - Build (Net-New Agents)** | locked |
| Original work, created during Contest Period | Concierge agent + MCP wrappers + Brand UI net-new from 2026-05-27 (well inside Contest Period). Backend services act as third-party tool endpoints. | declared in `devpost_submission.md` |
| English-language submission | ✅ all artefacts English | none |
| No third-party logo / slogan / trademark in video | Video must avoid Twenty, Hunter, NeverBounce, Influencer's Club logos. Names may be spoken in voiceover (not visual). | re-check during Day 8 recording |
| No real client brand surfaces | Synthetic demo brand "Chapterhouse" | locked |

## Key Considerations alignment (Rules §6, non-binding but judge-facing)

| Recommendation | Our current state | Plan |
|---|---|---|
| Multi-agent design and orchestration | Single root agent + 6 tools today | **Day 2 refactor**: planner + 3 sub-agents (research / matching / outreach) + `crm_upsert` as planner-level tool |
| Deploy on Agent Engine | Cloud Run | Rules §6 lists Cloud Run as a valid alternative; keep Cloud Run, justify in submission text |
| Compelling business use case | $10K MRR Q3 plan, $5-15k agency baseline | already in `devpost_submission.md` |
| Grounding & RAG | None today | **Day 2-3**: Gemini Enterprise Search index over CashTime canonical taxonomies (40 niches, 10 platforms, 468 sub-niches, MCN registry, tone-of-voice dictionary); research sub-agent uses RAG grounding over brand brief |
| Collaboration between agents | Not yet | follows from multi-agent refactor |

## Intellectual Property (Rules §6)

- Submission is the original work of CashTime Pay AG. ✅
- No financial or preferential support from Google / Devpost. ✅
- $500 Google Cloud credits (default for all eligible startups) - apply on
  Day 1, approval up to 72h. **Open action.**
- Backend services (AIBMR / AI-MM / AICREN / AICROPS / Twenty) act
  as third-party tool endpoints to the Concierge agent and predate the
  Contest Period. The agent itself and all orchestration / MCP wrappers /
  Brand UI are net-new. This positioning is stated in `devpost_submission.md`.

## Third-Party Integrations (Rules §6)

All declared in `devpost_submission.md` § Third-party integrations:
GCP (Cloud ToS), Cloudflare Access (Enterprise), Twenty CRM (AGPL-3.0
self-hosted), paid contracts (Hunter.io, NeverBounce, Influencer's Club),
public APIs under ToS (YouTube Data API v3, Substack, Spotify, Apple
Podcasts, GitHub). Active CashTime subscriptions / rate-limit compliance
confirmed.

## Open actions (Day 1 → Day 9)

1. **Day 1 (today)** - apply for $500 Google Cloud credits.
2. **Day 2** - multi-agent refactor (planner + 3 sub-agents).
3. **Day 2-3** - Gemini Enterprise Search index + research sub-agent RAG grounding.
4. **Day 5** - Cloud IAP tester account, expiry 2026-06-22.
5. **Day 7** - Excalidraw → PNG architecture diagram.
6. **Day 8** - record 2-min demo video, no third-party logos on screen,
   English subtitles burned in.
7. **Day 9 morning** - audit private repo for secrets / internal naming
   collisions, then flip `cashtimepay/cashtime-concierge` to public.
8. **Day 9** - submit on Devpost, EMEA regional flag.

## Residual risks

- **Repo public exposes our MCP wrapper layout publicly.** Mitigation:
  the wrappers contain no business logic; all heavy lifting is behind
  `mcp.cashtimepay.com` with auth. Demo-mode payloads in `tools/*.py`
  use synthetic data only.
- **Cloud Run vs Agent Engine.** Rules §6 explicitly lists Cloud Run as
  acceptable; Key Considerations prefer Agent Engine. We justify Cloud
  Run in the submission text as the GA, production-equivalent path.
- **Judging timeline typo** between Rules §4 (Jun 11-18) and §8
  (Jun 4-11). §4 governs; tester credentials valid until 2026-06-22 to
  cover both interpretations.
