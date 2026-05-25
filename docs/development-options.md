# Development Options — Where Should `bitrix24-bd-lead` Live?

**Project:** `bitrix24-bd-lead` — AI-native BD assistant that creates an enriched Contact + Deal + 3 follow-up Tasks for B2B outreach, with per-user memory of past leads
**Date:** 2026-05-25
**Author:** Bojan Bartoniček
**Companion docs:** [`market_research.md`](./market_research.md), `project_kanban.md`

---

## 0. Product Premise (load-bearing)

Three constraints shape every architectural decision below:

1. **Target buyer is non-technical.** Croatian/EU SMB BD reps, sales managers, founders doing their own outreach. They cannot reason about webhooks, OAuth scopes, or CRM data models. Onboarding must be: *sign up → connect CRM → paste a name → magic happens*.
2. **AI is the selling point, in v1.** Not a v2 feature. The pitch is "paste a name and email, get an enriched lead with a personalized 3-step follow-up plan that remembers everything you've done before." Without AI we are a glorified form filler and indistinguishable from CRM-native macros.
3. **We need per-user memory.** The product gets smarter per user the more they use it (their writing style, their typical follow-up cadence, which industries they target, which deals they won). This requires a backend with persistent state — not a stateless extension.

These force a **backend-on-VPS** architecture, modelled on [`../vanguard-game`](../../vanguard-game/) (Node + Python + Postgres + Redis + Docker Compose, deployed to our own VPS). LLM inference uses cheap models — **Gemini 2.5 Flash primary, Claude Haiku 4.5 fallback** — to keep per-lead cost in the ~$0.001–0.01 range.

---

## 1. Executive Summary

The MCP server is the engine. Around it we need to wrap a **product**, not a developer tool. Given the premises in §0 (non-technical buyer, AI-first selling point, per-user memory), every viable path needs the same backend; only the *client* differs.

**Required infra (all paths):**
- **Backend on VPS** — Node + Python + Postgres + Redis + Docker Compose (mirror `../vanguard-game`). Hosts: auth, per-user memory, CRM token vault, LLM proxy, billing.
- **LLM proxy** — calls Gemini 2.5 Flash (primary) and Claude Haiku 4.5 (fallback). We hold the API keys; users never see them.
- **Per-user memory store** — Postgres for structured lead history + a small vector index (pgvector) for semantic recall of prior outreach.

**Client distribution paths (the actual choice):**

| Path | Time-to-first-user | Fit for non-technical buyer | AI integration ease | Recommendation |
|---|---|---|---|---|
| **A. MCP server** | shipped | poor (devs only) | trivial | Keep as engine + dev surface |
| **B. CRM-marketplace app** | 6–10 wks per CRM | excellent (inside the CRM) | medium (UI extension constraints) | Phase 3 / opportunistic |
| **C. Browser extension** (MV3, Chrome + Firefox) | 4–6 wks after backend | great (sits in CRM tab + LinkedIn) | medium (MV3 service-worker quirks) | **★ Primary client v1** |
| **D. Standalone web app** | 4–6 wks after backend | great (own demo URL, easy onboarding) | trivial (same origin as backend) | **★ Ship alongside extension** |
| **E. Slack / Teams bot** | 3–4 wks | niche | trivial | Phase 3 add-on |

**Decision:** Build the backend first (single VPS, vanguard-game pattern). Then ship **both the web app *and* the extension on top of it** — the web app is the demo/onboarding surface (login, connect CRM, "try it now" form, billing); the extension is the daily-driver surface that lives where the BD rep already works. They share the backend, share the AI, share the per-user memory.

**Why both:** The web app is required anyway for sign-up, OAuth callback, billing, and account management. Once that exists, the extension is a thin client over the same backend — not a duplicated codebase. Skipping the web app would force us to do all of those things inside Chrome's popup, which is hostile UX for a non-technical buyer.

**Sequencing:**
1. **Backend + AI layer + web app v1** (~5–7 weeks) — sign-up, Bitrix24 + HubSpot CRM connection, paste-a-lead form, AI enrichment + 3-task plan, billing stub.
2. **Browser extension v1** (~2–3 weeks after backend stabilizes) — same backend, content-script trigger on CRM/LinkedIn tabs.
3. **Marketplace apps + Slack bot** — opportunistic, driven by where paying users actually came from.

The MCP server (A) stays as the reference implementation and the surface for engineers/AI agents — same `CrmClient` interface, different transport.

---

## 2. The Distribution Problem

Today the flow is:

```
BD rep → Claude Desktop → MCP server (us) → Bitrix24 REST
```

That requires the user to (a) own a Claude Code/Desktop license, (b) install our MCP server, (c) hold a Bitrix24 webhook token. The audience that clears all three filters is roughly **the same engineers who could build it themselves** — a poor PMF.

The product value (auto-skeleton: Contact + Deal + 3 follow-ups on a 4/9/14-day cadence) is generic. The packaging is the bottleneck.

---

## 3. Path Detail

### A. Keep as MCP server (status quo)

- **What it is:** Today's `src/index.ts` + `src/client.ts`. Stdio transport, Claude/Cursor/Continue as clients.
- **Pros:** Already works. Zero distribution cost. Future-proof — MCP is becoming the lingua franca for LLM tool use, and Anthropic, OpenAI, and others now ship MCP clients in their official products.
- **Cons:** Audience is engineers with an MCP client. Non-technical BD reps will not install Node, edit JSON, and paste a webhook URL.
- **Verdict:** Keep this as the **reference implementation and the engine**. All other paths should call the same `CrmClient` abstraction.

### B. CRM-native app (marketplace installation) — deferred / opportunistic

This means turning the project into an app that installs *inside* the CRM itself — surfaced as a button or sidebar in the CRM's lead/deal UI.

#### B1. HubSpot Marketplace app

- **Mechanics:** Build a public app on **HubSpot Developer Platform v2026.03** (older versions are now rejected from new listings). Listing requires OAuth v3, a security questionnaire, and demo videos (testing credentials no longer required as of 2026-03-31). Legacy CRM cards are banned; must use UI Extensions (the new CRM Cards). Apps in marketplace-distribution mode are **capped at 25 installs until approval**. (Source: developers.hubspot.com changelog, May 2026.)
- **Surface:** UI Extension on the contact/deal record → a button "Generate BD follow-ups" → creates 3 tasks via our backend.
- **Effort:** 6–10 weeks first time (OAuth, UI extension, listing, security review). Faster on re-cert.
- **Pros:** Discoverable to ~200k+ HubSpot users. Trust signal. Free distribution.
- **Cons:** Marketplace review cycle is slow and pedantic. We must self-host an OAuth callback + token store.

#### B2. Bitrix24 Market app

- **Mechanics:** Submit through partner portal; moderation reviews metadata, support terms, icon, screenshots, pricing policy. Once approved, instantly available to millions of Bitrix24 users. (Source: helpdesk.bitrix24.com, course 268.)
- **Effort:** 4–6 weeks (Bitrix24's REST is what we already speak; the wrapper is mostly UI + metadata + a payment flow).
- **Pros:** We already have the integration. Bitrix24's market has less competition for BD-specific tools than HubSpot's.
- **Cons:** Bitrix24's user base skews CIS/EE/MENA — overlap with our Croatian/EU target is partial, not total.

#### B3. Pipedrive Marketplace app

- **Mechanics:** Pipedrive Marketplace app, OAuth, Pipedrive App Extensions (panel on the deal page). Lighter review than HubSpot.
- **Effort:** 4–6 weeks.
- **Pros:** Pipedrive's API maps almost 1:1 to our data model. Reviews are fast.
- **Cons:** No free tier means smaller funnel of users.

**General CRM-app trade-off:** Each marketplace = ~1 month of dev + ongoing recertification. Sequence them; don't parallelise. **Decision:** we are *not* leading with this path — see §5. We'll spin up a marketplace listing only if the extension shows concentrated traction in one CRM and the buyer specifically asks for in-CRM installation.

### C. Browser extension (Chrome + Firefox, Manifest V3) — **CHOSEN PATH**

- **What it is:** A button injected into the CRM's web UI (or on LinkedIn / a prospect's website) that scrapes the visible page or accepts a paste, then calls the CRM's API directly with the user's stored token. The extension detects the host (HubSpot, Pipedrive, Bitrix24, Attio, …) and dispatches to the matching `CrmClient` adapter.
- **Why this is the primary bet:**
  - **Platform-agnostic.** One codebase, every CRM. We become the BD-follow-up tool, not "the HubSpot tool." Adding a CRM = writing a new adapter, not standing up a new marketplace listing.
  - **No per-marketplace certification tax.** Each marketplace listing costs ~6–10 weeks of dev + ongoing recertification. The extension avoids that bill entirely.
  - **Meets the user where they already are.** The BD rep is already on the CRM tab or on LinkedIn Sales Nav. No tab switching, no "open the app."
  - **Fast distribution.** Chrome Web Store + Firefox Add-ons typically review in days, not the 2–4 week marketplace cycles.
- **Why now:** Manifest V2 is fully sunsetted in 2026. **All new extensions must ship MV3** (service workers, declarativeNetRequest, no remote code). The constraints are well-understood; AI/CRM helper extensions ship MV3 in 6–10 weeks routinely.
- **Cons (and how we'll handle them):**
  - **MV3 service-worker lifecycle is hostile to long-running work** — every call must be quick or queued; no persistent background page. Our flow is three API calls — fits cleanly. AI enrichment, if added later, needs an event-driven pattern.
  - No remote code execution means our JS bundle must ship complete; LLM/AI helpers (if added) call APIs, not load remote scripts.
  - Two stores = two review cycles. Firefox is usually fine; Chrome occasionally rejects for "purpose unclear" — we'll invest in store copy and a clear demo video upfront.
  - Token storage: the rep's CRM token sits in `chrome.storage.local` (encrypted at rest by the browser, but readable by other extensions in the same profile). We'll disclose this in the privacy policy and offer a "use webhook URL instead of OAuth" path for paranoid buyers.
- **Effort:** ~4–6 weeks for a multi-CRM v1 (Bitrix24 + HubSpot first; Pipedrive shortly after).
- **v1 scope:**
  - Detect host → load adapter (Bitrix24, HubSpot)
  - Popup UI: paste/confirm Contact fields → "Generate follow-ups" button
  - Creates Contact + Deal + 3 Tasks via the matching `CrmClient`
  - Settings page for per-CRM auth (Bitrix24 webhook URL, HubSpot OAuth)
- **Out of scope for v1:** AI enrichment, multi-user workspaces, billing, in-page DOM scraping of CRM pages (paste-first interaction only).

### D. Standalone web app — **CHOSEN, ships alongside extension**

- **What it is:** `bdlead.app` (or similar). User signs in, connects HubSpot/Bitrix24 via OAuth or webhook, pastes a lead's name + email + LinkedIn URL, sees AI-enriched lead preview, clicks "Push to CRM with 3 follow-ups."
- **Why now required:** §0 says the buyer is non-technical and AI is the selling point. Both demand a place to *demo* the product before install — that's the web app. It's also where sign-up, OAuth callbacks, billing, and account settings live.
- **Pros:**
  - Full control over UX and AI presentation — we can render an enrichment summary, suggested email opener, follow-up plan rationale, the whole sales-y experience.
  - Easy to demo: a single URL. No extension install required to evaluate.
  - Same origin as backend → no cross-origin token shuffling.
  - Required for billing and account management anyway.
- **Cons:**
  - We're now an auth provider + hosting target + billing target. Operational surface area is real.
  - BD rep has to switch tabs for daily use — which is exactly why the extension exists on top.
- **Stack (mirrors `../vanguard-game`):** Node (Fastify or Hono) + Python worker for LLM orchestration + Postgres + Redis + Docker Compose on a single VPS. Frontend: React/Vite or Next.js, whichever the team prefers.

### E. Slack / Teams bot

- **What it is:** `/bdlead add ACME, jane@acme.com, https://linkedin.com/in/jane` posted in a sales channel creates the CRM record.
- **Pros:** Slack is where small sales teams live; the friction of opening the CRM disappears. Slack app marketplace exists.
- **Cons:** Niche. Only useful where the buyer is already a Slack-first sales team. Slack app review is moderate.
- **Verdict:** Cheap add-on for phase 3 if a customer asks. Don't lead with it.

---

## 4. Decision Framework

The choice depends on which constraint binds:

| If the binding constraint is… | Build… |
|---|---|
| "Our prospect already uses HubSpot and wants this *inside* their CRM" | B1 (HubSpot Marketplace) |
| "We need one tool that works across whatever CRM the prospect happens to use" | C (browser extension) |
| "We need a free-standing thing we can demo to anyone in 30 seconds" | D (web app) |
| "Our pilot customers live in Slack and barely open the CRM" | E (Slack bot) |
| "We need zero new infra and an engineering-only audience" | A (MCP, current state) |

---

## 5. Recommendation — AI-Native Backend + Web App + Extension

We are building an **AI-native BD assistant**. AI is the selling point. The product needs persistent per-user memory, and the buyer is non-technical. That mandates a backend; the only real choice is which clients sit on top of it.

### Architecture (target state)

```
┌─────────────────────────────┐  ┌────────────────────────┐  ┌─────────────────────────┐
│  Web app (bdlead.app)       │  │  Browser extension     │  │  MCP server (existing)  │
│  • signup / OAuth / billing │  │  • content script on   │  │  • engineers / agents   │
│  • paste-a-lead demo UI     │  │    CRM tab + LinkedIn  │  │  • same CrmClient       │
│  • account & memory mgmt    │  │  • thin client → API   │  │                         │
└──────────────┬──────────────┘  └───────────┬────────────┘  └────────────┬────────────┘
               │                             │                            │
               └─────────────────────────────┴────────────────────────────┘
                                             │
                              ┌──────────────▼───────────────┐
                              │  Backend (VPS, vanguard-game │
                              │  pattern)                    │
                              │  • Node + Python workers     │
                              │  • Postgres (memory)         │
                              │  • Redis (queue/cache)       │
                              │  • LLM proxy → Gemini Flash  │
                              │    primary, Haiku fallback   │
                              │  • CrmClient adapters        │
                              │    (Bitrix24, HubSpot, …)    │
                              │  • Token vault per user      │
                              └──────────────────────────────┘
```

### Sequencing

1. **Phase 0 (now → 1 week):** Refactor `src/client.ts` into a `CrmClient` interface inside the existing MCP repo. This becomes the adapter contract used by *all* paths.
2. **Phase 1 — Backend + AI + Web app (~5–7 weeks):**
   - Spin up VPS deployment mirroring `../vanguard-game` (Docker Compose, Postgres, Redis).
   - LLM proxy with Gemini 2.5 Flash primary + Haiku 4.5 fallback. Budget guardrails per user.
   - Per-user memory schema: leads, outreach history, user writing style profile, follow-up cadence preferences.
   - CRM adapters: Bitrix24 + HubSpot.
   - Web app: sign-up, OAuth/webhook setup, paste-a-lead demo UI showing AI enrichment + 3-task plan, billing stub (Stripe test mode).
3. **Phase 2 — Browser extension (~2–3 weeks):**
   - Chrome + Firefox MV3 thin client over the same backend.
   - Detects host (CRM page or LinkedIn), pre-fills the paste form, calls backend, confirms.
   - No new business logic on the client.
4. **Phase 3 — Opportunistic distribution (post-launch):** Marketplace listings, Slack/Teams bot, Pipedrive adapter — driven by where paying users came from.

### Why AI from day 1 is the bet

- **Differentiation.** Without AI we are a form filler. CRM marketplaces have dozens of those, free.
- **Memory compounds.** Each lead the user puts through the system improves their personalised opener, cadence, and tone-match — switching cost grows over time.
- **Cost is contained.** Gemini 2.5 Flash + Haiku 4.5 keep marginal cost per lead well under $0.01. Even a €5/mo plan covers ~500 leads worth of inference comfortably.

The MCP server stays as the engine/reference and the surface for the engineer/AI-agent segment.

---

## 6. Risks & Caveats

- **We're now custodians of CRM tokens AND LLM keys AND customer data.** This is a real security perimeter. Mandatory before first external user: encrypted token storage (per-user envelope encryption), audit log on memory reads, GDPR-aligned data retention policy, one-page security note.
- **LLM cost surprises.** Gemini Flash / Haiku are cheap but a runaway prompt loop or a user pasting a 50k-token page can spike a bill. Hard per-user token budget + per-request size cap from day 1.
- **Model quality at the cheap end.** Gemini 2.5 Flash and Haiku 4.5 are good for enrichment and short follow-ups, less good for nuanced lead research. If output quality is the differentiator, we may need a "Pro" tier that calls Sonnet 4.6 for the same task — design the LLM proxy to switch models per request from day 1.
- **HubSpot's Sept 2024 contact cap (1,000)** means our heavy users will burn through their free HubSpot fast — pricing pitch should acknowledge this.
- **MV3 service workers terminate when idle** — the extension must call the backend synchronously and not try to do long work locally. Fine, since AI runs server-side anyway.
- **Marketplace review cycles** — only relevant when we get to Phase 3; budget 2–4 weeks buffer per submission.
- **VPS operational load.** Mirroring vanguard-game keeps the stack familiar but we now have two services to keep up, patch, and back up. Plan a shared ops runbook.

---

## 7. Open Questions

1. **Which two CRMs ship in v1?** Default: Bitrix24 (integration done) + HubSpot (reach). Swap HubSpot for Pipedrive if the team's warmest leads are Pipedrive shops.
2. **Pricing model.** Cheap LLMs let us hit a profitable €5–€9/user/mo at modest volume. Three credible shapes:
   - (a) Free tier with N AI enrichments/month, paid above
   - (b) Trial only (14 days), then paid
   - (c) Flat paid from day 1, no free
   Recommendation: **(a)** — free tier doubles as our demo, and our marginal cost is low enough to absorb tyre-kickers.
3. **What does the AI actually produce in v1?** Minimum: (i) one-paragraph company snapshot from public signals, (ii) personalized first-email opener in the user's tone, (iii) the 3-task follow-up plan with specific actions and timing. Anything more (multi-channel sequences, reply detection, A/B variants) is v2.
4. **Memory scope.** What do we persist per user? Recommendation: prior leads + outcomes, user tone/style profile derived from their accepted emails, industry/ICP preferences. Explicitly *not*: contents of CRM beyond what the user sent through our tool (avoids the "we read your whole CRM" privacy fight).
5. **Hosting.** Same VPS as `vanguard-game` (shared infra, faster ops), or a dedicated one? Recommendation: dedicated VPS once we have a paying user; share infra during dev.
6. **Model fallback policy.** Gemini Flash primary; when does Haiku 4.5 take over — only on Gemini outage, or also for specific task types where Haiku is stronger? Decide before LLM proxy ships.

---

## References

HubSpot:
- App listing and certification updates for May 2026: https://developers.hubspot.com/changelog/app-listing-and-app-certification-requirement-updates-for-may-2026
- App marketplace listing requirements: https://developers.hubspot.com/docs/guides/apps/marketplace/app-marketplace-listing-requirements
- Marketplace install limits (25-install cap pre-approval): https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits

Bitrix24:
- How to publish an application: https://helpdesk.bitrix24.com/courses/index.php?COURSE_ID=268&LESSON_ID=26048
- Bitrix24 Market overview: https://helpdesk.bitrix24.com/open/19498694/
- Developer portal: https://www.bitrix24.com/apps/dev.php

Chrome / Firefox extensions:
- What is Manifest V3: https://developer.chrome.com/docs/extensions/develop/migrate/what-is-mv3
- Manifest V3 migration timeline: https://developer.chrome.com/blog/resuming-the-transition-to-mv3
- Practical MV3 guide (2026): https://www.groovyweb.co/blog/chrome-extension-development-guide-2026
