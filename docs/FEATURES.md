# FEATURES: AI-Native BD Lead Assistant — MVP & Roadmap

**Project:** bitrix24-bd-lead  
**Status:** Draft (Phase 0)  
**Date:** 2026-07-13  
**Sources:** `docs/development-options.md`, `docs/project_kanban.md`, `docs/project_agents_tasks.md`, `docs/market-research-handoff.md`

---

## MVP Definition

MVP is the smallest independently valuable and testable slice that delivers the core promise to a non-technical buyer:

> "Sign up with Google → connect my CRM (Bitrix24 or HubSpot) → paste a lead → see AI-enriched preview with personalized follow-ups → push to CRM → it appears correctly with 3 tasks. The system remembers my style on the next lead."

Everything else (advanced memory, billing, more CRMs, team features) is explicitly roadmap.

### MVP Must-Haves (P1 — shippable as standalone slice)

1. **User account & Google Auth**
   - Sign up / login via Google OAuth.
   - Protected routes / JWT session for web + extension.

2. **CRM Connection (2 providers)**
   - Bitrix24: paste inbound webhook URL + validation (basic call succeeds).
   - HubSpot: full OAuth2 private app flow + token storage.
   - Per-user encrypted storage of credentials.
   - Simple UI to view / disconnect.

3. **Lead Composer + AI Enrichment (the magic moment)**
   - Form fields matching current `BdLeadSchema` + a couple of nice-to-haves (LinkedIn URL, email).
   - "Generate with AI" calls backend → returns:
     - One-paragraph company snapshot (public signals).
     - Personalized first-email opener in user's tone (from memory or defaults).
     - Exactly 3 follow-up tasks with titles, descriptions, due dates (+4/+9/+14), and short rationale.
   - Preview UI (read-only or lightly editable) before push.
   - Cost/usage shown (e.g. "This lead used ~2,300 tokens").

4. **Push to CRM**
   - Creates Contact + Deal (linked) + 3 Tasks with correct associations and deadlines.
   - Success feedback with CRM record IDs (and deep links where possible).
   - Graceful handling of duplicates / errors with clear messages.

5. **Basic Memory / History**
   - List of user's past leads (company, date, outcome if recorded).
   - On second+ lead, the enrichment prompt includes prior context (tone match visible in preview).
   - Simple "replay" or "use similar" action.

6. **MCP parity (engine)**
   - Existing `bitrix24_create_bd_lead` tool (and future multi-provider) continues to work against the new backend or via shared library.

7. **Extension (thin)**
   - MV3 extension installs.
   - Popup or page action that opens the composer (pre-filled if page context detectable).
   - Calls same authenticated backend APIs.

8. **Operational basics**
   - Billing page stub ("Free during beta — X leads this month").
   - Error boundaries, loading states for AI, rate-limit messaging.
   - Per-user daily LLM budget guardrails (hard stop + nice message).

### Explicit Out of MVP Scope (P2+ or never for v1)

- Real payments / Stripe checkout.
- Multi-user teams / workspaces.
- Reply detection or inbox integration.
- A/B variants or multi-channel sequences.
- Full CRM marketplace listings.
- Advanced analytics dashboard.
- Zoho / Pipedrive / Attio adapters (unless warm lead appears).
- Self-hosted option.

---

## Acceptance Criteria (Examples — testable independently)

**Core happy path (Bitrix24):**
- Given a fresh user connected to a valid Bitrix24 webhook, when they submit a complete lead brief and click "Push":
  - Exactly 1 Contact is created with NAME/LAST_NAME/POST/COMPANY_TITLE.
  - Exactly 1 Deal is created linked to the Contact, with TITLE and COMMENTS containing signal + pain + notes.
  - Exactly 3 Tasks are created linked via UF_CRM_TASK, with correct DEADLINEs and RESPONSIBLE_ID.
- The UI shows the three task IDs and dates.

**HubSpot path:**
- Same counts + linking via associations.
- `hs_timestamp` values correctly represent +4/+9/+14 days in UTC ms epoch.
- Custom property handling documented or auto-created.

**Memory / personalization:**
- After user accepts 2–3 leads and the system has stored tone samples or explicit preferences, the third enrichment produces measurably different opener language or task phrasing that references prior context.
- History page shows the prior leads for that user only.

**Error & edge cases:**
- Invalid or expired CRM credentials → clear "Reconnect your CRM" message + link. No partial data left in CRM.
- LLM timeout or quota → fallback model attempted; if both fail, user sees friendly message + "Try again later" (no broken records).
- Duplicate-ish lead → still creates (no dedupe in MVP) but surfaces warning.

**Extension:**
- Clicking the extension icon on a Bitrix24 deal page opens popup with some fields pre-filled from visible DOM or page title (best-effort).
- Push succeeds and shows same success state as web.

**Non-technical onboarding:**
- A new user with zero technical background can go from landing page → Google sign-in → connected CRM → successful push in under 10 minutes following on-screen guidance (measured in user testing or video).

---

## User Stories (Prioritized)

### P1 (MVP — must ship to claim "it works")

- **Story 1**: As a non-technical Croatian BD rep using Bitrix24 free, I want to sign up with my Google account, paste my webhook once, then paste a company + decision maker name + signal, see a smart preview, and have Contact + Deal + 3 tasks created so I can stop doing this by hand.
- **Story 2**: As a returning user, when I create a second lead the AI uses what it learned about my writing style and follow-up cadence so the output feels like "me" and I don't have to rewrite everything.
- **Story 3**: As a South African rep on HubSpot, I want the exact same flow to work without learning a different tool.
- **Story 4**: As any user, I want to see my last 10 leads and what I pushed so I have a record and can re-use context.

### P2 (post-MVP polish / first expansion)

- As a user on LinkedIn Sales Navigator, I want a one-click "BD Lead" button from the extension that pre-fills the form from the profile I'm looking at.
- As a user who hit a transient error, I want to retry the push without re-entering everything.
- As a user, I want a "Regenerate with different tone" button that uses more/less formal memory samples.
- Basic usage dashboard ("X leads this month, Y tokens, Z estimated cost").

### P3 / Roadmap

- Team workspaces and shared memory.
- Full Stripe billing with usage tiers.
- More CRM adapters driven by paying customers.
- Marketplace distribution where it adds value.
- Reply detection and auto-bump suggestions.

---

## MVP vs. Roadmap Priority Table

| Area                    | MVP (this build)                          | Post-MVP / Roadmap                          | Notes |
|-------------------------|-------------------------------------------|---------------------------------------------|-------|
| Auth                    | Google OAuth + JWT                        | + Email/password, LinkedIn, magic links     | Google is P1 for friction |
| CRM Adapters            | Bitrix24 + HubSpot                        | Pipedrive, Zoho, Attio (if customer asks)   | CrmClient makes adding cheap |
| AI Enrichment           | Snapshot + opener + 3 tasks + rationale   | Multi-variant, A/B, research deep-dive      | AI is non-negotiable in v1 |
| Memory                  | Basic profile + recent leads in prompts   | Vector recall, outcome tracking, win patterns | Core switching-cost moat |
| Clients                 | Web app (full) + thin MV3 extension       | Slack/Teams bot, in-CRM marketplace cards   | Web required for onboarding |
| Billing & Tiers         | Stub ("Free beta — X leads/mo")           | Real Stripe, Free / Pro / Team              | Pricing shape still open |
| Observability           | Per-lead cost logging + basic guards      | Alerts, admin dashboard, export             | Mandatory for cost control |
| Polish / DX             | Loading skeletons, clear errors, mobile   | Onboarding wizard videos, templates library | |

---

## Definition of Done for MVP Slice

- All P1 user stories independently testable and passing acceptance criteria.
- Both Bitrix24 and HubSpot happy paths create correct records in real sandboxes.
- Memory effect demonstrable on repeat use for the same user.
- Extension installs from unpacked + store (if submitted) and performs push.
- 4 product docs (CONCEPT, ARCHITECTURE, FEATURES, UI_UX) exist and are consistent.
- Speckit spec/plan/tasks cover the slice; constitution updated.
- Security token handling + LLM budget notes written.
- `docker compose up` brings a working local environment.
- README updated with new user flow.

See `project_agents_tasks.md` for the skill-owned card breakdown that will implement the above.

---

**Cross References**
- Open questions from `docs/development-options.md` §7 (pricing, memory scope, model fallback, v1 CRMs).
- Current implementation in `src/tool.ts` (task templates and orchestration logic to be generalized and called from new backend).
