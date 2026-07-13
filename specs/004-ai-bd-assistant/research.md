# Research: AI-Native BD Lead Assistant

**Feature**: 004-ai-bd-assistant
**Date**: 2026-07-13

## Decisions

**LLM Choice**:
- Primary: Gemini 2.5 Flash (lowest cost, good quality for enrichment + short text).
- Fallback: Claude Haiku 4.5 (on primary error or for specific task types).
- Rationale: Keeps per-lead cost in $0.001–0.01 range as required by CONCEPT and development-options.

**Auth**:
- Users: Google OAuth2 (Sign in with Google) + short-lived JWT.
- Why: Lowest friction for non-technical SMB buyers. Matches recommendation in ARCHITECTURE.md.

**Memory**:
- Structured Postgres tables + optional pgvector embeddings for semantic recall of prior outreach and tone.
- Inject recent tone samples + ICP into prompts.
- Full vector strategy to be detailed in data-model iteration.

**Backend**:
- Align closely to vanguard-game: Python FastAPI for core + AI services.
- Possible thin additional layer if needed for specific Node libs (TBD in research follow-up).

**Clients**:
- Web: React + Vite (or Next.js for easier auth) — full onboarding surface.
- Extension: Thin MV3 client — reuses the same backend APIs.

## Open Questions Resolved / Carried

- v1 CRMs confirmed: Bitrix24 + HubSpot (per market research and dev-options).
- Token storage: envelope encryption (per-user).
- No client-side LLM calls.

## Sources

- docs/CONCEPT.md, ARCHITECTURE.md, FEATURES.md
- docs/development-options.md (distribution decision, cost targets)
- docs/market_research.md (regional CRM data)
- vanguard-game (proven patterns for FastAPI + React + Postgres + LLM factory)
- Current src/client.ts and src/tool.ts (refactor base)

Further research spikes (if needed):
- Exact token counts for a representative enrichment prompt + memory context.
- HubSpot associations API edge cases.
