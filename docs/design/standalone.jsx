/* ============================================================
   standalone.jsx — shared bootstrap for the single-surface HTML files.
   Applies the default brand palette + exposes T_DEFAULT for mounting.
   (The canvas file bd-lead.html uses the live Tweaks panel instead.)
   ============================================================ */

const T_DEFAULT = {
  palette: ["#4a7cff", "#7c5cff", "#22d3ee"],
  crm: "bitrix24",
  cadence: "4/9/14",
  density: "regular",
};

function applyPalette(p) {
  const r = document.documentElement.style;
  const [a, b, c] = p;
  r.setProperty("--accent", a);
  r.setProperty("--accent2", b);
  r.setProperty("--accent3", c);
  r.setProperty("--grad", `linear-gradient(135deg, ${a} 0%, ${b} 55%, ${c} 100%)`);
  r.setProperty("--grad-soft", `linear-gradient(135deg, ${a}2e, ${b}29 55%, ${c}24)`);
  r.setProperty("--grad-text", `linear-gradient(100deg, ${a} 0%, ${b} 50%, ${c} 100%)`);
  r.setProperty("--accent-soft", `${a}1a`);
  r.setProperty("--accent-line", `${b}47`);
  r.setProperty("--glow-accent", `0 4px 16px ${a}47, inset 0 1px 0 rgba(255,255,255,0.18)`);
  r.setProperty("--glow-accent-hover", `0 8px 28px ${b}66, inset 0 1px 0 rgba(255,255,255,0.22)`);
}

applyPalette(T_DEFAULT.palette);
window.T_DEFAULT = T_DEFAULT;
window.applyPalette = applyPalette;
