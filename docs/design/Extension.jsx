/* ============================================================
   Extension.jsx — bd-lead Chrome/Firefox MV3 extension
   Two surfaces: ExtPopup (toolbar popup) + ExtInPage (injected panel)
   Exposes window.ExtPopup, window.ExtInPage
   ============================================================ */

function Conf({ level }) {
  const map = { HIGH: "#6ee7b7", MEDIUM: "#fcd576", LOW: "#f87171" };
  return <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontFamily: "var(--font-mono)",
    fontSize: 10, fontWeight: 600, color: map[level] }}><Icon d="shield" size={11} /> {level}</span>;
}

// condensed brief used in both popup & in-page panel
function MiniBrief({ lead, crm, plan, cadence, pushed, onPush, onReset }) {
  const [tab, setTab] = React.useState("signal");
  const tabs = [["signal", "Signal"], ["email", "Email"], ["plan", "Plan"]];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
      {/* identity */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 34, height: 34, borderRadius: 10, background: "var(--grad)", display: "grid",
          placeItems: "center", fontSize: 13, fontWeight: 700, color: "#fff", flexShrink: 0 }}>
          {lead.name.split(" ").map((x) => x[0]).join("")}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <span style={{ fontSize: 13.5, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{lead.name}</span>
            <Conf level={lead.contact.confidence} />
          </div>
          <div style={{ fontSize: 11.5, color: "var(--text-soft)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {lead.title} · {lead.company}
          </div>
        </div>
      </div>

      {/* mini tabs */}
      <div style={{ display: "flex", gap: 4, background: "rgba(255,255,255,0.03)", padding: 3, borderRadius: 9, border: "1px solid var(--border)" }}>
        {tabs.map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} style={{ flex: 1, padding: "6px 0", fontSize: 11.5, fontWeight: 600,
            border: "none", borderRadius: 7, cursor: "pointer", fontFamily: "inherit",
            background: tab === k ? "var(--grad)" : "transparent", color: tab === k ? "#fff" : "var(--text-soft)" }}>{l}</button>
        ))}
      </div>

      <div style={{ background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 11, padding: 13, minHeight: 132 }}>
        {tab === "signal" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 9 }}>
            <span className="tag gold" style={{ alignSelf: "flex-start" }}><Icon d="bolt" size={11} /> {lead.signal.source} · {lead.signal.date}</span>
            <div style={{ fontSize: 12.5, color: "var(--text-soft)", lineHeight: 1.6 }}>{lead.signal.text}</div>
          </div>
        )}
        {tab === "email" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
            <div style={{ fontSize: 12.5, fontWeight: 600 }}>{lead.outreach.subject}</div>
            <div style={{ fontSize: 12, color: "var(--text-soft)", lineHeight: 1.65, whiteSpace: "pre-wrap",
              maxHeight: 96, overflow: "hidden" }}>{lead.outreach.body}</div>
            <span className="tag green" style={{ alignSelf: "flex-start" }}><Icon d="check" size={10} /> {lead.outreach.words} words</span>
          </div>
        )}
        {tab === "plan" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
            {plan.map((p, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 9 }}>
                <span style={{ width: 26, height: 26, borderRadius: 8, flexShrink: 0, display: "grid", placeItems: "center",
                  background: "var(--accent-soft)", border: "1px solid var(--accent-line)", color: "#b4a3ff" }}>
                  <Icon d={typeIcon[p.type]} size={13} />
                </span>
                <span style={{ flex: 1, fontSize: 12, color: "var(--text-soft)" }}>{p.title}</span>
                <span className="chip chip-accent" style={{ fontSize: 9, padding: "1px 6px" }}>+{p.day}d</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* memory line */}
      <div style={{ display: "flex", gap: 7, alignItems: "center", padding: "8px 10px", borderRadius: 9,
        background: "var(--grad-soft)", border: "1px solid rgba(124,92,255,0.22)" }}>
        <span style={{ color: "#b4a3ff", display: "flex" }}><Icon d="memory" size={13} /></span>
        <span style={{ fontSize: 11, color: "var(--text-soft)", lineHeight: 1.4 }}>Matched your tone &amp; {cadence} cadence from past leads.</span>
      </div>

      {pushed ? (
        <div className="risein" style={{ display: "flex", alignItems: "center", gap: 9, padding: "10px 12px", borderRadius: 10,
          background: "var(--green-soft)", border: "1px solid var(--green-line)" }}>
          <span style={{ color: "#6ee7b7", display: "flex" }}><Icon d="check" size={16} /></span>
          <span style={{ fontSize: 12.5, color: "#6ee7b7", fontWeight: 600, flex: 1 }}>Pushed to {crm.name} — Contact + Deal + 3 tasks</span>
          <button onClick={onReset} className="btn btn-quiet btn-sm" style={{ padding: 4 }}><Icon d="plus" size={13} /></button>
        </div>
      ) : (
        <button className="btn btn-primary" style={{ width: "100%" }} onClick={onPush}>
          <Icon d="send" size={14} /> Push to {crm.name}
        </button>
      )}
    </div>
  );
}

/* ---------------- toolbar POPUP ---------------- */
function ExtPopup({ t }) {
  const crm = CRM[t.crm] || CRM.bitrix24;
  const plan = buildPlan(t.cadence);
  const [phase, setPhase] = React.useState("input"); // input | gen | result | pushed
  const [form, setForm] = React.useState({ name: LEAD.name, email: LEAD.email });
  const timer = React.useRef();

  const gen = () => { setPhase("gen"); clearTimeout(timer.current); timer.current = setTimeout(() => setPhase("result"), 1700); };
  const reset = () => { clearTimeout(timer.current); setPhase("input"); };
  React.useEffect(() => () => clearTimeout(timer.current), []);

  return (
    <div className="ext" data-density="compact" style={{ position: "relative", width: "100%", height: "100%",
      background: "var(--bg)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div className="fieldbg" />
      {/* popup header */}
      <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "13px 15px", borderBottom: "1px solid var(--border)" }}>
        <div className="bd-logo" style={{ fontSize: 13.5 }}>
          <span className="bd-mark" style={{ width: 23, height: 23 }}><Icon d="bolt" size={13} /></span>
          <span>bd<span style={{ color: "#b4a3ff" }}>·</span>lead</span>
        </div>
        <span className="chip" style={{ color: crm.color, fontSize: 10 }}>
          <span className="chip-dot" style={{ color: crm.color }} /> {crm.name}
        </span>
      </div>

      <div className="scrollable" style={{ position: "relative", zIndex: 1, flex: 1, padding: 15 }}>
        {phase === "input" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.02em" }}>Enrich a lead</div>
              <div style={{ fontSize: 11.5, color: "var(--text-soft)", marginTop: 3, lineHeight: 1.5 }}>
                Detected <strong style={{ color: "var(--text)" }}>{crm.name}</strong> tab — fields pre-filled from the open record.
              </div>
            </div>
            {[["Name", "name"], ["Email", "email"]].map(([lab, k]) => (
              <div key={k} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                <span className="label label-accent" style={{ fontSize: 9 }}>{lab}</span>
                <input className="field" style={{ fontSize: 12.5, padding: "9px 11px" }} value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
              </div>
            ))}
            <button className="btn btn-primary" style={{ width: "100%", marginTop: 2 }} onClick={gen}>
              <Icon d="spark" size={14} /> Research &amp; enrich
            </button>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "center" }}>
              {["<60s", "remembers you", "3 tasks"].map((s) => (
                <span key={s} className="chip" style={{ fontSize: 9 }}><Icon d="check" size={9} /> {s}</span>
              ))}
            </div>
          </div>
        )}

        {phase === "gen" && (
          <div className="risein" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            height: "100%", gap: 14, textAlign: "center" }}>
            <div className="bd-mark" style={{ width: 40, height: 40, borderRadius: 12 }}>
              <Icon d="refresh" size={19} style={{ animation: "spin .9s linear infinite" }} />
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Researching {form.name.split(" ")[0]}…</div>
              <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 4 }}>Snapshot · signal · contact · email · tasks</div>
            </div>
            <div style={{ width: "70%", height: 4, borderRadius: 99, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
              <div style={{ height: "100%", background: "var(--grad)", borderRadius: 99, animation: "loadbar 1.7s ease forwards" }} />
            </div>
            <style>{`@keyframes loadbar{from{width:6%}to{width:100%}}`}</style>
          </div>
        )}

        {(phase === "result" || phase === "pushed") && (
          <div className="risein">
            <MiniBrief lead={LEAD} crm={crm} plan={plan} cadence={t.cadence}
              pushed={phase === "pushed"} onPush={() => setPhase("pushed")} onReset={reset} />
            <button className="btn btn-quiet btn-sm" style={{ width: "100%", marginTop: 9 }}>
              <Icon d="arrow" size={12} /> Open full brief in web app
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- in-page INJECTED panel ---------------- */
function ExtInPage({ t }) {
  const crm = CRM[t.crm] || CRM.bitrix24;
  const plan = buildPlan(t.cadence);
  const [open, setOpen] = React.useState(true);
  const [phase, setPhase] = React.useState("result"); // result | pushed (panel opens already enriched from the page)

  return (
    <div className="inpage" style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden",
      background: "#0d1117", display: "flex", flexDirection: "column" }}>
      {/* fake CRM/LinkedIn record behind */}
      <div style={{ height: 46, flexShrink: 0, background: "#161b22", borderBottom: "1px solid rgba(255,255,255,0.08)",
        display: "flex", alignItems: "center", gap: 12, padding: "0 18px" }}>
        <div style={{ width: 22, height: 22, borderRadius: 6, background: crm.color, opacity: 0.9 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "#c9d1d9" }}>{crm.name}</span>
        <span style={{ fontSize: 12, color: "#8b949e" }}>· Contacts · Lena Vuković</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <div style={{ width: 60, height: 9, borderRadius: 99, background: "rgba(255,255,255,0.07)" }} />
          <div style={{ width: 24, height: 24, borderRadius: 99, background: "rgba(255,255,255,0.1)" }} />
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* page body skeleton */}
        <div style={{ flex: 1, padding: 24, display: "flex", flexDirection: "column", gap: 16, filter: open ? "blur(1.5px)" : "none",
          opacity: open ? 0.55 : 1, transition: "filter .3s, opacity .3s" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 56, height: 56, borderRadius: 99, background: "rgba(255,255,255,0.1)" }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              <div style={{ width: 160, height: 14, borderRadius: 6, background: "rgba(255,255,255,0.12)" }} />
              <div style={{ width: 210, height: 10, borderRadius: 6, background: "rgba(255,255,255,0.06)" }} />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{ height: 54, borderRadius: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }} />
            ))}
          </div>
          <div style={{ height: 90, borderRadius: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }} />
        </div>

        {/* injected floating button */}
        {!open && (
          <button onClick={() => setOpen(true)} className="btn btn-primary risein" style={{ position: "absolute", right: 22, bottom: 22, boxShadow: "var(--glow-accent-hover)" }}>
            <Icon d="bolt" size={15} /> Enrich with bd-lead
          </button>
        )}

        {/* slide-in panel */}
        {open && (
          <div style={{ width: 348, flexShrink: 0, background: "var(--bg)", borderLeft: "1px solid var(--border)",
            position: "relative", display: "flex", flexDirection: "column", boxShadow: "-20px 0 50px rgba(0,0,0,0.5)" }}
            className="risein">
            <div className="fieldbg" />
            <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "13px 15px", borderBottom: "1px solid var(--border)" }}>
              <div className="bd-logo" style={{ fontSize: 13 }}>
                <span className="bd-mark" style={{ width: 22, height: 22 }}><Icon d="bolt" size={12} /></span>
                <span>bd<span style={{ color: "#b4a3ff" }}>·</span>lead</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="chip chip-live" style={{ fontSize: 9 }}><span className="pulse-dot" /> enriched</span>
                <button onClick={() => setOpen(false)} className="btn btn-quiet btn-sm" style={{ padding: 5 }}><Icon d="x" size={14} /></button>
              </div>
            </div>
            <div className="scrollable" style={{ position: "relative", zIndex: 1, flex: 1, padding: 15 }}>
              <div style={{ fontSize: 11.5, color: "var(--text-soft)", marginBottom: 12, lineHeight: 1.5 }}>
                Read this record from the {crm.name} tab and enriched it — no paste needed.
              </div>
              <MiniBrief lead={LEAD} crm={crm} plan={plan} cadence={t.cadence}
                pushed={phase === "pushed"} onPush={() => setPhase("pushed")} onReset={() => setPhase("result")} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { ExtPopup, ExtInPage });
