# UI_UX: AI-Native BD Lead Assistant — Screens, Journeys, Design

**Project:** bitrix24-bd-lead  
**Status:** Phase 0 product/UX direction — **superseded on visual design** (updated 2026-08-15)  
**Date:** 2026-07-13  
**Scope:** screens, journeys, information architecture, and the audience constraints from
`docs/development-options.md`.

> ## ⚠️ This is not the visual specification
>
> **For colors, type, spacing, and component styling, use `docs/design/` instead** —
> `docs/design/README.md` is the written spec and `docs/design/styles.css` is the token source of
> truth. The machine-readable, committed transcription is `design/tokens.css`.
>
> The palette this document originally proposed (orange `#f97316` on GitHub-dark `#0d1117`, adapted
> from the Vanguard-game design system) is **retired**. It was never a deliberate brand — it was a
> placeholder that shipped. `make check-tokens` now fails the build if any of those values reappear.
>
> What remains authoritative here: the **design principles** below, the **screen inventory**, the
> **user journey**, and the **accessibility requirements**. Those still hold.

---

## Design Principles (Non-Negotiable for This Audience)

- **Zero config after first connect.** Every subsequent use is "paste → magic → push".
- **AI is visible and trustworthy.** Show the snapshot, the opener, the tasks, and a short "why this" rationale. Never hide the AI output behind a black box.
- **Memory is a feature, not a setting.** Surface "Personalized using your last 7 leads" so users feel the compounding value.
- **Mobile-friendly first.** Many BD reps review leads on phones between meetings.
- **Forgiving and reversible.** Clear errors, easy retry, no data loss on refresh.
- **Dark theme default.** Sales tools are often used in low light or late hours.

---

## Screen Inventory & Navigation

### Public / Marketing (no login required)
- **Landing** (`/`)
  - Hero: "Paste a name. Get an enriched lead + 3 perfect follow-ups. In your CRM in 30 seconds."
  - Primary CTA: "Sign up free with Google" or "Try it now" (demo mode that doesn't require account but limited).
  - Trust bar: "Works with Bitrix24 + HubSpot" + logos.
  - Secondary: "See how it works" (30s video or animated GIF of the flow).
- **Pricing** (`/pricing`)
  - Simple tiers (Free beta / Pro €X/mo) — stub for MVP.
  - "Start free" button.

### Auth Flow
- Google OAuth redirect (standard consent screen).
- Post-login: immediate redirect to Onboarding or Dashboard.
- Fallback: magic link or "Continue with email" (P2).

### Authenticated App (protected)
Top-level nav (persistent header):
- Logo + "BD Lead"
- Links: Dashboard | New Lead | History | Connections | Account
- Right side: User avatar (Google photo) + usage pill ("47 / 100 leads this month")

**Dashboard** (`/`)
- Quick stats: Leads this month, Avg. time saved (stub), Memory strength indicator.
- Recent leads (last 5 cards or table row).
- Big "Create new lead" primary button.
- CRM connection health pill (green "Bitrix24 connected" or warning).

**Connections** (`/connections`)
- Cards or table: Bitrix24 (webhook URL masked, last validated, Reconnect / Remove).
- HubSpot (OAuth status, Reconnect).
- "Add CRM" button → modal with two options + inline instructions ("Go to Bitrix24 → Applications → Webhooks → Add inbound... then paste here").

**Lead Composer** (`/new` or modal from dashboard)
- Split or stacked layout:
  - Left / top: Form
    - Company name (required)
    - Contact name + Role
    - Signal (free text or quick chips for signal_type)
    - Pain point / Why now
    - Notes (bullet friendly)
    - Optional: LinkedIn, Email
  - Right / bottom: Preview pane (appears after "Generate with AI")
    - Company Snapshot (paragraph)
    - Suggested Opener (copy button)
    - Follow-up Plan (3 cards or timeline: title + description + due date + "Why this timing")
    - "Regenerate" (with note "using your memory")
- Actions: "Generate with AI" (primary), "Push to CRM" (enabled after preview), "Save draft".

**Lead History** (`/history`)
- Table or card list: Company | Contact | Date | CRM | Outcome (won / open / lost — editable later) | View
- Click row → detail modal or page showing the exact snapshot + opener + tasks that were pushed + any user notes.
- Filters: by CRM, by date, by signal type.
- "Create similar lead" action that pre-fills composer with memory boost.

**Account / Settings** (`/account`)
- Profile (from Google).
- Memory profile summary (visible tone samples, industries, cadence prefs — editable).
- Usage & limits.
- Billing (stub).
- Danger: "Export my data", "Delete account & all memory".

### Browser Extension Surfaces (MV3)

> Updated 2026-08-15 to match what shipped. The compact-composer-in-a-popup model below was replaced
> by a docked side panel in `specs/007-extension-side-panel/` — a popup is capped near 800x600 and
> Chrome dismisses it on any outside click, which broke the core "read the prospect's page alongside
> the brief" workflow.

- **Side panel** (`sidepanel.html`) — the workspace, and the daily driver. Docked, user-resizable,
  stays open while the user browses. Holds the lead form and the full AI preview. Requires Chrome
  116+. Includes a footer "Close panel" action; the top-right is left to Chrome's own close control.
- **Popup** (`popup.html`) — a thin 320px launcher only. Opens the panel, shows API and session
  status, links to settings and the dashboard. Deliberately does *not* duplicate the composer.
- **Options page** (`options.html`) — Google sign-in, OAuth client ID, the redirect URI, and default
  CRM provider.
- **Page capture** — "Grab from this page" in the panel, via on-demand `chrome.scripting` against the
  active tab. Not a persistent content script, and no floating in-page button.

**Navigation model overall:**
- Web: SPA (React Router) or Next.js pages.
- Extension popup is self-contained but shares auth tokens / backend.
- Deep links from success states back to History or CRM.

---

## Primary User Journey (Happy Path — Non-Technical Rep)

1. **Discovery** — Lands on marketing page (from cold email, LinkedIn, or colleague).
2. **30-second signup** — Clicks "Sign up with Google". Approves. Lands on Dashboard.
3. **One-time connect** (2–4 min):
   - Sees "Connect your CRM" card.
   - Chooses Bitrix24 → sees exact 4-step copy: "In Bitrix24 go to Applications → Webhooks → Add inbound webhook → enable CRM + Tasks → copy URL → paste here".
   - Pastes URL → "Test connection" succeeds (green).
   - (HubSpot path: "Connect with HubSpot" → OAuth consent → success).
4. **First lead** (under 2 min active time):
   - Clicks "New Lead".
   - Pastes or types: Company, Name + Role, Signal ("Series B announced"), Pain.
   - Hits "Generate with AI" → sees loading skeleton (important) → enriched preview appears.
   - Reads rationale, likes it, hits "Push to CRM".
   - Toast: "✅ Created Contact 1234, Deal 567, Tasks 89/90/91. View in Bitrix24 →".
5. **Second lead (memory effect)**:
   - Same flow.
   - Preview now says "Personalized using your style from 3 prior leads".
   - Opener language is subtly closer to what the user accepted before.
6. **Later** — Uses History to review what worked, or triggers from extension while on a prospect tab.

**Time-to-value target:** < 10 minutes from landing page to first real record in CRM.

---

## Component Library & Design Tokens (Initial)

**Base tokens — see `design/tokens.css`, do not copy values out of this document.**

The token set is generated into `web/src/index.css` and `extension/tokens.css` by
`make sync-tokens`; `make check-tokens` fails on drift. Summary of the current language:

```css
/* surfaces — near-black navy, translucent glass panels */
--bg: #05070d;
--bg-elev: #0a0e18;
--panel: rgba(255,255,255,0.025);
--border: rgba(255,255,255,0.07);   /* hairline, not a solid line */

/* brand — iris → violet → cyan gradient, NOT a flat accent */
--accent: #4a7cff;
--accent2: #7c5cff;
--accent3: #22d3ee;
--grad: linear-gradient(135deg, #4a7cff 0%, #7c5cff 55%, #22d3ee 100%);
--grad-btn: linear-gradient(135deg, #4a7cff 0%, #7c5cff 100%);  /* stops before cyan */

/* text ramp */
--text: #eaecf2;  --text-soft: #b0b6c4;  --muted: #6b7385;  --muted-dim: #4a5160;

/* semantic */
--green: #10b981;  --gold: #f5b841;  --red: #ef4444;

/* radius ramp (not a single --radius) */
--r-sm: 8px;  --r-md: 10px;  --r-lg: 14px;  --r-xl: 18px;

/* type — self-hosted, no font CDN */
--font-ui: "Inter", -apple-system, system-ui, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, monospace;
```

Two deliberate deviations from `docs/design/styles.css`, both documented in
`specs/008-design-system-pass/`:

- **12px minimum font size.** The handoff specifies ~10.5px chips and 10px labels. This project has
  a hard 12px floor — Chrome's UA stylesheet already shrinks extension-page body text by 0.75, and
  sub-12px type was a shipped defect once. The ramp is rescaled upward from 12px.
- **`--grad-btn` for button fills.** The full `--grad` ends in cyan, where white label text falls to
  a 1.81 contrast ratio and is effectively unreadable. Decorative uses keep the full gradient.

**BD-specific components (to build or adapt):**
- `LeadCard` / `HistoryRow`
- `SignalBadge` (color per type: funding = green, new_leadership = blue, etc.)
- `TaskTimeline` (3 vertical steps with due dates)
- `EnrichmentPreview` (split pane or accordion)
- `CrmStatus` pill
- `MemoryBadge` ("Using your memory · 7 leads")
- `CopyButton`, `RegenerateButton`
- Form primitives with good labels + inline validation

**Icons:** Use a minimal set (lucide-react or heroicons). No custom icon font in MVP.

**Typography:** Clear hierarchy. Form labels above inputs. Preview uses slightly larger readable text for the opener.

---

## Accessibility & Responsive Requirements

**Accessibility (WCAG 2.2 AA target):**
- All form controls have visible labels.
- Keyboard navigable end-to-end (Tab, Enter, Escape for modals).
- Focus visible (strong ring).
- Color is never the only indicator (SignalBadge has text + color).
- ARIA live regions for AI generation status and success toasts.
- Error messages associated with fields.
- Sufficient contrast on dark theme (test with tools).
- Skip links or logical heading order.

**Responsive (mobile-first):**
- Composer: On <768px stacks vertically (form on top, preview below or collapsible).
- Dashboard cards become full-width.
- Header collapses to hamburger or bottom nav on very small screens (extension popup is constrained anyway).
- Touch targets ≥ 44px.
- Tables become cards or horizontally scrollable on phones.
- Extension popup: 360–400px wide max, clean scrolling.

**Performance perception:**
- AI preview always shows skeleton or progress ("Contacting Gemini…") within 300ms.
- No layout shift when preview appears.
- Optimistic push UI where safe.

**Edge states to design:**
- No CRMs connected.
- First lead ever (empty memory).
- AI slow / fallback used.
- CRM rate limit or auth expired.
- Offline (rare for this app).

---

## Extension-Specific UX Notes

- Popup must feel fast and contained — heavy work happens server-side.
- "Pre-fill from page" is best-effort and clearly labeled "May be incomplete — edit before generating".
- Settings link opens the web dashboard in a new tab for complex actions.
- Permission model: only activeTab + storage + the hosts we declare. No broad host permission if avoidable.

---

## Open UX Questions (to validate with users or in research)

- Exact wording of onboarding steps for Bitrix24 webhook (screenshots vs text).
- How much editing of the AI preview to allow before push (none vs light vs full).
- Memory visibility level (show raw samples? or just "using your style").
- Whether to offer a "demo mode" that creates fake records without a real CRM connection.

---

**Related Artifacts**
- `docs/design/` — **the visual specification**. `README.md` is the written spec, `styles.css` the
  token source of truth, and the `*.jsx` files are runnable prototypes (reference only — never ship
  their in-browser Babel or `design-canvas`/`tweaks-panel` scaffolding).
- `design/tokens.css` — the committed, machine-readable token upstream. `make sync-tokens`.
- `FEATURES.md` for stories and acceptance criteria that these screens must satisfy.
- `ARCHITECTURE.md` for the data that must be displayed (enriched json shape, memory profile).
- `specs/008-design-system-pass/` — how the design was applied, and the two documented deviations.

---

*This document will be updated as we build and test with real BD reps.*
