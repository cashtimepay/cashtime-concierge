# 3-minute demo video — script

> Recorded on Day 8 (2026-06-03). Voiceover in English. Screen capture via
> OBS at 1920×1080, exported H.264, uploaded as YouTube unlisted.

## Cold open (0:00 – 0:15)

**Screen:** Brand UI landing page. Cursor hovers over "Run a new brief".
**VO:**
> "Influencer marketing works. But the path from 'we have a product' to
> 'fifteen creators are negotiating with us' takes a junior marketer two to
> three days. We collapsed that into one conversation."

## The brief (0:15 – 0:30)

**Screen:** Brief form. Three fields fill in:
- URL: `https://chapterhouse.demo`
- Goal: `100 trial signups per month from indie-fiction readers`
- Budget: `$5,000 / month`
**VO:**
> "Meet Chapterhouse — an indie-fiction audiobook subscription. Three
> inputs: their website, their goal, their budget."

The user clicks **Run**.

## The pipeline runs live (0:30 – 1:50)

**Screen:** SSE log on the right. Tool calls appear one by one. Brand
profile renders on the left as soon as `research_brand` returns.

**VO over visuals:**
> "Behind the scenes, our Concierge agent — built on Google's Agent
> Development Kit, planning with Gemini 3.1 Pro Preview — orchestrates six tools
> through MCP."
>
> *(research_brand fires)* "First, it reads the brand homepage and
> extracts the product description, ideal audience, geographic focus, and
> tone-of-voice. Tone-of-voice will matter in a minute."
>
> *(match_creators fires)* "Then it ranks our database of nearly five
> thousand vetted creators and surfaces the top fifteen. Niche match,
> audience match, geo match."
>
> *(enrich_creator fires, in parallel)* "For every shortlisted creator,
> Gemini 3.5 Flash refreshes contact and engagement metrics in parallel."
>
> *(draft_outreach fires)* "Then it drafts a personalised first email per
> creator. This is where tone-of-voice pays off — every draft sounds like
> Chapterhouse, not like a template."
>
> *(schedule_sequence fires)* "Each creator goes into a 3-step sequence —
> initial message plus two follow-ups, timed against CashTime's historical
> response curves."
>
> *(crm_upsert fires)* "Finally, the agent writes the brand, the contacts,
> and the campaign into CashTime CRM, with every creator linked."

## The result (1:50 – 2:25)

**Screen:** Final summary panel. Creator table with handles, niches,
follower counts, fit scores. Click on one draft — it expands to show the
full email. Click "Open in CRM" — Twenty opens with the new Company,
Persons, and Opportunity.

**VO:**
> "That took 47 seconds. In the CRM, the brand owner now sees a Company,
> three Persons, an Opportunity, and fifteen linked Creators — exactly
> what a senior account manager would have produced over two days."

## The trace (2:25 – 2:45)

**Screen:** Cloud Trace dashboard. The full waterfall — 6 tool calls,
~110 spans total. Hover on the `match_creators` span — it shows ~14k
candidates scored.

**VO:**
> "Every tool call is a span. Every Gemini round-trip is a span. Judges
> and engineers can replay any session in Cloud Trace — production-grade
> from day one, not an afterthought."

## Close (2:45 – 3:00)

**Screen:** CashTime logo + one-line tagline.
**VO:**
> "CashTime Brand Concierge. Built on Google ADK, Gemini, and Vertex AI.
> Brand briefs in, working creator pipelines out — in a single conversation.
> Thank you."

---

## Production notes

- Open the run with `DEMO_MODE=false` against the real `match_creators` so
  the creator table shows real BookTok / Bookstagram handles. We are
  cleared to surface those publicly (they are public creator profiles).
- Keep total length 2:55 — leave 5s headroom under the 3-min cap.
- No background music. SSE-stream sounds carry the rhythm.
- Subtitles burned in (high-contrast, sans-serif) — judges may have
  audio off.
