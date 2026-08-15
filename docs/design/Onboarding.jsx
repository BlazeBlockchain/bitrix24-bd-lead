/* ============================================================
   Onboarding.jsx — bd-lead first-run: sign up → connect CRM → personalize → ready
   Full-screen two-column flow (no app sidebar). Exposes window.BDOnboarding
   ============================================================ */

const OB_STEPS = ["Connect CRM", "Authorize", "Personalize", "Ready"];

const CRM_OPTIONS = [
  { id: "bitrix24", name: "Bitrix24", color: "var(--accent3)", desc: "Webhook or OAuth", ready: true },
  { id: "hubspot", name: "HubSpot", color: "var(--gold)", desc: "Connect with OAuth", ready: true },
  { id: "pipedrive", name: "Pipedrive", color: "var(--muted)", desc: "Coming soon", ready: false },
];

function StepRail({ step }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {OB_STEPS.map((s, i) => {
        const state = i < step ? "done" : i === step ? "active" : "idle";
        return (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", opacity: state === "idle" ? 0.45 : 1, transition: "opacity .25s" }}>
            <div style={{ width: 26, height: 26, borderRadius: 99, flexShrink: 0, display: "grid", placeItems: "center",
              background: state === "done" ? "var(--grad)" : state === "active" ? "rgba(124,92,255,0.12)" : "rgba(255,255,255,0.05)",
              border: "1px solid", borderColor: state === "active" ? "var(--accent-line)" : state === "done" ? "transparent" : "var(--border)",
              color: state === "done" ? "#fff" : state === "active" ? "#b4a3ff" : "var(--muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
              {state === "done" ? <Icon d="check" size={13} /> : i + 1}
            </div>
            <span style={{ fontSize: 13.5, fontWeight: state === "active" ? 600 : 500, color: state === "idle" ? "var(--muted)" : "var(--text)" }}>{s}</span>
          </div>
        );
      })}
    </div>
  );
}

function BDOnboarding({ t, onNav = () => {} }) {
  const [step, setStep] = React.useState(0);
  const [crmId, setCrmId] = React.useState(t.crm || "bitrix24");
  const [connecting, setConnecting] = React.useState(false);
  const [connected, setConnected] = React.useState(false);
  const [cadence, setCadence] = React.useState(t.cadence || "4/9/14");
  const [icp, setIcp] = React.useState("Croatian logistics & freight, 100–250 staff");
  const crm = CRM_OPTIONS.find((c) => c.id === crmId) || CRM_OPTIONS[0];
  const timer = React.useRef();

  const doConnect = () => {
    setConnecting(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => { setConnecting(false); setConnected(true); }, 1500);
  };
  React.useEffect(() => () => clearTimeout(timer.current), []);

  return (
    <div className="app" data-density={t.density} style={{ position: "relative", height: "100%", display: "flex",
      background: "var(--bg)", overflow: "hidden" }}>
      <div className="fieldbg" />

      {/* left brand rail */}
      <aside style={{ position: "relative", zIndex: 1, width: 320, flexShrink: 0, borderRight: "1px solid var(--border)",
        background: "rgba(255,255,255,0.012)", padding: "32px 30px", display: "flex", flexDirection: "column" }}>
        <div className="bd-logo" style={{ fontSize: 16, marginBottom: 34 }}>
          <span className="bd-mark"><Icon d="bolt" size={15} /></span>
          <span>bd<span style={{ color: "#b4a3ff" }}>·</span>lead</span>
        </div>
        <div style={{ fontSize: 21, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1.25, marginBottom: 8 }}>
          Set up bd-lead <span className="gtext">in 2 minutes.</span>
        </div>
        <div style={{ fontSize: 13, color: "var(--text-soft)", lineHeight: 1.6, marginBottom: 30 }}>
          Connect your CRM, teach it your style, and you're ready to turn any name into a complete lead brief.
        </div>
        <StepRail step={connected && step === 1 ? 1 : step} />
        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 11 }}>
          {["No webhooks or code to wire up", "Your CRM token is encrypted at rest", "Free to start — 25 leads / month"].map((s) => (
            <div key={s} style={{ display: "flex", gap: 9, alignItems: "center", fontSize: 12, color: "var(--text-soft)" }}>
              <span style={{ color: "#6ee7b7", display: "flex" }}><Icon d="check" size={14} /></span> {s}
            </div>
          ))}
        </div>
      </aside>

      {/* right step content */}
      <main style={{ position: "relative", zIndex: 1, flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div className="scrollable" style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "30px" }}>
          <div style={{ width: "100%", maxWidth: 480 }}>

            {/* STEP 0 — choose CRM */}
            {step === 0 && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                <div>
                  <div className="label label-accent" style={{ marginBottom: 8 }}>Step 1 of 4</div>
                  <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" }}>Which CRM do you use?</h1>
                  <p style={{ fontSize: 13.5, color: "var(--text-soft)", marginTop: 7, lineHeight: 1.6 }}>
                    bd-lead pushes contacts, deals and tasks straight into it. Pick one to start — you can add more later.
                  </p>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {CRM_OPTIONS.map((c) => (
                    <button key={c.id} disabled={!c.ready} onClick={() => c.ready && setCrmId(c.id)} className="panel" style={{
                      display: "flex", alignItems: "center", gap: 14, padding: "15px 16px", textAlign: "left", cursor: c.ready ? "pointer" : "not-allowed",
                      opacity: c.ready ? 1 : 0.5, fontFamily: "inherit", color: "var(--text)",
                      borderColor: crmId === c.id ? "rgba(124,92,255,0.5)" : "var(--border)",
                      background: crmId === c.id ? "var(--grad-soft)" : "var(--panel)",
                    }}>
                      <div style={{ width: 36, height: 36, borderRadius: 9, background: c.color, opacity: 0.92, flexShrink: 0,
                        display: "grid", placeItems: "center", color: "#06121a", fontWeight: 700, fontSize: 14 }}>{c.name[0]}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{c.name}</div>
                        <div style={{ fontSize: 12, color: "var(--muted)" }}>{c.desc}</div>
                      </div>
                      <div style={{ width: 20, height: 20, borderRadius: 99, border: "1px solid", display: "grid", placeItems: "center",
                        borderColor: crmId === c.id ? "transparent" : "var(--border)", background: crmId === c.id ? "var(--grad)" : "transparent", color: "#fff" }}>
                        {crmId === c.id && <Icon d="check" size={12} />}
                      </div>
                    </button>
                  ))}
                </div>
                <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => { setConnected(false); setStep(1); }}>
                  Continue <Icon d="arrow" size={14} />
                </button>
              </div>
            )}

            {/* STEP 1 — authorize */}
            {step === 1 && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                <div>
                  <div className="label label-accent" style={{ marginBottom: 8 }}>Step 2 of 4</div>
                  <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" }}>Connect {crm.name}</h1>
                  <p style={{ fontSize: 13.5, color: "var(--text-soft)", marginTop: 7, lineHeight: 1.6 }}>
                    {crmId === "bitrix24"
                      ? "Authorize with one click, or paste an inbound webhook URL if your admin gave you one."
                      : "Sign in to HubSpot and approve access. We only read and write the records you push through bd-lead."}
                  </p>
                </div>

                {!connected ? (
                  <div className="panel" style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: 14 }}>
                    <button className="btn btn-primary" style={{ width: "100%" }} disabled={connecting} onClick={doConnect}>
                      {connecting
                        ? <React.Fragment><Icon d="refresh" size={14} style={{ animation: "spin .9s linear infinite" }} /> Connecting…</React.Fragment>
                        : <React.Fragment><Icon d="link" size={14} /> Authorize {crm.name}</React.Fragment>}
                    </button>
                    {crmId === "bitrix24" && (
                      <React.Fragment>
                        <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--muted)", fontSize: 11 }}>
                          <div style={{ flex: 1, height: 1, background: "var(--border)" }} /> OR PASTE WEBHOOK <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          <input className="field" placeholder="https://your-co.bitrix24.eu/rest/1/xxxx/" style={{ fontFamily: "var(--font-mono)", fontSize: 12 }} />
                          <span style={{ fontSize: 11, color: "var(--muted)", display: "flex", alignItems: "center", gap: 6 }}>
                            <Icon d="search" size={11} /> Where do I find this? — Bitrix24 → Developer resources → Inbound webhook
                          </span>
                        </div>
                      </React.Fragment>
                    )}
                  </div>
                ) : (
                  <div className="panel risein" style={{ padding: "var(--pad)", display: "flex", alignItems: "center", gap: 14,
                    background: "var(--green-soft)", borderColor: "var(--green-line)" }}>
                    <div style={{ width: 40, height: 40, borderRadius: 99, display: "grid", placeItems: "center",
                      background: "rgba(16,185,129,0.15)", color: "#6ee7b7", flexShrink: 0 }}><Icon d="check" size={20} /></div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{crm.name} connected</div>
                      <div style={{ fontSize: 12, color: "var(--text-soft)" }}>Token encrypted &amp; stored. You can revoke anytime in Settings.</div>
                    </div>
                  </div>
                )}

                <div style={{ display: "flex", gap: 10 }}>
                  <button className="btn btn-ghost" onClick={() => setStep(0)}>Back</button>
                  <button className="btn btn-primary" style={{ flex: 1 }} disabled={!connected} onClick={() => setStep(2)}>
                    Continue <Icon d="arrow" size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2 — personalize (memory) */}
            {step === 2 && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                <div>
                  <div className="label label-accent" style={{ marginBottom: 8 }}>Step 3 of 4</div>
                  <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" }}>Teach bd-lead your style</h1>
                  <p style={{ fontSize: 13.5, color: "var(--text-soft)", marginTop: 7, lineHeight: 1.6 }}>
                    This seeds your memory so the very first brief sounds like you. It keeps learning from every lead you push.
                  </p>
                </div>
                <div className="panel" style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <span className="label label-accent">Default follow-up cadence</span>
                    <div style={{ display: "flex", gap: 8 }}>
                      {["4/9/14", "3/7/14", "2/5/10"].map((c) => (
                        <button key={c} onClick={() => setCadence(c)} className="btn btn-sm" style={{ flex: 1,
                          background: cadence === c ? "var(--grad)" : "rgba(255,255,255,0.03)", color: cadence === c ? "#fff" : "var(--text-soft)",
                          border: "1px solid", borderColor: cadence === c ? "transparent" : "var(--border)", fontFamily: "var(--font-mono)" }}>
                          {c}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                    <span className="label label-accent">Who's your ideal customer?</span>
                    <input className="field" value={icp} onChange={(e) => setIcp(e.target.value)} />
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                    <span className="label label-accent">Paste a past email you're proud of <span style={{ color: "var(--muted)", textTransform: "none", letterSpacing: 0 }}>· optional</span></span>
                    <textarea className="field" rows={3} placeholder="We learn your tone, length and sign-off from this — never sent anywhere."
                      style={{ resize: "none", fontFamily: "inherit" }} />
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <button className="btn btn-quiet" onClick={() => setStep(3)}>Skip for now</button>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => setStep(3)}>
                    Save &amp; finish <Icon d="arrow" size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3 — ready */}
            {step === 3 && (
              <div className="risein" style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: 16 }}>
                <div className="bd-mark" style={{ width: 56, height: 56, borderRadius: 16 }}><Icon d="check" size={28} /></div>
                <div>
                  <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em" }}>You're all set, Marko.</h1>
                  <p style={{ fontSize: 14, color: "var(--text-soft)", marginTop: 9, lineHeight: 1.6, maxWidth: 380 }}>
                    {crm.name} is connected and bd-lead knows your {cadence} cadence. Paste your first lead and watch it build the full brief.
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
                  <span className="chip" style={{ color: crm.color }}><span className="chip-dot" style={{ color: crm.color }} /> {crm.name}</span>
                  <span className="chip"><Icon d="clock" size={11} /> {cadence} cadence</span>
                  <span className="chip"><Icon d="memory" size={11} /> Memory primed</span>
                </div>
                <button className="btn btn-primary" style={{ marginTop: 4 }} onClick={() => onNav("new")}>
                  <Icon d="spark" size={15} /> Paste your first lead
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

window.BDOnboarding = BDOnboarding;
