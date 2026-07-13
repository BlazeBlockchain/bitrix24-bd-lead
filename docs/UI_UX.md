# UI_UX: AI-Native BD Lead Assistant — Screens, Journeys, Design

**Project:** bitrix24-bd-lead  
**Status:** Draft (Phase 0)  
**Date:** 2026-07-13  
**Inspiration:** Vanguard-game design system (dark theme, accent colors, component patterns) + non-technical buyer constraints from `docs/development-options.md`

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
- **Popup** (default action)
  - Compact version of composer (or "Open full composer in web" link).
  - "Use visible page data" button (best-effort scrape of name/company on known CRM/LinkedIn hosts).
  - Status line: "Connected to your Bitrix24".
- **Options page** (chrome://extensions or link)
  - Same as web Connections + Account summary.
  - "Open web dashboard" button.
- Content script (optional v1+): Floating "BD Lead" button on recognized CRM record pages (non-intrusive).

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

**Base tokens** (adapt from vanguard-game `src/index.css` + components):
```css
--bg: #0d1117;
--surface: #161b22;
--surface-2: #1c2330;
--border: #30363d;
--text: #e6edf3;
--muted: #8b949e;
--accent: #f97316;      /* Orange — primary action */
--accent-2: #38bdf8;    /* Blue — secondary / HubSpot */
--accent-3: #4ade80;    /* Green — success / connected */
--danger: #f87171;
--radius: 8px;
--font-sans: system-ui, sans-serif;
```

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
- `FEATURES.md` for stories and acceptance criteria that these screens must satisfy.
- `ARCHITECTURE.md` for the data that must be displayed (enriched json shape, memory profile).
- Vanguard-game components for reuse patterns (`ChallengeCard`, `Layout`, forms, protected routes).

---

*This document will be updated as we build and test with real BD reps.*
