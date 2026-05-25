# Development Options — Where Should `bitrix24-bd-lead` Live?

**Project:** `bitrix24-bd-lead` (creates Contact + Deal + 3 follow-up Tasks for B2B outreach)
**Date:** 2026-05-25
**Author:** Bojan Bartoniček
**Companion docs:** [`market_research.md`](./market_research.md), `project_kanban.md`

---

## 1. Executive Summary

The MCP server today is a **local-first developer tool** — Claude (or any MCP client) calls our server, which calls the Bitrix24 REST webhook. That's the easiest thing to keep building, but it ships to almost nobody outside the people who already run an MCP client.

To turn the prototype into something a non-technical BD person can use daily, we have five credible distribution paths:

| Path | Time-to-first-user | Reach | Maintenance | Recommendation |
|---|---|---|---|---|
| **A. Keep as MCP server (status quo)** | already shipped | tiny (MCP users only) | very low | Keep as the *engine* |
| **B. CRM-native app** (HubSpot/Bitrix24 marketplaces) | 6–10 weeks per CRM | large (marketplace traffic) | medium-high (per-CRM cert) | Phase 2 / opportunistic |
| **C. Browser extension** (Chrome + Firefox, MV3) | 4–6 weeks | broad, **platform-agnostic** | medium (MV3 quirks, two store reviews) | **★ Recommended primary** |
| **D. Standalone web app** (login → connect CRM → paste lead) | 6–8 weeks | self-served via own domain | high (auth, hosting, billing) | Defer to phase 3 |
| **E. Slack / Teams bot** | 3–4 weeks | niche (where the BD person lives) | low | Optional add-on |

**Decision: ship a multi-CRM browser extension first.** Rationale: we want to be **the BD follow-up tool, wherever the BD person works** — not "the HubSpot tool" or "the Bitrix24 tool." A marketplace-first strategy locks us to one CRM ecosystem at a time and costs ~6–10 weeks per CRM in certification. The extension covers every CRM the prospect happens to use from a single codebase, ships in ~4–6 weeks, and meets the BD rep in the tab they already have open.

**Sequencing:** Keep (A) as the canonical engine. Refactor `src/client.ts` into a `CrmClient` interface. Ship (C) covering Bitrix24 + HubSpot first, add Pipedrive behind the same UI. Treat (B) as **opportunistic** — only spin up a marketplace listing if extension traction in that CRM justifies it. Defer (D) and (E).

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

### D. Standalone web app

- **What it is:** `bdlead.app` (or similar). User signs in, connects HubSpot/Pipedrive/Bitrix24 via OAuth, pastes a lead's name + email + LinkedIn URL, hits Generate.
- **Pros:** Full control over UX, billing, and AI enrichment. Easy to layer on a paid tier.
- **Cons:** We're now an auth provider + hosting target + billing target. Significantly more surface area than the other paths. The BD rep has to switch tabs.
- **Verdict:** Defer until we have demand and revenue signal from (B) or (C). If we do build it, reuse the same `CrmClient` interface — it's literally another transport for the same engine.

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

## 5. Recommendation — Browser Extension First

We are betting on the **browser extension** as the primary distribution path. The principle: be **platform-agnostic**. The BD rep should not care which CRM their org runs; we should work on all of them.

1. **Refactor `src/client.ts` into a `CrmClient` interface first** (already proposed in `market_research.md` §3). Every path needs this; the extension *requires* it.
2. **Phase 1 (now → ~6 weeks):** Ship the Chrome + Firefox MV3 extension v1 covering **Bitrix24 + HubSpot**.
   - Bitrix24 first because the integration is already done.
   - HubSpot next because of free-tier reach (still ~200k+ active free users despite the Sept 2024 contact cap).
   - Both stores submitted in parallel.
3. **Phase 2 (weeks 6–10):** Add the **Pipedrive** adapter behind the same extension. No new UI, just a new adapter — proves the platform-agnostic thesis cheaply.
4. **Phase 3 (after first ~10 paying users):** Based on where activations came from, decide whether to:
   - (a) spin up an opportunistic marketplace listing for the dominant CRM, or
   - (b) build the standalone web app for buyers who can't install extensions (locked-down enterprise environments), or
   - (c) keep adding CRM adapters to the extension.

**The MCP server stays.** It remains the engine and the reference implementation for engineers/AI agents — same `CrmClient` interface, different transport.

---

## 6. Risks & Caveats

- **HubSpot's Sept 2024 contact cap (1,000)** means our free-plan customers will burn through it fast if they're heavy outbound — this affects pricing positioning more than which build path we pick, but raises the chance buyers convert to paid HubSpot, which changes which features our app can rely on.
- **MV3 service workers terminate when idle** — any "watch this CRM page and auto-create" feature must use event-driven triggers, not long-lived workers. Our current 3-API-call flow fits; future enrichment work may not.
- **Marketplace review cycles are unpredictable** — budget 2–4 weeks of buffer per submission and don't put a customer-promised date inside that window.
- **Token storage liability:** Whether we hold OAuth tokens server-side (paths B/D) or in `chrome.storage` (C), we're now a security-relevant component. Write a one-page security note before the first external user.
- **Cannibalisation risk:** If the browser extension is good enough, customers may never install the in-CRM app — meaning we paid for marketplace cert without ROI. Track install attribution from day one.

---

## 7. Open Questions

1. **Which two CRMs ship in extension v1?** Default: Bitrix24 (integration done) + HubSpot (reach). Swap HubSpot for Pipedrive if the team's warmest leads are Pipedrive shops.
2. **Free or paid from day one?** Extension users expect free, but charging early teaches us pricing faster. Recommend: free v1 with a clear "Pro" placeholder; introduce paid in v2 once we know what feature pulls conversion.
3. **AI enrichment in v1, or v2?** Adding "auto-research the lead's company" turns this from a 3-API-call tool into an LLM product — affects MV3 service-worker design, bundle size, privacy disclosures. Recommend: **defer to v2**.
4. **OAuth or webhook for HubSpot?** OAuth = smoother UX but requires us to run an OAuth callback service (small backend). Webhook/private-app token = no backend, but uglier setup. Recommend: ship webhook v1, add OAuth in v2.

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
