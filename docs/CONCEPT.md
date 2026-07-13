# CONCEPT: AI-Native BD Lead Assistant

**Project:** bitrix24-bd-lead  
**Status:** Draft (Phase 0 grounding)  
**Date:** 2026-07-13  
**Based on:** `docs/development-options.md`, `docs/market_research.md`, `docs/market-research-handoff.md`, `docs/project_agents_tasks.md`

---

## Problem Statement

B2B business development (BD) representatives — especially in SMBs — spend disproportionate time on low-value mechanical work:

- Manually creating Contact + Deal records in the CRM.
- Planning and scheduling follow-ups (typically 3 touches over 2 weeks).
- Repeating the same research and personalization for every lead.
- Remembering (or forgetting) what tone, cadence, and messaging worked for similar prospects in the past.

Current solutions fail non-technical users:

- **MCP servers / Claude tools** (current state of this project): Require Node install, webhook URLs, JSON config, and an LLM desktop client. Audience shrinks to engineers who could build it themselves.
- **CRM-native macros or marketplace "lead creators"**: No AI enrichment, no memory of past outreach, generic outputs. They are form-fillers.
- **Free tiers of CRMs**: Bitrix24 free caps tasks at 100 total (~33 leads at 3 tasks each). HubSpot free (post-Sept 2024) caps at 1,000 contacts. Heavy users hit walls fast.

The result: slow pipeline velocity, inconsistent follow-up, and no compounding intelligence per rep.

---

## Market Size (CEE + Africa Focus)

**Primary wedge markets (from verified 2026 data in market_research.md):**

- **Central Europe / CIS**: Bitrix24 holds ~19.12% global CRM market share with 22,000–23,000 active domains. Strongest concentration in Russian-speaking and CEE markets. HubSpot is the common "upgrade path" (net migration gains from Bitrix24 documented).
- **Africa (South Africa benchmark — best data available)**: Zendesk 20.7%, ActiveCampaign 14.7%, HubSpot 13%, Zoho 5.4%. Only HubSpot, Salesforce, and MS Dynamics have local South Africa support presence. MEA (combined with LatAm) projected ~$18B CRM market by 2030. HubSpot growing 20–25% YoY, strongest in SMB/mid-market.

**Implications for sizing:**
- Bottom-up wedge: A single free-tier Bitrix24 user exhausts ~33 leads before hitting task limits. Paid conversion pressure is real.
- Top-down: SMB BD/sales teams in these regions (tens of thousands of potential accounts) currently have no affordable AI + memory tool that works across their actual CRMs without technical setup.
- SAM estimate direction (to be refined by market-research skill): Low thousands of paying SMB reps in target regions at €5–9/mo yields a realistic early revenue pool before expansion to global English-speaking markets.

**Competitive gap:** No major player combines (a) true AI enrichment from day one, (b) per-user memory that improves output over time, (c) thin-client distribution (web + extension) that works inside whatever CRM the buyer already uses, and (d) sub-€0.01 marginal cost via cheap models.

---

## Solution & UVP

**Core offering:** An AI-native BD assistant that turns a minimal lead brief into a fully enriched, ready-to-execute skeleton in the user's CRM — plus a 3-step personalized follow-up plan — while getting smarter with every use.

**User flow (non-technical ideal):**
1. Sign up (Google OAuth recommended).
2. Connect CRM (paste Bitrix24 webhook or complete HubSpot OAuth — one time).
3. Paste or trigger: company name + decision maker + buying signal + pain.
4. See preview: one-paragraph company snapshot, tone-matched email opener, and 3 concrete follow-up tasks (Check+Connect day +4, Short Bump +9, Close the Loop +14).
5. Push → Contact + Deal + 3 Tasks created with correct linking and deadlines.
6. History + memory compounds: future leads automatically reference prior style, cadence, won/lost patterns, and ICP.

**UVP (differentiation):**
- **AI is v1, not v2.** Without the enrichment + rationale the product is indistinguishable from free macros.
- **Memory is the moat.** Per-user profile (writing tone, typical follow-up success patterns, industry preferences) is stored and injected into prompts. Switching cost grows with usage.
- **Multi-surface, single backend.** Web app = frictionless demo + billing + account management. Extension = lives where the rep already works (CRM tab or LinkedIn). MCP stays for power users/agents.
- **Platform-agnostic distribution.** One adapter contract (`CrmClient`) supports Bitrix24 + HubSpot in v1; adding Pipedrive/Zoho later is an adapter, not a new marketplace cert marathon.
- **Cost discipline.** Gemini 2.5 Flash primary + Haiku 4.5 fallback keeps per-lead inference in the $0.001–0.01 range. Free tier is economically viable.

**What it is not (MVP scope boundaries):**
- Not a full sales engagement platform or sequencer.
- Not a CRM replacement.
- Not reading the user's entire CRM history (privacy boundary).

---

## Target Users

**Primary (P1):**
- Non-technical BD reps, sales managers, and solo founders in Croatia, broader CEE/CIS, and English-speaking Africa (SA + expansion to Nigeria/Kenya/Egypt).
- They use Bitrix24 (dominant locally) or HubSpot (upgrade + Africa growth).
- They do their own outreach; time is the bottleneck; they hate context switching and config.

**Secondary:**
- Small sales teams or agencies that want consistent follow-up without hiring an ops person.
- Engineers/power users who discover via the MCP surface (kept alive deliberately).

**Explicitly out of scope for messaging:**
- Large enterprise Salesforce teams (they have dedicated ops + budget for heavier tools).
- Pure technical users who are happy living in Claude Desktop + webhooks.

---

## Success Vision (One Sentence)

"Every BD rep who pastes a name into bdlead once never wants to go back to manual CRM entry or generic follow-up templates — because the output feels like it was written by a smarter, better-rested version of themselves who remembers every deal they've ever worked."

---

## Sources & References (internal)

- `docs/development-options.md` (premise, distribution decision, architecture target, risks).
- `docs/market_research.md` (CRM scoring + regional §1a data with sources).
- `docs/market-research-handoff.md` (summary + pitfalls).
- Sibling `vanguard-game` (proven VPS + Docker + Postgres + cheap LLM primary/fallback pattern).

*Market sizing numbers to be refreshed/expanded with `tessl__market-research` skill before final pricing or investor use.*
