/* ============================================================
   Shell.jsx — shared app chrome (sidebar + topbar) for the web app.
   Used by WebApp, Billing (and any other logged-in screen).
   Exposes window.AppSidebar, window.AppTopbar
   ============================================================ */

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

function AppSidebar({ active = "new", onNav = () => {}, usage = { used: 12, cap: 25 }, plan = "Free plan" }) {
  const nav = [
    ["new", "search", "New lead"],
    ["leads", "layers", "Leads", "38"],
    ["memory", "memory", "Memory"],
    ["billing", "card", "Billing"],
    ["settings", "settings", "Settings"],
  ];
  return (
    <aside style={{ position: "relative", zIndex: 1, width: 232, flexShrink: 0, borderRight: "1px solid var(--border)",
      background: "rgba(255,255,255,0.012)", display: "flex", flexDirection: "column", padding: "18px 14px" }}>
      <div className="bd-logo" style={{ padding: "4px 6px 18px", fontSize: 15 }}>
        <span className="bd-mark"><Icon d="bolt" size={15} /></span>
        <span>bd<span style={{ color: "#b4a3ff" }}>·</span>lead</span>
      </div>
      <button className="btn btn-primary" onClick={() => onNav("new")} style={{ marginBottom: 16 }}>
        <Icon d="plus" size={15} /> New lead
      </button>
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {nav.map(([k, ic, lab, bdg]) => (
          <SidebarItem key={k} icon={ic} label={lab} badge={bdg} active={active === k} onClick={() => onNav(k)} />
        ))}
      </div>
      <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
        <div className="panel" style={{ padding: 12, background: "rgba(255,255,255,0.02)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 }}>
            <span className="label" style={{ fontSize: 9 }}>{plan}</span>
            <span style={{ fontSize: 11, color: "var(--text-soft)", fontFamily: "var(--font-mono)" }}>{usage.used} / {usage.cap}</span>
          </div>
          <div style={{ height: 5, borderRadius: 99, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
            <div style={{ width: `${(usage.used / usage.cap) * 100}%`, height: "100%", background: "var(--grad)", borderRadius: 99 }} />
          </div>
          <button className="btn btn-ghost btn-sm" style={{ width: "100%", marginTop: 10 }} onClick={() => onNav("billing")}>Upgrade</button>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "2px 4px" }}>
          <div style={{ width: 30, height: 30, borderRadius: 99, background: "var(--grad)", display: "grid",
            placeItems: "center", fontSize: 12, fontWeight: 700, color: "#fff" }}>M</div>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontSize: 12.5, fontWeight: 600 }}>Marko Š.</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>Spark Digital</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function AppTopbar({ title, crm, children }) {
  return (
    <header style={{ height: 56, flexShrink: 0, borderBottom: "1px solid var(--border)", display: "flex",
      alignItems: "center", justifyContent: "space-between", padding: "0 22px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 15, fontWeight: 600 }}>{title}</span>
        {children}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {crm && (
          <span className="chip" style={{ color: crm.color }}>
            <span className="chip-dot" style={{ color: crm.color }} /> {crm.name} connected
          </span>
        )}
      </div>
    </header>
  );
}

Object.assign(window, { AppSidebar, AppTopbar });
