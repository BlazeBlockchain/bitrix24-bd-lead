/* ============================================================
   WebApp.jsx — bd-lead standalone web app (bdlead.app)
   States: input → researching → result → pushed
   Exposes window.BDWebApp
   ============================================================ */

const RESEARCH_STEPS = [
  { k: "snapshot", label: "Company snapshot", sub: "Website · LinkedIn · news" },
  { k: "signal",   label: "Buying-signal scan", sub: "5 sources, priority order" },
  { k: "contact",  label: "Contact verification", sub: "2-source confirm" },
  { k: "email",    label: "Outreach email", sub: "Signal-matched, <90 words" },
  { k: "crm",      label: "CRM entry + follow-ups", sub: "Deal + 3 tasks" },
];

function Confidence({ level }) {
  const map = { HIGH: "#6ee7b7", MEDIUM: "#fcd576", LOW: "#f87171" };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: "var(--font-mono)",
      fontSize: 11, fontWeight: 600, color: map[level] }}>
      <Icon d="shield" size={13} /> {level}
    </span>
  );
}

function SidebarItem({ icon, label, active, badge, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 11, width: "100%",
      padding: "9px 11px", borderRadius: 9, border: "1px solid transparent",
      background: active ? "rgba(124,92,255,0.10)" : "transparent",
      borderColor: active ? "rgba(124,92,255,0.22)" : "transparent",
      color: active ? "#fff" : "var(--text-soft)", cursor: "pointer",
      font: "inherit", fontSize: 13.5, fontWeight: active ? 600 : 500,
      transition: "background .15s, color .15s",
    }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = "transparent"; }}>
      <span style={{ color: active ? "#b4a3ff" : "var(--muted)", display: "flex" }}><Icon d={icon} size={17} /></span>
      <span style={{ flex: 1, textAlign: "left" }}>{label}</span>
      {badge != null && <span className="chip" style={{ padding: "1px 7px", fontSize: 10 }}>{badge}</span>}
    </button>
  );
}

function FieldRow({ label, value, mono }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <span className="label" style={{ fontSize: 9.5 }}>{label}</span>
      <span style={{ fontSize: 13, color: "var(--text)", fontWeight: 500,
        fontFamily: mono ? "var(--font-mono)" : "inherit", wordBreak: "break-word" }}>{value}</span>
    </div>
  );
}

function MemoryCallout({ items, accent }) {
  const ic = { tone: "edit", cadence: "clock", icp: "target" };
  return (
    <div className="panel risein" style={{ padding: "var(--pad)", background: "var(--grad-soft)",
      borderColor: "rgba(124,92,255,0.22)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 13 }}>
        <span style={{ color: "#b4a3ff", display: "flex" }}><Icon d="memory" size={16} /></span>
        <span className="label label-accent" style={{ letterSpacing: "0.12em" }}>Your memory shaped this</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {items.map((m, i) => (
          <div key={i} style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
            <span style={{ color: "#7cdff0", marginTop: 1, display: "flex" }}><Icon d={ic[m.icon]} size={14} /></span>
            <span style={{ fontSize: 12.5, color: "var(--text-soft)", lineHeight: 1.55 }}>{m.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------- the tabbed Lead Brief ---------------- */
function LeadBrief({ lead, crm, plan, cadence }) {
  const [tab, setTab] = React.useState("brief");
  const tabs = [
    { k: "brief", label: "Full brief", icon: "doc" },
    { k: "email", label: "Email", icon: "mail" },
    { k: "crm", label: "CRM entry", icon: "grid" },
    { k: "plan", label: "Follow-ups", icon: "clock" },
  ];
  return (
    <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
      {/* tab bar */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--border)", padding: "0 6px" }}>
        {tabs.map((t) => (
          <button key={t.k} onClick={() => setTab(t.k)} style={{
            position: "relative", padding: "13px 14px", fontSize: 12.5, fontWeight: 500,
            color: tab === t.k ? "var(--text)" : "var(--muted)", background: "none", border: "none",
            cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 7, fontFamily: "inherit",
          }}>
            <Icon d={t.icon} size={14} /> {t.label}
            {tab === t.k && <span style={{ position: "absolute", left: 10, right: 10, bottom: -1, height: 2,
              background: "var(--grad)", borderRadius: 2 }} />}
          </button>
        ))}
      </div>

      <div className="scrollable" style={{ padding: "var(--pad)", maxHeight: 440 }}>
        {tab === "brief" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#6ee7b7",
              background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: 10, padding: "10px 12px" }}>
              <span style={{ color: "var(--muted)" }}>input · </span>
              Enrich lead: {lead.name}, {lead.email}
            </div>
            <div style={{ textAlign: "center", fontWeight: 700, fontSize: 13, letterSpacing: "0.1em",
              paddingBottom: 12, borderBottom: "1px solid var(--border)" }} className="gtext">
              LEAD BRIEF — {lead.company.toUpperCase()}
            </div>
            {[
              ["Company", lead.snapshot],
              ["Buying signal", <span><strong style={{ color: "var(--text)" }}>{lead.signal.source} ({lead.signal.date}):</strong> {lead.signal.text}</span>],
              ["Contact", <span><Confidence level={lead.contact.confidence} /> · {lead.contact.note}</span>],
            ].map(([h, body], i) => (
              <div key={i}>
                <div className="label label-accent" style={{ marginBottom: 5 }}>{h}</div>
                <div style={{ fontSize: 13.5, color: "var(--text-soft)", lineHeight: 1.7 }}>{body}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "email" && (
          <div className="risein">
            <div style={{ background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "13px 15px", borderBottom: "1px solid var(--border)" }}>
                <div style={{ display: "flex", gap: 8, fontSize: 12.5, marginBottom: 5 }}>
                  <span style={{ color: "var(--muted)", minWidth: 48 }}>To</span>
                  <span>{lead.name} · {lead.title}, {lead.company}</span>
                </div>
                <div style={{ display: "flex", gap: 8, fontSize: 12.5 }}>
                  <span style={{ color: "var(--muted)", minWidth: 48 }}>Subject</span>
                  <span style={{ fontWeight: 600 }}>{lead.outreach.subject}</span>
                </div>
              </div>
              <div style={{ padding: "15px", fontSize: 13.5, lineHeight: 1.8, color: "var(--text-soft)", whiteSpace: "pre-wrap" }}>
                {lead.outreach.body}
              </div>
            </div>
            <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span className="tag green"><Icon d="check" size={12} /> {lead.outreach.words} words</span>
              <span className="tag">{lead.outreach.angle}</span>
              <span className="tag green">No banned phrases</span>
            </div>
          </div>
        )}

        {tab === "crm" && (
          <div className="risein">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9 }}>
              {[
                ["Deal name", `${lead.company} — Dispatch Scaling`],
                ["Contact role", lead.title],
                ["Signal", `Hiring 3 dispatch roles (${lead.signal.source}, ${lead.signal.date})`],
                ["Pain point", "Follow-ups slipping between dispatch handoffs"],
                ["Pipeline", `${crm.name} · New Lead`],
                ["Confidence", lead.contact.confidence + " — 2 sources"],
              ].map(([l, v], i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.022)", border: "1px solid var(--border)",
                  borderRadius: 10, padding: "10px 12px" }}>
                  <div className="label" style={{ fontSize: 9 }}>{l}</div>
                  <div style={{ fontSize: 12.5, color: i === 5 ? "#6ee7b7" : "var(--text)", fontWeight: 600, marginTop: 4 }}>{v}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 9, background: "rgba(255,255,255,0.022)", border: "1px solid var(--border)",
              borderRadius: 10, padding: "10px 12px" }}>
              <div className="label" style={{ fontSize: 9 }}>Notes (pre-call)</div>
              <div style={{ fontSize: 12.5, color: "var(--text-soft)", lineHeight: 1.7, marginTop: 5 }}>
                • Rail-link expansion → frame around lane volume, not price<br />
                • Two+ roles open = budget exists, timeline tight<br />
                • Ops lead, not founder — anchor on booking speed + headcount relief
              </div>
            </div>
          </div>
        )}

        {tab === "plan" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 9 }}>
            <div className="label" style={{ marginBottom: 2 }}>Auto-scheduled · {cadence} cadence</div>
            {plan.map((t, i) => (
              <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", background: "rgba(255,255,255,0.022)",
                border: "1px solid var(--border)", borderRadius: 11, padding: "12px 13px" }}>
                <div style={{ width: 34, height: 34, borderRadius: 9, flexShrink: 0, display: "grid", placeItems: "center",
                  background: "var(--accent-soft)", border: "1px solid var(--accent-line)", color: "#b4a3ff" }}>
                  <Icon d={typeIcon[t.type]} size={16} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{t.title}</span>
                    <span className="chip chip-accent" style={{ padding: "1px 7px", fontSize: 9.5 }}>Day +{t.day}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-soft)", lineHeight: 1.55, marginBottom: 6 }}>{t.desc}</div>
                  <div style={{ fontSize: 11.5, color: "var(--muted)", lineHeight: 1.5, fontStyle: "italic",
                    borderLeft: "2px solid var(--accent-line)", paddingLeft: 9 }}>{t.script}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- main app ---------------- */
function BDWebApp({ t, onNav = () => {} }) {
  const crm = CRM[t.crm] || CRM.bitrix24;
  const plan = buildPlan(t.cadence);
  const [phase, setPhase] = React.useState("input"); // input | researching | result | pushed
  const [done, setDone] = React.useState(-1);
  const [form, setForm] = React.useState({ name: LEAD.name, email: LEAD.email, linkedin: LEAD.linkedin });
  const timers = React.useRef([]);

  const reset = () => { timers.current.forEach(clearTimeout); setPhase("input"); setDone(-1); };

  const research = () => {
    setPhase("researching"); setDone(-1);
    timers.current.forEach(clearTimeout); timers.current = [];
    RESEARCH_STEPS.forEach((_, i) => {
      timers.current.push(setTimeout(() => setDone(i), 520 * (i + 1)));
    });
    timers.current.push(setTimeout(() => setPhase("result"), 520 * (RESEARCH_STEPS.length + 1)));
  };

  React.useEffect(() => () => timers.current.forEach(clearTimeout), []);

  return (
    <div className="app" data-density={t.density} style={{ position: "relative", height: "100%", display: "flex",
      background: "var(--bg)", overflow: "hidden" }}>
      <div className="fieldbg" />

      <AppSidebar active="new" onNav={(k) => k === "new" ? reset() : onNav(k)} />

      {/* main */}
      <main style={{ position: "relative", zIndex: 1, flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <AppTopbar title="New lead" crm={crm}>
          <span className="chip chip-live"><span className="pulse-dot" /> AI live</span>
        </AppTopbar>

        <div className="scrollable" style={{ flex: 1, padding: "26px", display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ width: "100%", maxWidth: 920 }}>

            {phase === "input" && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                <div style={{ textAlign: "center", marginTop: 14 }}>
                  <h1 style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1.1 }}>
                    Paste a lead. <span className="gtext">Get a full brief.</span>
                  </h1>
                  <p style={{ color: "var(--text-soft)", fontSize: 14.5, marginTop: 10, maxWidth: 480, marginInline: "auto", lineHeight: 1.6 }}>
                    Name and email is enough. bd-lead researches the company, finds the buying signal, writes the opener, and drafts a 3-task plan — in seconds.
                  </p>
                </div>
                <div className="panel" style={{ padding: "var(--pad)", maxWidth: 560, width: "100%", marginInline: "auto" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 13 }}>
                    {[["Full name", "name", "Lena Vuković"], ["Work email", "email", "lena@company.hr"], ["LinkedIn (optional)", "linkedin", "linkedin.com/in/…"]].map(([lab, k, ph]) => (
                      <div key={k} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <span className="label label-accent">{lab}</span>
                        <input className="field" value={form[k]} placeholder={ph}
                          onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
                      </div>
                    ))}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginTop: 4 }}>
                      <span className="chip" style={{ color: crm.color }}>
                        <span className="chip-dot" style={{ color: crm.color }} /> Push to {crm.name}
                      </span>
                      <button className="btn btn-primary" onClick={research}>
                        <Icon d="spark" size={15} /> Research &amp; enrich
                      </button>
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap", marginTop: 2 }}>
                  {["<60s full brief", "5 research steps", "Remembers your tone", "3 follow-ups auto-dated"].map((s) => (
                    <span key={s} className="chip"><Icon d="check" size={11} /> {s}</span>
                  ))}
                </div>
              </div>
            )}

            {phase === "researching" && (
              <div className="risein" style={{ maxWidth: 520, marginInline: "auto", marginTop: 30 }}>
                <div style={{ textAlign: "center", marginBottom: 22 }}>
                  <div className="bd-mark" style={{ width: 44, height: 44, margin: "0 auto 14px", borderRadius: 12 }}>
                    <Icon d="spark" size={22} />
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>Researching {form.name.split(" ")[0]}…</div>
                  <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>{LEAD.companyDomain} · {crm.name}</div>
                </div>
                <div className="panel" style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: 4 }}>
                  {RESEARCH_STEPS.map((s, i) => {
                    const state = i <= done ? "done" : i === done + 1 ? "active" : "idle";
                    return (
                      <div key={s.k} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 6px",
                        opacity: state === "idle" ? 0.4 : 1, transition: "opacity .3s" }}>
                        <div style={{ width: 26, height: 26, borderRadius: 99, flexShrink: 0, display: "grid", placeItems: "center",
                          background: state === "done" ? "var(--grad)" : "rgba(255,255,255,0.04)",
                          border: "1px solid", borderColor: state === "done" ? "transparent" : "var(--border)",
                          color: state === "done" ? "#fff" : "var(--muted)" }}>
                          {state === "done" ? <Icon d="check" size={14} /> :
                           state === "active" ? <Icon d="refresh" size={13} style={{ animation: "spin .9s linear infinite" }} /> :
                           <span style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>{i + 1}</span>}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 13.5, fontWeight: 500, color: state === "idle" ? "var(--muted)" : "var(--text)" }}>{s.label}</div>
                          <div style={{ fontSize: 11.5, color: "var(--muted)" }}>{s.sub}</div>
                        </div>
                        {state === "active" && <span className="chip chip-accent" style={{ fontSize: 9.5 }}>working</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {(phase === "result" || phase === "pushed") && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {/* lead identity header */}
                <div className="panel" style={{ padding: "var(--pad)", display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
                  <div style={{ width: 48, height: 48, borderRadius: 13, background: "var(--grad)", display: "grid",
                    placeItems: "center", fontSize: 18, fontWeight: 700, color: "#fff", flexShrink: 0 }}>
                    {LEAD.name.split(" ").map((x) => x[0]).join("")}
                  </div>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 9, flexWrap: "wrap" }}>
                      <span style={{ fontSize: 18, fontWeight: 700 }}>{LEAD.name}</span>
                      <Confidence level={LEAD.contact.confidence} />
                    </div>
                    <div style={{ fontSize: 13, color: "var(--text-soft)", marginTop: 2 }}>
                      {LEAD.title} · {LEAD.company} · {LEAD.location}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <span className="chip chip-live"><Icon d="check" size={11} /> brief in 48s</span>
                    <span className="chip"><Icon d="search" size={11} /> {LEAD.sources} sources</span>
                  </div>
                </div>

                {/* two-column: brief + side rail */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16, alignItems: "start" }}>
                  <LeadBrief lead={LEAD} crm={crm} plan={plan} cadence={t.cadence} />

                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <MemoryCallout items={MEMORY} />
                    {/* enriched fields */}
                    <div className="panel" style={{ padding: "var(--pad)" }}>
                      <div className="label" style={{ marginBottom: 13 }}>Enriched contact</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 13 }}>
                        <FieldRow label="Company" value={LEAD.company} />
                        <FieldRow label="Industry" value={LEAD.industry} />
                        <FieldRow label="Headcount" value={LEAD.headcount} />
                        <FieldRow label="Founded" value={LEAD.founded} />
                        <div style={{ gridColumn: "1 / -1" }}><FieldRow label="Domain" value={LEAD.companyDomain} mono /></div>
                      </div>
                    </div>
                    {/* push panel */}
                    <div className="panel" style={{ padding: "var(--pad)" }}>
                      {phase === "pushed" ? (
                        <div className="risein" style={{ textAlign: "center" }}>
                          <div style={{ width: 40, height: 40, borderRadius: 99, margin: "0 auto 10px", display: "grid",
                            placeItems: "center", background: "var(--green-soft)", border: "1px solid var(--green-line)", color: "#6ee7b7" }}>
                            <Icon d="check" size={20} />
                          </div>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>Pushed to {crm.name}</div>
                          <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4, lineHeight: 1.5 }}>
                            Contact + Deal + 3 tasks created.<br />Memory updated with this lead.
                          </div>
                          <button className="btn btn-ghost btn-sm" style={{ marginTop: 13 }} onClick={reset}>
                            <Icon d="plus" size={13} /> Next lead
                          </button>
                        </div>
                      ) : (
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>Ready to push</div>
                          <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.55, marginBottom: 13 }}>
                            Creates Contact + Deal + 3 follow-up tasks in {crm.name}. Edit anything before you send.
                          </div>
                          <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => setPhase("pushed")}>
                            <Icon d="send" size={14} /> Push to {crm.name}
                          </button>
                          <button className="btn btn-quiet btn-sm" style={{ width: "100%", marginTop: 8 }}>
                            <Icon d="edit" size={12} /> Edit brief
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

window.BDWebApp = BDWebApp;
