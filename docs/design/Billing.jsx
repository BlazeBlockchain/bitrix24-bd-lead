/* ============================================================
   Billing.jsx — bd-lead web app · Billing & plan
   Uses the shared AppShell. Exposes window.BDBilling
   ============================================================ */

const PLANS = [
  {
    id: "free", name: "Free", price: "€0", per: "forever",
    blurb: "Your demo plan. Enough to feel the magic.",
    feats: ["25 AI enrichments / month", "Bitrix24 + HubSpot", "3-task follow-up plans", "Personal memory (tone + cadence)"],
    cta: "Current plan",
  },
  {
    id: "pro", name: "Pro", price: "€9", per: "/ user / month",
    blurb: "For reps running outreach every day.",
    feats: ["500 enrichments / month", "Pro model on demand (Sonnet-tier research)", "Priority enrichment queue", "Full memory + ICP profiles", "Email + LinkedIn signal scan"],
    cta: "Upgrade to Pro", popular: true,
  },
  {
    id: "team", name: "Team", price: "€7", per: "/ seat / month",
    blurb: "Shared playbook for the whole BD team.",
    feats: ["Everything in Pro", "Shared team memory & ICP", "Seat management + roles", "Usage analytics", "Priority support"],
    cta: "Choose Team",
  },
];

const INVOICES = [
  { date: "May 1, 2026", desc: "Free plan", amount: "€0.00", status: "—" },
  { date: "Apr 1, 2026", desc: "Free plan", amount: "€0.00", status: "—" },
  { date: "Mar 1, 2026", desc: "Free plan", amount: "€0.00", status: "—" },
];

function PlanCard({ plan, current, selected, onSelect }) {
  const active = selected === plan.id;
  return (
    <div onClick={() => onSelect(plan.id)} className="panel" style={{
      padding: "var(--pad)", position: "relative", cursor: "pointer",
      borderColor: active ? "rgba(124,92,255,0.5)" : plan.popular ? "var(--accent-line)" : "var(--border)",
      background: active ? "var(--grad-soft)" : "var(--panel)",
      boxShadow: active ? "0 0 0 1px rgba(124,92,255,0.4)" : "none",
      transition: "border-color .2s, background .2s, box-shadow .2s", display: "flex", flexDirection: "column", gap: 14,
    }}>
      {plan.popular && (
        <span className="chip chip-accent" style={{ position: "absolute", top: -10, right: 16, fontSize: 9.5 }}>
          <Icon d="star" size={11} /> Most popular
        </span>
      )}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>{plan.name}</span>
          {current === plan.id && <span className="chip chip-live" style={{ fontSize: 9 }}>current</span>}
        </div>
        <div style={{ fontSize: 12.5, color: "var(--text-soft)", marginTop: 4, lineHeight: 1.5 }}>{plan.blurb}</div>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 7 }}>
        <span style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-0.03em" }} className={plan.popular ? "gtext" : ""}>{plan.price}</span>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>{plan.per}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 9, flex: 1 }}>
        {plan.feats.map((f, i) => (
          <div key={i} style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
            <span style={{ color: "#6ee7b7", marginTop: 1, display: "flex" }}><Icon d="check" size={14} /></span>
            <span style={{ fontSize: 12.5, color: "var(--text-soft)", lineHeight: 1.5 }}>{f}</span>
          </div>
        ))}
      </div>
      <button className={"btn " + (current === plan.id ? "btn-ghost" : plan.popular ? "btn-primary" : "btn-ghost")}
        disabled={current === plan.id} style={{ width: "100%" }}>
        {current === plan.id ? "Current plan" : plan.cta}
      </button>
    </div>
  );
}

function BDBilling({ t, onNav = () => {} }) {
  const crm = CRM[t.crm] || CRM.bitrix24;
  const [selected, setSelected] = React.useState("pro");
  const current = "free";

  return (
    <div className="app" data-density={t.density} style={{ position: "relative", height: "100%", display: "flex",
      background: "var(--bg)", overflow: "hidden" }}>
      <div className="fieldbg" />
      <AppSidebar active="billing" onNav={onNav} />

      <main style={{ position: "relative", zIndex: 1, flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <AppTopbar title="Billing & plan" crm={crm} />

        <div className="scrollable" style={{ flex: 1, padding: "26px" }}>
          <div style={{ maxWidth: 940, margin: "0 auto", display: "flex", flexDirection: "column", gap: 18 }}>

            {/* usage banner */}
            <div className="panel risein" style={{ padding: "var(--pad)", display: "flex", alignItems: "center", gap: 22, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 260 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
                  <span className="label">Current usage</span>
                  <span className="chip" style={{ fontSize: 9.5 }}>Free plan</span>
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 10 }}>
                  <span style={{ fontSize: 26, fontWeight: 700, fontFamily: "var(--font-mono)" }}>12</span>
                  <span style={{ fontSize: 13, color: "var(--muted)" }}>/ 25 enrichments this month</span>
                </div>
                <div style={{ height: 7, borderRadius: 99, background: "rgba(255,255,255,0.06)", overflow: "hidden", maxWidth: 420 }}>
                  <div style={{ width: "48%", height: "100%", background: "var(--grad)", borderRadius: 99 }} />
                </div>
                <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 9 }}>Resets June 1 · 13 enrichments left</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 12, color: "var(--text-soft)", maxWidth: 200, lineHeight: 1.5, marginBottom: 10 }}>
                  Running low? Pro lifts you to 500 / month and unlocks deeper research.
                </div>
                <button className="btn btn-primary" onClick={() => setSelected("pro")}><Icon d="zap" size={14} /> Upgrade to Pro</button>
              </div>
            </div>

            {/* plans */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 13 }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>Plans</h2>
                <span className="chip"><Icon d="shield" size={11} /> Cancel anytime</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, alignItems: "stretch" }}>
                {PLANS.map((p) => <PlanCard key={p.id} plan={p} current={current} selected={selected} onSelect={setSelected} />)}
              </div>
              <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 12, textAlign: "center", lineHeight: 1.6 }}>
                Inference runs on cost-efficient models (Gemini 2.5 Flash + Haiku 4.5) — Pro adds Sonnet-tier research on demand for nuanced leads.
              </div>
            </div>

            {/* payment + history */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: 16, alignItems: "start" }}>
              <div className="panel" style={{ padding: "var(--pad)" }}>
                <div className="label" style={{ marginBottom: 14 }}>Payment method</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "13px", borderRadius: 11,
                  background: "rgba(255,255,255,0.022)", border: "1px solid var(--border)" }}>
                  <div style={{ width: 40, height: 28, borderRadius: 6, background: "var(--grad)", display: "grid", placeItems: "center", color: "#fff" }}>
                    <Icon d="card" size={16} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, fontFamily: "var(--font-mono)" }}>•••• 4242</div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>Stripe · test mode · exp 12/29</div>
                  </div>
                  <button className="btn btn-quiet btn-sm"><Icon d="edit" size={12} /> Edit</button>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginTop: 13, fontSize: 11.5, color: "var(--muted)" }}>
                  <Icon d="lock" size={12} /> Card details are stored by Stripe, never on our servers.
                </div>
              </div>

              <div className="panel" style={{ padding: "var(--pad)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                  <span className="label">Billing history</span>
                  <button className="btn btn-quiet btn-sm"><Icon d="download" size={12} /> Export</button>
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {INVOICES.map((inv, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 12, alignItems: "center",
                      padding: "11px 0", borderTop: i ? "1px solid var(--border)" : "none" }}>
                      <div>
                        <div style={{ fontSize: 12.5, fontWeight: 500 }}>{inv.desc}</div>
                        <div style={{ fontSize: 11, color: "var(--muted)" }}>{inv.date}</div>
                      </div>
                      <span style={{ fontSize: 12.5, fontFamily: "var(--font-mono)", color: "var(--text-soft)" }}>{inv.amount}</span>
                      <button className="btn btn-quiet btn-sm" style={{ padding: 5 }}><Icon d="doc" size={13} /></button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

window.BDBilling = BDBilling;
