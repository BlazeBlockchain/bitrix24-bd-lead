# Feature Specification: AI-Native BD Lead Assistant

**Feature Branch**: `004-ai-bd-assistant`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Build AI-native BD lead assistant with backend, web app and browser extension. Per-user memory, Google auth, cheap LLM (Gemini primary + Haiku), CrmClient for Bitrix24 + HubSpot. Grounded in CONCEPT, ARCHITECTURE, FEATURES, UI_UX docs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-technical BD rep creates first lead (Priority: P1)

As a non-technical BD rep in CEE or Africa using Bitrix24 (or HubSpot), I sign up with Google, connect my CRM once, paste a company name + decision maker + buying signal, see an AI-enriched preview with a personalized opener and 3 follow-up tasks, then push it so that a Contact, Deal, and 3 dated Tasks are created in my CRM.

**Why this priority**: This is the core value proposition and the minimal slice that proves the product for the target non-technical buyer. Everything else builds on this happy path.

**Independent Test**: Can be fully tested by a new user going through signup → connect → compose → push and verifying the records appear correctly in a CRM sandbox. Delivers end-to-end value without any other stories.

**Acceptance Scenarios**:

1. **Given** a fresh user with no CRM connected, **When** they complete Google sign-up, paste a Bitrix24 webhook, submit a valid lead brief and click push, **Then** Contact + Deal + exactly 3 Tasks are created with correct linking and deadlines (+4/+9/+14 days).
2. **Given** the same user on a subsequent lead, **When** they generate the preview, **Then** the output references their prior style/tone/ICP from memory and produces a personalized result.
3. **Given** HubSpot connection instead of Bitrix24, **When** the same flow is executed, **Then** objects are created with proper v3 associations and hs_timestamp values.

### User Story 2 - Daily use via browser extension (Priority: P1)

As the same BD rep, while on a CRM tab or LinkedIn profile, I trigger the extension, see a pre-filled form, generate the AI plan, and push without leaving my current workflow.

**Why this priority**: The web app is required for onboarding/billing/demo, but the extension is the daily driver that meets the user where they work. Both clients must work for the distribution strategy.

**Independent Test**: Install the MV3 extension, trigger from a test CRM page or LinkedIn, complete the flow, and confirm records are created via the shared backend.

### User Story 3 - Review history and benefit from memory (Priority: P2)

As a returning user, I can browse my past leads, see what was pushed, and have the system use accumulated memory (tone samples, outcomes, ICP) to improve future suggestions.

**Why this priority**: Memory is the key differentiator and switching cost. While basic memory effect is required for P1, rich history UI can come slightly after the core push flow.

**Independent Test**: After creating 2-3 leads, visit History, verify list + detail, create a 4th lead and observe memory influence in the preview.

### Edge Cases

- Invalid or expired CRM credentials → clear error + reconnect guidance; no partial records created.
- LLM provider failure (primary or fallback) → graceful degradation with user-friendly message and option to retry.
- Rate limits or per-user budget exceeded → informative message instead of silent failure or high costs.
- Duplicate-ish lead data → still creates (MVP has no dedup) but surfaces a warning.
- Mobile / small screen usage of web composer → fully usable (stacked layout).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to sign up and authenticate using Google OAuth and issue short-lived JWTs for subsequent API calls (web + extension).
- **FR-002**: System MUST support connecting at least Bitrix24 (via webhook URL) and HubSpot (via OAuth) per user, with encrypted storage of credentials.
- **FR-003**: System MUST provide a lead composer that accepts company, contact, signal, pain, and notes, then calls a server-side LLM proxy to return an enriched preview (company snapshot + personalized opener + exactly 3 follow-up tasks with timing and rationale).
- **FR-004**: System MUST, on user confirmation, create a Contact, a linked Deal, and 3 Tasks in the chosen CRM using a shared CrmClient abstraction, preserving correct associations and due dates.
- **FR-005**: The backend MUST maintain per-user memory (structured lead history + tone/ICP profile + optional vector embeddings) and inject relevant context into enrichment prompts for subsequent leads.
- **FR-006**: Both the web app and browser extension MUST call the same authenticated backend APIs for enrichment and push.
- **FR-007**: System MUST expose the existing `bitrix24_create_bd_lead` (and future multi-provider) capability via the MCP server using the shared core logic.
- **FR-008**: System MUST enforce per-user LLM cost guardrails and log usage (model, tokens, approximate cost).
- **FR-009**: Users MUST be able to view basic history of their leads and the exact plans that were pushed.

*Clarifications carried forward from grounding docs (to be resolved in plan/research):*
- **FR-010**: Auth method for users is Google OAuth primary [confirmed in ARCHITECTURE]; email/password fallback is P2.
- **FR-011**: Memory storage details (exact vector usage, retention) [NEEDS CLARIFICATION in detailed data model].

### Non-Functional Requirements

- **NFR-001**: Marginal LLM cost per lead MUST stay under ~$0.01 using Gemini 2.5 Flash primary + Haiku 4.5 fallback.
- **NFR-002**: Onboarding time for a non-technical user (first successful push) SHOULD be under 10 minutes.
- **NFR-003**: The extension MUST be Manifest V3 compliant and work on Chrome + Firefox.
- **NFR-004**: All CRM tokens MUST be stored with envelope encryption; LLM keys never leave the backend.
- **NFR-005**: The system MUST be deployable via Docker Compose on a single VPS (mirroring vanguard-game patterns).

### Key Entities

- **User**: Authenticated identity (Google-linked), preferences, memory profile.
- **CrmConnection**: Per-user, per-provider credentials (encrypted), auth type, validation state.
- **Lead**: The input brief + enriched output (snapshot, opener, tasks) + resulting CRM IDs.
- **OutreachHistory / MemoryProfile**: Data used to personalize future enrichments (tone samples, ICP, past outcomes, embeddings).
- **CrmClient**: Abstraction interface with adapters for Bitrix24 and HubSpot (createContact, createDeal, createTask).

## Success Criteria *(mandatory)*

- A new non-technical user can complete Google signup, connect Bitrix24 or HubSpot, create one lead via web, and see correct records in the CRM sandbox.
- A second lead for the same user shows measurable personalization from memory.
- The same backend calls succeed from the MV3 browser extension.
- MCP tool path continues to function using the shared orchestration.
- All P1 acceptance scenarios from FEATURES.md pass.
- Architecture matches the decisions in ARCHITECTURE.md and CONCEPT.md (cheap LLMs, per-user memory, dual clients, CrmClient).

## Scope

**In Scope (MVP slice)**:
- Google OAuth + JWT auth
- Bitrix24 + HubSpot adapters via CrmClient
- Backend (FastAPI/Python preferred + possible Node layer) with LLM proxy, memory layer (Postgres + pgvector), token vault
- Web app (React/Vite or Next.js) with composer, preview, history, connections
- MV3 browser extension (thin client)
- Basic usage tracking and guardrails
- Docker Compose deployment setup
- MCP compatibility layer

**Out of Scope (Roadmap)**:
- Real Stripe billing and paid tiers (stub only)
- Team workspaces / multi-user
- Additional CRMs (Pipedrive, Zoho, etc.)
- Advanced memory features (reply detection, A/B variants)
- Marketplace listings
- Full analytics dashboard

## Dependencies & Assumptions

- Access to Gemini API key and Anthropic key for fallback (server-side only).
- Sandbox/test accounts for Bitrix24 and HubSpot during development.
- VPS or Docker environment matching vanguard-game patterns.
- The four grounding documents (CONCEPT.md, ARCHITECTURE.md, FEATURES.md, UI_UX.md) in `docs/` represent the source of truth for product decisions.

## References

- `docs/CONCEPT.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURES.md`
- `docs/UI_UX.md`
- `docs/development-options.md`
- `docs/market_research.md`
- Sibling vanguard-game architecture and deployment patterns
- Current `src/client.ts` + `src/tool.ts` (to be refactored into shared CrmClient + core)

## Open Questions / NEEDS CLARIFICATION

- Exact memory schema and vector strategy (to be resolved during data-model in plan phase).
- Backend language split (pure FastAPI vs hybrid) — default to vanguard alignment unless clarified.
- Pricing model details (free tier limits) — stub for MVP.
- Whether to use Next.js for web (auth/billing convenience) or stick to Vite + React.

---
*This spec is derived from the product foundation docs created in the prior phase and the approved implementation plan.*
