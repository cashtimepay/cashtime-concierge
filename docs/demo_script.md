# 2-minute demo video — script

> Hard cap from Rules §6: max 2 minutes — anything past 02:00 is not
> evaluated. Recorded on Day 8 (2026-06-03). Voiceover in English. Screen
> capture via OBS at 1920×1080, exported H.264, uploaded as YouTube
> unlisted. English subtitles burned in (judges may watch muted).
>
> Rules §6: no third-party logo / slogan / trademark may appear on screen.
> All vendor names (Twenty, Hunter, NeverBounce, Influencer's Club,
> YouTube, Substack, Spotify) may only be spoken in voiceover; the UI
> captures must not show their logos. The Twenty CRM tab and any vendor
> brand marks are blurred or replaced with our own UI shell.

## Cold open (0:00 – 0:08)

**Screen:** Brand UI landing page (CashTime branding only).
**VO:**
> "Influencer marketing takes a marketer two to three days per campaign.
> We collapsed that into one conversation."

## The brief (0:08 – 0:18)

**Screen:** Brief form, three fields:
- URL: `https://chapterhouse.demo`
- Goal: `100 trial signups per month`
- Budget: `$5,000 / month`

User clicks **Run**.

**VO:**
> "Meet Chapterhouse — an indie audiobook subscription. Three inputs:
> their site, their goal, their budget."

## Live pipeline (0:18 – 1:25)

**Screen:** SSE log on the right; brand profile, creator table, drafts,
CRM summary fill in the left column as events stream.

**VO over visuals:**
> "Behind the scenes, our agent — built on Google's Agent Development
> Kit, planning with Gemini 3.1 Pro Preview — orchestrates a research
> sub-agent, a matching sub-agent, and an outreach sub-agent through
> the Model Context Protocol."
>
> *(research sub-agent runs)* "The research sub-agent grounds itself
> against a Vertex AI Search index of CashTime's canonical taxonomies
> and the brand's own homepage; it extracts product, ICP, geo, and
> tone-of-voice."
>
> *(matching sub-agent runs)* "The matching sub-agent ranks our database
> of nearly five thousand vetted creators against the brand profile and
> returns the top fifteen."
>
> *(outreach sub-agent runs, parallel)* "The outreach sub-agent refreshes
> each shortlisted creator and writes a personalised first email plus
> two follow-ups — tone-matched to the brand."
>
> *(crm_upsert tool fires)* "Finally, the planner writes the brand, the
> contacts, and the campaign into our CRM."

## Result + trace (1:25 – 1:55)

**Screen:** Final summary — creator table, expandable drafts, CRM deep
link. Quick cut to Cloud Trace waterfall showing planner → 3 sub-agents
→ tools.

**VO:**
> "Forty-seven seconds end-to-end. Every Gemini call, every sub-agent
> invocation is a span in Cloud Trace — production-grade from day one."

## Close (1:55 – 2:00)

**Screen:** CashTime logo + project name.
**VO:**
> "CashTime Brand Concierge. Built on Google ADK, Gemini, and Gemini
> Enterprise Agent Platform."

---

## Production notes

- **Length budget: 1:55 final cut**, leaving 5 s headroom under the
  2-minute cap.
- Run in `DEMO_MODE=true` for the recording so timings are deterministic
  and the creator handles do not surface real CashTime client data.
- The Cloud Trace cutaway uses our own service-name `cashtime-concierge`;
  no third-party logos visible.
- No background music — SSE stream rhythm carries the pace.
- Subtitles burned in, high-contrast sans-serif, 16:9 lower third.
