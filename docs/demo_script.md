# 2-minute demo video — script

> Hard cap (Rules §6): **max 2:00** — anything past 02:00 is not evaluated.
> Target final cut **~1:50**. English voiceover + burned-in English subtitles
> (judges may watch muted). 1920×1080, H.264, YouTube unlisted.
>
> Rules §6: no third-party logo / slogan / trademark on screen. We capture the
> synthetic **Chapterhouse** brand (our own — no third-party mark); creator
> handles shown are public account names inside our own UI shell. Vendor names
> (Vertex AI, Twenty, etc.) may be spoken, not shown as logos.

---

## 0:00 – 0:09 · Cold open (the problem)

**Screen:** Brand UI landing page (CashTime branding only).
**VO:**
> "Matching a brand with the right creators and launching personalised
> outreach takes a marketer two to three days. CashTime Brand Concierge does it
> in one conversation — with real AI agents."

## 0:09 – 0:20 · The brief

**Screen:** Brief form. **Live** toggle ON. Fields:
`chapterhouse.demo` · `100 trial signups a month` · `$5,000`. Click **Run**.
**VO:**
> "Three inputs — a brand's site, a goal, a budget. 'Live' runs real Gemini
> agents. We hit Run."

## 0:20 – 1:05 · The pipeline (speed-ramp the ~60–90 s wait)

**Screen:** The four agent tabs light up in order — Research → Match → Outreach
→ CRM — each filling with output. Keep the status dots / live banner visible.
**VO (over visuals):**
> "On Google's Agent Development Kit, a planner on Gemini 3.1 Pro orchestrates
> three specialist sub-agents on Gemini 3.5 Flash, through the Model Context
> Protocol. They never talk to each other — the planner threads each result to
> the next.
>
> The research agent fetches the brand and grounds it against our canonical
> taxonomy with Vertex AI Search, so it maps to real niches, never invented
> ones — and it works for any real brand URL you enter.
>
> The matching agent ranks our network of nearly five thousand creators and
> returns the best fits. The outreach agent writes a personalised first message
> and a follow-up sequence for each — it drafts and schedules, but never sends.
> A human approves every message."

## 1:05 – 1:30 · The result

**Screen:** Click through tabs — Match (real creator table), Outreach (a draft
+ schedule), CRM (the record, "not written to production" banner).
**VO:**
> "Each agent's work lands in its own tab — the grounded profile, the matched
> creators, the ready-to-approve drafts, and the CRM record. What took days is
> ready in about a minute."

## 1:30 – 1:50 · Why it's real

**Screen:** Brief hover on the FAQ line "Which AI models run, and on what
credentials?" / the architecture diagram.
**VO:**
> "Every Gemini call runs on Vertex AI inside our own Google Cloud project,
> authenticated by its service account — no API keys, no outside gateway. ADK,
> Gemini and MCP, on Cloud Run."

## 1:50 – 1:58 · Close

**Screen:** CashTime Brand Concierge title card.
**VO:**
> "CashTime Brand Concierge. Time, as currency."

---

## Production notes

- **Length: ~1:50 final**, ≥10 s headroom under the 2:00 cap.
- Record a real **Live** run (toggle on) so the tabs fill with real Gemini
  output + real network creators — then speed-ramp / time-lapse the wait so the
  cut stays tight. Do **not** fake it with Fast mode on screen.
- On-screen brand = synthetic **Chapterhouse** (no third-party trademark). The
  matched creators are real, public network handles shown in our own UI — no
  third-party logos/marks on screen. Blur anything borderline.
- Subtitles burned in, high-contrast sans-serif, lower third.
- No music, or a quiet bed; let the tab/stream rhythm carry the pace.
- Capture URL: `https://cashtime-concierge-ui-455884480848.europe-west6.run.app`.
