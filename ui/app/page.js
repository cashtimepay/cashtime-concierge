"use client";

import { useEffect, useRef, useState } from "react";
import "./globals.css";

const BUILD_API_BASE =
  process.env.NEXT_PUBLIC_CONCIERGE_API || "http://localhost:8080";

const DEMO_PRESET = {
  brand_url: "https://chapterhouse.demo",
  goal: "100 trial signups per month from indie-fiction readers",
  budget_monthly_usd: 5000,
};

// Which pipeline step each tool belongs to.
const STEP_OF = {
  research_brand: "research",
  ground_taxonomy: "research",
  match_creators: "match",
  enrich_creator: "match",
  draft_outreach: "outreach",
  schedule_sequence: "outreach",
  crm_upsert: "crm",
};
const STEP_ORDER = ["research", "match", "outreach", "crm"];
const TABS = [
  { key: "research", label: "1 · Research" },
  { key: "match", label: "2 · Match" },
  { key: "outreach", label: "3 · Outreach" },
  { key: "crm", label: "4 · CRM" },
  { key: "activity", label: "Activity log" },
];

function emptyPipe() {
  return {
    profile: null,
    grounding: null,
    creators: [],
    enriched: {},
    drafts: [],
    sequences: [],
    crm: null,
    steps: { research: "pending", match: "pending", outreach: "pending", crm: "pending" },
  };
}

function fmtNum(n) {
  return n == null ? "—" : Intl.NumberFormat("en-US").format(n);
}

export default function Home() {
  const [brandUrl, setBrandUrl] = useState("");
  const [goal, setGoal] = useState("");
  const [budget, setBudget] = useState(5000);
  const [events, setEvents] = useState([]);
  const [pipe, setPipe] = useState(emptyPipe());
  const [tab, setTab] = useState("research");
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [apiBase, setApiBase] = useState(BUILD_API_BASE);
  const pinnedRef = useRef(false);
  const logRef = useRef(null);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((c) => c.apiBase && setApiBase(c.apiBase))
      .catch(() => {});
  }, []);

  function applyEvent(ev) {
    // raw activity log
    if (ev.type !== "summary_data") {
      setEvents((prev) => {
        const next = [...prev, ev];
        queueMicrotask(() => {
          if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
        });
        return next;
      });
    }

    // step status + auto-advance on a tool starting
    if (ev.type === "tool_call" && ev.tool_calls?.length) {
      const step = STEP_OF[ev.tool_calls[0].name];
      if (step) {
        const idx = STEP_ORDER.indexOf(step);
        setPipe((p) => {
          const steps = { ...p.steps };
          STEP_ORDER.forEach((s, i) => {
            if (i < idx) steps[s] = "done";
          });
          steps[step] = "running";
          return { ...p, steps };
        });
        if (!pinnedRef.current) setTab(step);
      }
    }

    // accumulate structured results per tab
    if (ev.type === "tool_result" && ev.tool_results?.length) {
      const { name, response } = ev.tool_results[0];
      setPipe((p) => {
        const n = { ...p };
        if (name === "research_brand") n.profile = response;
        else if (name === "ground_taxonomy") n.grounding = response;
        else if (name === "match_creators") n.creators = response.creators || [];
        else if (name === "enrich_creator")
          n.enriched = { ...p.enriched, [response.creator_id]: response };
        else if (name === "draft_outreach") n.drafts = [...p.drafts, response];
        else if (name === "schedule_sequence") n.sequences = [...p.sequences, response];
        else if (name === "crm_upsert") n.crm = response;
        return n;
      });
    }

    if (ev.type === "summary" || ev.type === "done") {
      setPipe((p) => ({
        ...p,
        steps: { research: "done", match: "done", outreach: "done", crm: "done" },
      }));
    }
  }

  async function run(payload) {
    setEvents([]);
    setPipe(emptyPipe());
    setTab("research");
    pinnedRef.current = false;
    setStatus("running");
    try {
      const resp = await fetch(`${apiBase}/concierge/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // SSE frames are separated by a blank line; the wire uses CRLF
        // (event:…\r\ndata:…\r\n\r\n), so split on either \r\n\r\n or \n\n.
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const dataLine = frame
            .split(/\r?\n/)
            .find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          let ev;
          try {
            ev = JSON.parse(dataLine.slice(5).trim());
          } catch {
            continue;
          }
          applyEvent(ev);
        }
      }
      setStatus("done");
    } catch (err) {
      applyEvent({ type: "text", text: `Error: ${err.message}` });
      setStatus("error");
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    run({ brand_url: brandUrl, goal, budget_monthly_usd: Number(budget) });
  }

  function runDemo() {
    setBrandUrl(DEMO_PRESET.brand_url);
    setGoal(DEMO_PRESET.goal);
    setBudget(DEMO_PRESET.budget_monthly_usd);
    run(DEMO_PRESET);
  }

  function selectTab(k) {
    pinnedRef.current = true;
    setTab(k);
  }

  const running = status === "running";

  return (
    <div className="wrap">
      <div className="header">
        <h1>CashTime Brand Concierge</h1>
        <span className="badge">AI Agents Challenge · Track 1</span>
      </div>
      <p className="sub">
        Give us a brand brief. The agent researches the brand, matches creators
        from the CashTime network, drafts personalised outreach, and writes the
        campaign to the CRM — live.
      </p>

      <HowItWorks />

      <div className="grid">
        <form className="panel" onSubmit={onSubmit}>
          <h2>Brief</h2>
          <label htmlFor="brand">Brand URL</label>
          <input id="brand" placeholder="https://your-brand.com" value={brandUrl}
            onChange={(e) => setBrandUrl(e.target.value)} disabled={running} />
          <label htmlFor="goal">Goal</label>
          <textarea id="goal" rows={3} placeholder="e.g. 100 trial signups per month"
            value={goal} onChange={(e) => setGoal(e.target.value)} disabled={running} />
          <label htmlFor="budget">Monthly creator budget (USD)</label>
          <input id="budget" type="number" min={0} step={500} value={budget}
            onChange={(e) => setBudget(e.target.value)} disabled={running} />
          <div className="row">
            <button className="primary" type="submit" disabled={running || !brandUrl || !goal}>
              {running ? "Running…" : "Run pipeline"}
            </button>
            <button className="ghost" type="button" onClick={runDemo} disabled={running}>
              Run the Chapterhouse demo
            </button>
          </div>
        </form>

        <div className="panel">
          <div className="tabs">
            {TABS.map((t) => (
              <button
                key={t.key}
                className={`tab ${tab === t.key ? "active" : ""}`}
                onClick={() => selectTab(t.key)}
                type="button"
              >
                {t.key !== "activity" && (
                  <span className={`tdot ${pipe.steps[t.key]}`} />
                )}
                {t.label}
              </button>
            ))}
          </div>

          <div className="tabbody">
            {tab === "research" && <ResearchTab pipe={pipe} />}
            {tab === "match" && <MatchTab pipe={pipe} />}
            {tab === "outreach" && <OutreachTab pipe={pipe} />}
            {tab === "crm" && <CrmTab pipe={pipe} />}
            {tab === "activity" && <ActivityTab events={events} logRef={logRef} />}
          </div>
        </div>
      </div>

      <p className="foot">
        CashTime Pay AG · Switzerland — drafts and schedules only; a human
        approves every message. Demo data is synthetic.
      </p>
    </div>
  );
}

/* ---------- tab content ---------- */

function Waiting({ what }) {
  return <div className="waiting">Waiting for the {what} agent…</div>;
}

function ResearchTab({ pipe }) {
  const p = pipe.profile;
  const g = pipe.grounding;
  if (!p) return <Waiting what="research" />;
  const c = p.company || {};
  const icp = p.icp || {};
  return (
    <div>
      <h3 className="tab-h">{c.name} — brand profile</h3>
      <p className="muted-p">{c.description}</p>
      <div className="kv">
        <div><span>Pricing</span>{c.pricing_model || "—"}{c.monthly_price_usd ? ` · $${c.monthly_price_usd}/mo` : ""}</div>
        <div><span>Audience</span>{icp.audience || "—"}</div>
        <div><span>Geo</span>{(p.geo || []).join(", ") || "—"}</div>
        <div><span>Tone of voice</span>{p.tone_of_voice || "—"}</div>
      </div>
      {p.persons?.length > 0 && (
        <div className="block">
          <div className="block-t">Decision-makers</div>
          {p.persons.map((pe, i) => (
            <div className="muted small" key={i}>{pe.name} — {pe.role} · {pe.email}</div>
          ))}
        </div>
      )}
      <div className="block">
        <div className="block-t">
          Grounded niches {g && <span className="src">via {g.backend === "local_corpus" ? "taxonomy index" : g.backend}</span>}
        </div>
        <div>
          {(p.categories || []).map((cat) => <span className="pill on" key={cat}>{cat}</span>)}
        </div>
        {g && (
          <div className="muted small" style={{ marginTop: 8 }}>
            Matched against {g.citations?.length || 0} canonical taxonomy entries — only real
            CashTime niches are used, never invented ones.
          </div>
        )}
      </div>
    </div>
  );
}

function MatchTab({ pipe }) {
  if (!pipe.creators.length) return <Waiting what="matching" />;
  return (
    <div>
      <h3 className="tab-h">{pipe.creators.length} creators matched</h3>
      <div className="creator head">
        <span>Creator</span><span>Niche</span><span>Followers</span><span>Eng.</span><span>Fit</span><span>Geo</span>
      </div>
      {pipe.creators.map((c, i) => {
        const e = pipe.enriched[c.creator_id] || {};
        return (
          <div className="creator c6" key={i}>
            <span>{c.handle} {e.creator_id && <span className="ok">✓</span>}</span>
            <span>{c.niche}</span>
            <span>{fmtNum(e.follower_count || c.follower_count)}</span>
            <span>{(e.engagement_percent || c.engagement_percent) ?? "—"}%</span>
            <span>{c.fit_score != null ? c.fit_score.toFixed(2) : "—"}</span>
            <span>{c.geo || "—"}</span>
          </div>
        );
      })}
      <div className="muted small" style={{ marginTop: 10 }}>
        ✓ = contact + audience metrics refreshed by the enrichment step.
      </div>
    </div>
  );
}

function OutreachTab({ pipe }) {
  if (!pipe.drafts.length) return <Waiting what="outreach" />;
  return (
    <div>
      <h3 className="tab-h">{pipe.drafts.length} drafts ready for approval</h3>
      <div className="warn-strip">Drafts &amp; schedules only — nothing is sent. A human approves each message.</div>
      {pipe.drafts.map((d, i) => {
        const seq = pipe.sequences.find((s) => s.creator_id === d.creator_id);
        const body = (d.body_markdown || "").slice(0, 220);
        return (
          <div className="draft" key={i}>
            <div className="draft-h">{d.handle}</div>
            <div className="draft-subj">{d.subject}</div>
            <div className="draft-body">{body}{(d.body_markdown || "").length > 220 ? "…" : ""}</div>
            {seq && (
              <div className="muted small">
                Sequence: {seq.total_messages} messages
                {seq.steps?.length ? ` · first ${seq.steps[0].scheduled_at?.slice(0, 10)}` : ""}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function CrmTab({ pipe }) {
  const crm = pipe.crm;
  if (!crm) return <Waiting what="CRM" />;
  return (
    <div>
      <h3 className="tab-h">CRM record</h3>
      {crm.written === false && (
        <div className="warn-strip">
          Demo record — synthetic data, <b>not written to the production CRM</b>.
          With production credentials this same step creates the records below in Twenty.
        </div>
      )}
      <div className="kv">
        <div><span>Company</span>{crm.company_name || "—"}</div>
        <div><span>Opportunity</span>{crm.opportunity_name || "—"}</div>
        <div><span>Creators linked</span>{crm.creators_linked ?? "—"}</div>
        <div><span>Sequences attached</span>{crm.sequences_attached ?? "—"}</div>
      </div>
      {crm.persons?.length > 0 && (
        <div className="block">
          <div className="block-t">Contacts (Persons)</div>
          {crm.persons.map((pe, i) => (
            <div className="muted small" key={i}>{pe.name} — {pe.role} · {pe.email}</div>
          ))}
        </div>
      )}
      {crm.written && crm.crm_url && (
        <a className="crm-link" href={crm.crm_url} target="_blank" rel="noreferrer">Open in CRM →</a>
      )}
    </div>
  );
}

function ActivityTab({ events, logRef }) {
  return (
    <div className="log" ref={logRef}>
      {events.length === 0 && (
        <div className="empty">
          Submit a brief or click <b>Run the Chapterhouse demo</b> to watch the agents work.
        </div>
      )}
      {events.map((ev, i) => <LogLine key={i} ev={ev} />)}
    </div>
  );
}

function LogLine({ ev }) {
  if (ev.type === "tool_call" && ev.tool_calls?.length) {
    return (
      <div className="ev tool_call">
        <span className="tag">call</span><span className="arrow">→</span> {ev.tool_calls[0].name}
      </div>
    );
  }
  if (ev.type === "tool_result" && ev.tool_results?.length) {
    return (
      <div className="ev tool_result">
        <span className="tag">result</span>{ev.tool_results[0].name} ✓
      </div>
    );
  }
  if (ev.type === "summary") return <div className="ev summary">{ev.text}</div>;
  if (ev.text) return <div className="ev text"><span className="tag">agent</span>{ev.text}</div>;
  return null;
}

/* ---------- How it works / FAQ ---------- */

const STEPS = [
  { n: 1, name: "Research", tool: "research_brand · ground_taxonomy",
    desc: "Reads your brand (ICP, geo, tone) and grounds it to real CashTime niches via Vertex AI Search — no made-up categories." },
  { n: 2, name: "Match", tool: "match_creators · enrich_creator",
    desc: "Finds the 10–15 best-fit creators in the network and refreshes their contact + audience data." },
  { n: 3, name: "Outreach", tool: "draft_outreach · schedule_sequence",
    desc: "Writes a personalised first message per creator and schedules a 3-step follow-up sequence. Drafts only — never sends." },
  { n: 4, name: "CRM", tool: "crm_upsert",
    desc: "Saves the brand, contacts and the campaign to the CRM and returns a link." },
];

const FAQ = [
  { q: "What is this, in one line?",
    a: "It turns a one-line brand brief into a ready-to-launch creator-marketing campaign in minutes — work that takes an account manager 2–3 days by hand." },
  { q: "Why is it useful?",
    a: "One brief in, a full campaign out: researched brand, matched creators, personalised outreach, scheduled follow-ups and a CRM record. Creators are the trusted bridge to their audience — we make reaching the right ones one click. And a human approves every message before anything is sent." },
  { q: "What do the four tabs show?",
    a: "Each tab is one agent's output, filled in live as it finishes: Research = the grounded brand profile, Match = the creators it picked, Outreach = the drafted messages + schedules, CRM = the record it would create. The Activity log tab is the raw tool-by-tool stream." },
  { q: "Is this real customer data?",
    a: "No. This public demo runs the synthetic \"Chapterhouse\" brand — no real customer data, and the CRM step writes nothing to production. No emails are ever sent." },
];

function HowItWorks() {
  return (
    <details className="how" open>
      <summary>ⓘ How it works — start here</summary>
      <div className="how-body">
        <div className="steps">
          {STEPS.map((s) => (
            <div className="step" key={s.n}>
              <div className="step-h"><span className="step-n">{s.n}</span>{s.name}</div>
              <div className="step-tool">{s.tool}</div>
              <div className="step-desc">{s.desc}</div>
            </div>
          ))}
        </div>
        <div className="agents-box">
          <div className="agents-title">Who does the work — and how they talk</div>
          <div className="agent-tree">
            <div className="planner">Planner · Gemini 3.1 Pro <span className="muted">— the conductor: runs the 4 steps in order, hands each result to the next</span></div>
            <div className="subs">
              <span className="sub-agent">research_agent</span>
              <span className="sub-agent">matching_agent</span>
              <span className="sub-agent">outreach_agent</span>
              <span className="muted">· Gemini 3.5 Flash</span>
            </div>
            <div className="muted small">
              The planner calls each sub-agent <b>as a tool</b> (agent-to-agent, ADK).
              Each sub-agent calls the real CashTime services <b>over MCP</b>. The planner
              does the final CRM write itself. Each tab above is one agent's output.
            </div>
          </div>
        </div>
        <div className="faq">
          {FAQ.map((f, i) => (
            <details className="faq-item" key={i}>
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </details>
  );
}
