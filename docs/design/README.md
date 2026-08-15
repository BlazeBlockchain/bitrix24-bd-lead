# Handoff: bd-lead — Web App + Browser Extension

## Overview
**bd-lead** is an AI-native B2B business-development assistant. A non-technical sales rep
pastes a lead's name + email; the product researches the company, finds the single most
relevant buying signal, verifies the contact, drafts a personalized outreach email, and
creates a **Contact + Deal + 3 follow-up tasks** in the rep's CRM (Bitrix24 / HubSpot) — on a
4 / 9 / 14-day cadence. A per-user **memory** layer makes every brief sound more like the
specific rep over time (tone, cadence, ICP).

This bundle covers the two client surfaces that sit on the shared backend described in
`docs/development-options.md`:

1. **Web app** (`bdlead.app`) — the demo / onboarding / billing surface. Screens: onboarding
   (connect-CRM), the paste-a-lead hero flow, and billing & plan.
2. **Browser extension** (Chrome + Firefox, **Manifest V3**) — the daily driver. Surfaces: a
   toolbar popup and an in-page injected panel that enriches the CRM/LinkedIn record already
   open in the tab.

The MCP server (the existing engine) is out of scope for this UI handoff.

## About the Design Files
**The files in this bundle are design references created in HTML/React-via-Babel** — runnable
prototypes that show the intended look, copy, and behavior. **They are not production code to
ship as-is.** The task is to **recreate these designs in the target codebase's environment**
using its established patterns and libraries.

Per `docs/development-options.md` the intended stack is **React/Vite or Next.js** for the web
app and an **MV3 extension** (service worker + content script + popup), both talking to a
Node + Python + Postgres + Redis backend on a VPS. Recreate the screens there. If you start
fresh, React + Vite (web) and a Vite-based MV3 extension (e.g. CRXJS) match the prototypes
most directly.

The prototypes use **React 18 + in-browser Babel** purely so they run from a static file —
do **not** carry the Babel transformer, the `window`-global module pattern, or the
`design-canvas` / `tweaks-panel` scaffolding into production. Convert each `*.jsx`
component into a normal module/component in your build.

## Fidelity
**High-fidelity.** Final colors, typography, spacing, copy, and interaction behavior are all
intentional. Recreate the UI pixel-accurately with your component library, then wire it to the
real backend. Exact tokens are in **Design Tokens** below; the source of truth is `styles.css`.

---

## Screens / Views

### 1. Onboarding — Connect CRM  (`onboarding.html` → `Onboarding.jsx`)
**Purpose:** First-run setup for a non-technical buyer: *sign up → connect CRM → teach style →
ready*. Full-screen, two-column, **no app sidebar**.

- **Layout:** Flex row. Left **brand rail** 320px (logo, headline, value props, a 4-step
  vertical progress rail at the bottom). Right **content column** flex-1, centered, content
  `max-width: 480px`.
- **Steps (internal state `step` 0–3):**
  1. **Connect CRM** — three selectable provider cards (Bitrix24 ✓, HubSpot ✓, Pipedrive
     "Coming soon", disabled). Selected card = iris border + `--grad-soft` bg + check pip.
  2. **Authorize** — provider-specific. Bitrix24: "Authorize" button **or** an inbound-webhook
     URL field (mono) with a "Where do I find this?" helper. HubSpot: OAuth button only.
     Clicking Authorize shows a ~1.5s connecting spinner → a green "connected" confirmation
     panel. Continue is disabled until connected.
  3. **Personalize** (seeds memory) — cadence segmented control (4/9/14 · 3/7/14 · 2/5/10),
     ICP text field, optional "paste a past email" textarea. "Skip for now" or "Save & finish".
  4. **Ready** — success mark, summary chips (CRM · cadence · memory primed), CTA
     "Paste your first lead" → navigates to the web app.
- **Progress rail states:** done (gradient fill + check), active (iris tint + ring), idle
  (muted, 0.45 opacity).

### 2. Web App — Paste → Enrich → Push  (`web-app.html` → `WebApp.jsx`, `Shell.jsx`)
**Purpose:** The hero flow. The core demo + daily web surface.

- **Layout:** Flex row. **Sidebar** 232px (`AppSidebar` in `Shell.jsx`): logo, "New lead"
  primary button, nav (New lead / Leads · badge 38 / Memory / Billing / Settings), and a
  pinned footer (Free-plan usage meter 12/25 + Upgrade, user chip). **Main** flex-1: a 56px
  **topbar** (`AppTopbar`: title + "AI live" chip; right = "{CRM} connected" chip) over a
  scrollable body, content `max-width: 920px`, centered.
- **Phases (internal state `phase`):**
  - `input` — centered headline "Paste a lead. *Get a full brief.*", a card with Full name /
    Work email / LinkedIn fields (pre-filled with the sample lead), a "Push to {CRM}" chip and
    a **Research & enrich** primary button; reassurance chips below.
  - `researching` — a 5-step checklist (Company snapshot → Buying-signal scan → Contact
    verification → Outreach email → CRM entry + follow-ups). Steps complete sequentially
    (~520ms each, **JS-driven** via setTimeout — not CSS), each flipping idle → working
    (spinner) → done (gradient check). After the last step → `result`.
  - `result` — lead identity header (avatar initials, name, **confidence pill** HIGH/MED/LOW,
    title · company · location, "brief in 48s" + "N sources" chips). Two columns: left =
    **tabbed Lead Brief**; right rail = **memory callout** + **enriched-contact** fields +
    **push panel**.
  - `pushed` — push panel swaps to a green "Pushed to {CRM} — Contact + Deal + 3 tasks /
    Memory updated" confirmation + "Next lead".
- **Lead Brief tabs** (`LeadBrief` component):
  - *Full brief* — input echo (mono), "LEAD BRIEF — {COMPANY}" header, sections Company
    (3-sentence snapshot) / Buying signal (source + date bold) / Contact (confidence + note).
  - *Email* — To / Subject header, body (`white-space: pre-wrap`), meta tags (word count,
    psychological angle, "No banned phrases").
  - *CRM entry* — 2-col grid of fields (Deal name, Contact role, Signal, Pain point, Pipeline,
    Confidence) + a pre-call Notes block.
  - *Follow-ups* — 3 task rows, each: type icon (Email/Call/LinkedIn), title, "Day +N" chip,
    description, and an italic signal-matched script (left iris border).
- **Memory callout** (`--grad-soft` panel, iris border): "Your memory shaped this" + 3 lines
  (tone / cadence / ICP) — the core differentiator.

### 3. Billing & Plan  (`billing.html` → `Billing.jsx`, `Shell.jsx`)
**Purpose:** Plan management. Same shell as the web app, `Billing` nav active.

- **Usage banner** — "12 / 25 enrichments this month", progress bar, reset date, an
  "Upgrade to Pro" CTA.
- **Plans** — 3 cards (`PlanCard`): **Free €0** (current — disabled "Current plan" button),
  **Pro €9/user/mo** (popular: iris border + "Most popular" chip; default-selected),
  **Team €7/seat/mo**. Cards are click-to-select (selected = iris ring + `--grad-soft`).
  Feature lists with green checks. Footnote names the model strategy (Gemini 2.5 Flash + Haiku
  4.5; Pro adds Sonnet-tier on demand).
- **Payment method** — Stripe **test-mode** card stub (•••• 4242), "Edit", a lock note that
  card data lives at Stripe.
- **Billing history** — date / desc / amount rows + per-row invoice icon, "Export".

### 4. Extension — Toolbar Popup  (`extension-popup.html` → `Extension.jsx` `ExtPopup`)
**Purpose:** MV3 popup; the quick capture surface. **Fixed 384 × 600** (a Chrome popup size).

- Header: logo + detected-CRM chip. States: `input` (detected-tab note + Name/Email fields +
  "Research & enrich" + reassurance chips) → `gen` (~1.7s spinner + animated load bar) →
  `result` (the condensed **MiniBrief**) → `pushed`.
- **MiniBrief**: identity row + confidence; segmented mini-tabs **Signal / Email / Plan**; a
  memory line; a "Push to {CRM}" button → green confirmation. Footer link "Open full brief in
  web app".

### 5. Extension — In-Page Injected Panel  (`extension-inpage.html` → `Extension.jsx` `ExtInPage`)
**Purpose:** Content-script UI over the CRM/LinkedIn tab the rep is already on.

- A faux CRM record (top bar + blurred skeleton body) with a **348px panel** docked right
  (`-20px 0 50px` shadow). When closed, a floating "Enrich with bd-lead" pill sits bottom-right.
- The panel reads the open record and shows the same **MiniBrief** (no paste needed) +
  "enriched" live chip + close (×).

---

## Interactions & Behavior
- **Navigation:** sidebar items + Upgrade route between surfaces. In the standalone files this
  is `location.href`; in production use your router (e.g. `/onboarding`, `/`, `/billing`).
- **Async simulation:** research progress (web app) is JS timers; popup uses one ~1.7s timer.
  In production these map to real backend calls — keep the **step-by-step reveal** (it doubles
  as the "5 research steps" value prop) by streaming server progress.
- **Animations:** entrance motion is a **transform-only** `risein` (translateY 10→0, 0.5s,
  `cubic-bezier(.2,.7,.3,1)`). Visibility is **never** gated on opacity (a deliberate choice so
  content can't get stuck invisible). Spinners use `spin` 0.9s linear. Connect/push use color
  state swaps. Keep transitions ~150–250ms.
- **Hover/active:** buttons lift 1px + stronger glow (primary) or brighten border/bg (ghost);
  sidebar/nav items get a faint white wash; plan & CRM cards highlight on select.
- **Form validation (to add in prod):** require a valid email before enrich; webhook URL must
  match the Bitrix24 REST pattern; disable submit while a request is in flight.
- **Loading/error states (to add in prod):** enrichment can fail or hit a per-user token
  budget — design a graceful "couldn't research, here's what we have" partial state and a
  rate-limit message (see Risks in the source doc).
- **Responsive:** prototypes are desktop-fixed. The popup is fixed 384×600. The web app should
  collapse the sidebar to a drawer < ~900px; plan cards should stack < ~720px.

## State Management
- **Onboarding:** `step` (0–3), `crmId`, `connecting`, `connected`, `cadence`, `icp`.
- **Web app:** `phase` (input | researching | result | pushed), `done` (step index), `form`
  ({name,email,linkedin}); the active **Lead Brief tab** is local to `LeadBrief`.
- **Billing:** `selected` plan id; `current` plan (from the account).
- **Extension popup:** `phase` (input | gen | result | pushed), `form`; MiniBrief tab is local.
- **In-page panel:** `open`, `phase` (result | pushed).
- **Real data the backend must provide:** authed user + plan/usage, connected-CRM list +
  tokens (server-side, encrypted), the enrichment result object (snapshot, signal, contact +
  confidence, outreach email, CRM field mapping, the 3-task plan), and the per-user memory
  profile (tone, cadence, ICP, prior outcomes). Shapes are illustrated in `data.jsx`.

## Design Tokens
Source of truth: **`styles.css`** (`:root`). Theme is **dark**.

**Surfaces:** bg `#05070d` · elevated `#0a0e18` · panel `rgba(255,255,255,.025)` ·
panel-2 `rgba(255,255,255,.045)`.
**Lines:** border `rgba(255,255,255,.07)` · hover `rgba(255,255,255,.14)` ·
strong `rgba(255,255,255,.2)`.
**Text:** primary `#eaecf2` · soft `#b0b6c4` · muted `#6b7385` · dim `#4a5160`.
**Brand (overridable):** accent `#4a7cff` · accent2 `#7c5cff` · accent3 `#22d3ee`.
**Gradients:** `--grad` `linear-gradient(135deg,#4a7cff,#7c5cff 55%,#22d3ee)` ·
`--grad-text` `linear-gradient(100deg,#8ab0ff,#b4a3ff 50%,#7cdff0)` · `--grad-soft` (same hues
at ~10–18% alpha).
**Semantic:** green `#10b981` (success/connected) · gold `#f5b841` · red `#ef4444`.
**CRM brand:** Bitrix24 `#2BB2E3` (uses accent3) · HubSpot `#FF7A59` (uses gold).
**Radius:** sm 8 · md 10 · lg 14 · xl 18 (px).
**Type:** UI = **Inter** (400/500/600/700/800); mono = **JetBrains Mono** (signals, codes,
numbers). Letter-spacing −0.005em base; headings −0.02 to −0.03em. Min UI text ~11px (chips),
body 12.5–14px, H1 24–30px.
**Density** (`data-density`): compact (`--pad`15/`--gap`9) · regular (22/14) · comfy (28/19).
**Shadows/glow:** primary `0 4px 16px rgba(74,124,255,.28), inset 0 1px 0 rgba(255,255,255,.18)`
(hover `0 8px 28px rgba(124,92,255,.4)…`); popover `0 28px 70px rgba(0,0,0,.6)`.
**Atmosphere:** `.fieldbg` = layered radial iris/cyan glows + a faint SVG noise overlay
(`mix-blend-mode: overlay`), behind each surface.

The bd-lead logo mark is the `bolt` glyph in a gradient rounded square (see `.bd-mark`).

## Assets
No external images. All icons are inline 24-grid stroke SVG paths in `data.jsx` (`I` map,
rendered by `<Icon d="…">`). Fonts load from Google Fonts (Inter, JetBrains Mono). The sample
lead (Lena Vuković / Maritimo Logistics) and all copy live in `data.jsx`.

## Files
**Standalone surface pages (open any in a browser):**
- `onboarding.html`, `web-app.html`, `billing.html`, `extension-popup.html`, `extension-inpage.html`

**Overview canvas (all surfaces side-by-side + live Tweaks for accent/CRM/cadence/density):**
- `bd-lead.html` (loads `design-canvas.jsx` + `tweaks-panel.jsx` — scaffolding only, not for prod)

**Components & shared code:**
- `styles.css` — all design tokens + primitives (buttons, chips, fields, panels) — **port this first**
- `data.jsx` — sample data shapes + icon set
- `Shell.jsx` — `AppSidebar` + `AppTopbar`
- `WebApp.jsx` — web-app phases + `LeadBrief`
- `Onboarding.jsx` — connect-CRM flow
- `Billing.jsx` — plans + payment + history
- `Extension.jsx` — `ExtPopup`, `ExtInPage`, shared `MiniBrief`
- `standalone.jsx` — palette bootstrap for the standalone pages

**Product context (read this):** `docs/development-options.md` in the source repo — architecture,
sequencing, pricing, MV3 constraints, and risks.
