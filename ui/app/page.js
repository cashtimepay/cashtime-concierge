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

function fmtNum(n) {
  if (n == null) return "—";
  return Intl.NumberFormat("en-US").format(n);
}

export default function Home() {
  const [brandUrl, setBrandUrl] = useState("");
  const [goal, setGoal] = useState("");
  const [budget, setBudget] = useState(5000);
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [apiBase, setApiBase] = useState(BUILD_API_BASE);
  const logRef = useRef(null);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((c) => {
        if (c.apiBase) setApiBase(c.apiBase);
      })
      .catch(() => {});
  }, []);

  function pushEvent(ev) {
    setEvents((prev) => {
      const next = [...prev, ev];
      queueMicrotask(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
      });
      return next;
    });
  }

  async function run(payload) {
    setEvents([]);
    setSummary(null);
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
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const dataLine = frame
            .split("\n")
            .find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          let ev;
          try {
            ev = JSON.parse(dataLine.slice(5).trim());
          } catch {
            continue;
          }
          if (ev.type === "summary_data") {
            setSummary(ev.data);
          } else if (ev.type === "done") {
            // handled by stream end
          } else {
            pushEvent(ev);
          }
        }
      }
      setStatus("done");
    } catch (err) {
      pushEvent({ type: "text", text: `Error: ${err.message}` });
      setStatus("error");
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    run({
      brand_url: brandUrl,
      goal,
      budget_monthly_usd: Number(budget),
    });
  }

  function runDemo() {
    setBrandUrl(DEMO_PRESET.brand_url);
    setGoal(DEMO_PRESET.goal);
    setBudget(DEMO_PRESET.budget_monthly_usd);
    run(DEMO_PRESET);
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
          <input
            id="brand"
            placeholder="https://your-brand.com"
            value={brandUrl}
            onChange={(e) => setBrandUrl(e.target.value)}
            disabled={running}
          />
          <label htmlFor="goal">Goal</label>
          <textarea
            id="goal"
            rows={3}
            placeholder="e.g. 100 trial signups per month"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={running}
          />
          <label htmlFor="budget">Monthly creator budget (USD)</label>
          <input
            id="budget"
            type="number"
            min={0}
            step={500}
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            disabled={running}
          />
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
          <h2>
            <span className={`dot ${status === "running" ? "run" : status === "done" ? "done" : "idle"}`} />
            Live run
          </h2>
          <div className="log" ref={logRef}>
            {events.length === 0 && (
              <div className="empty">
                Submit a brief or click <b>Run the Chapterhouse demo</b> to watch
                the agent work.
              </div>
            )}
            {events.map((ev, i) => (
              <LogLine key={i} ev={ev} />
            ))}
          </div>

          {summary && <SummaryCard s={summary} />}
        </div>
      </div>

      <p className="foot">
        CashTime Pay AG · Switzerland — drafts and schedules only; a human
        approves every message. Demo data is synthetic.
      </p>
    </div>
  );
}

function LogLine({ ev }) {
  if (ev.type === "tool_call" && ev.tool_calls?.length) {
    const tc = ev.tool_calls[0];
    return (
      <div className="ev tool_call">
        <span className="tag">call</span>
        <span className="arrow">→</span> {tc.name}
      </div>
    );
  }
  if (ev.type === "tool_result" && ev.tool_results?.length) {
    const tr = ev.tool_results[0];
    return (
      <div className="ev tool_result">
        <span className="tag">result</span>
        {tr.name} ✓
      </div>
    );
  }
  if (ev.type === "summary") {
    return <div className="ev summary">{ev.text}</div>;
  }
  if (ev.text) {
    return (
      <div className="ev text">
        <span className="tag">agent</span>
        {ev.text}
      </div>
    );
  }
  return null;
}

function SummaryCard({ s }) {
  return (
    <div className="summary-card">
      <h3>{s.brand} — campaign ready</h3>
      <div>
        {(s.categories || []).slice(0, 4).map((c) => (
          <span className="pill" key={c}>{c}</span>
        ))}
        {(s.geo || []).map((g) => (
          <span className="pill" key={g}>{g}</span>
        ))}
        <span className="pill">grounding: {s.grounding_backend}</span>
      </div>

      {s.creators?.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div className="creator head">
            <span>Creator</span><span>Niche</span><span>Followers</span><span>Fit</span><span>Geo</span>
          </div>
          {s.creators.map((c, i) => (
            <div className="creator" key={i}>
              <span>{c.handle}</span>
              <span>{c.niche}</span>
              <span>{fmtNum(c.follower_count)}</span>
              <span>{c.fit_score != null ? c.fit_score.toFixed(2) : "—"}</span>
              <span>{c.geo || "—"}</span>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12, color: "var(--muted)", fontSize: 13 }}>
        {s.drafts_ready} outreach sequences drafted and scheduled — awaiting your approval.
      </div>

      {s.crm_url && (
        <a className="crm-link" href={s.crm_url} target="_blank" rel="noreferrer">
          Open in CRM →
        </a>
      )}
    </div>
  );
}

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
  { q: "What am I watching in the live log?",
    a: "Every \"call → tool\" / \"result ✓\" line is a real step the agents take, streamed as it happens: research_brand → ground_taxonomy → match_creators → enrich_creator (×N) → draft_outreach (×N) → schedule_sequence (×N) → crm_upsert." },
  { q: "Is this real customer data?",
    a: "No. This public demo runs the synthetic \"Chapterhouse\" brand — no real customer data and no emails are ever sent." },
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
              Each sub-agent calls the real CashTime services <b>over MCP</b>. The
              planner does the final CRM write itself.
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
