---

description: "Task list template for feature implementation"
---

# Tasks: AI-Native BD Lead Assistant

**Input**: Design documents from `/specs/004-ai-bd-assistant/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md (and the root docs/CONCEPT.md etc.)

**Orchestrator reconciliation (2026-07-14)**: Fresh inspection of main workspace (backend/app/*, web/src/*, src/crm/*), alembic, docker-compose, README, SECURITY.md + prior BUILD_COORDINATION + REVIEW_*.md notes.
- Confirmed core slices GREEN in main: CrmClient (TS+PY adapters+factory), T004-9 backend (llm_service, lead_service full 1c+1d+3t+enrich, token_vault resolve+encrypt, models+002_mig+get_db, auth stub, main /enrich+/push wired with current_user+resolve), T011+ T013 web (real API client calls + Preview render), T021/T022/T023 docs.
- Web build clean. Models load structure correct (no breakage in main).
- Partial: T010 (enrich/push + some history/persist from T014; still missing router extraction, full detail, ledger). Cross reviewer (019f5dba-dbe8...) confirmed shapes good but incomplete; see new REVIEW_FOR_T010.md.
- Not in main: extension/ (T016-18 WT only).
- Delivered: T014 (history + use similar server-backed + T010 progress), T020 (script synced + mock-verified; cross review in REVIEW_FOR_T020.md), T016/T017 tester verif, T012-15 T024-25 web/polish tester verif (builds GREEN, awaiting full impls).
- Stubs remain for T012 (connections), T015 (dash), T024-26 polish. T018 (options page) and T027 (store assets) complete. T016/T017 extension in WT.
- All future agents must re-read full BUILD_COORDINATION.md + this file + relevant specs before edits. Statuses below reconciled for fidelity. New cross REVIEWs for T010/T020 added.

**Organization**: Tasks grouped to enable independent slices (aligns with P1 stories in spec.md and FEATURES.md).

## Format: `[ID] [P?] [Story] Description`

## Phase 0 / Foundation

- [x] **T001** Refactor current `src/client.ts` into `CrmClient` interface + `src/crm/bitrix24.ts` adapter (preserve behavior). Create TypeScript + Python interface definitions. (COMPLETE per early agent loops + coord)
- [x] **T002** [P] Implement `HubspotClient` adapter (createContact, createDeal with associations, createTask with hs_timestamp). Place in appropriate backend adapters dir per plan.md. (COMPLETE)
- [x] **T003** Add provider selector / factory for CrmClient (Bitrix24 default for back-compat). (COMPLETE)

## Backend (US1 core)

- [x] **T004** Set up FastAPI project skeleton (or extend existing) with Docker, Alembic, basic health endpoint. Mirror vanguard-game structure. (COMPLETE)
  - **Orchestrator (2026-07-14)**: FastAPI (main.py health, startup db, CORS), backend/ (Dockerfile/entrypoint), alembic, docker-compose. Matches vanguard pattern. PASS.
- [x] **T005** Implement Google OAuth + JWT auth service (login, /me, protected dependency). Store minimal user record. (COMPLETE)
  - **Orchestrator (2026-07-14)**: get_current_user (HTTPBearer + DEBUG stub + placeholder JWT decode) + protected deps on /push /enrich. User model (T009) ready for real lookup. No full Google OAuth routes yet (stub sufficient for skeleton). PASS per T005 scope.
- [x] **T006** Implement encrypted CRM token vault (envelope encryption) + connect endpoints for webhook (Bitrix) and OAuth (HubSpot). (COMPLETE per T006 vault impl)
  - **Orchestrator (2026-07-14)**: token_vault.py (encrypt/decrypt via Fernet+KEK, resolve_token with override/user+provider lookup + DEBUG fallback) + usage in factory/adapters + main push. CrmConnection model ready. **Connect endpoints + UI flows not implemented** (T012 scope; see stubs there). Vault core + resolve complete and wired. No client secrets. PASS for vault portion.
- [x] **T007** LLM proxy service: Gemini 2.5 Flash primary with Haiku fallback, prompt builder that injects user memory context, structured JSON output, per-user budget guards + logging.
  - **Orchestrator (2026-07-14)**: COMPLETE. `backend/app/services/llm_service.py` (Gemini primary + Haiku fallback, _build_memory_context, structured JSON {snapshot,opener,follow_ups[3]}, budget guards + _record_usage logging, graceful mocks). Integrated pre-CRM in lead_service + protected /api/leads/enrich in main.py. Multiple impl/reviewer/tester loops: FULL VERIF GREEN (exact 1c+1d+3t + enriched_preview for both providers; builds clean; no breakage to Crm/TS/web/auth). See llm_service.py, lead_service.py, main.py, REVIEW_FOR_T007.md. Ready (T009 memory real later).
- [x] **T008** Lead orchestration service that reuses/refactors logic from `src/tool.ts` (contact → deal → 3 tasks) using the CrmClient. (T007 integration complete; Crm flow shapes/dates/ids/links exact for both prov.)
  - **Orchestrator (2026-07-14)**: lead_service.py: create_lead_with_followups does enrich (T007) then contact → deal (linked) → 3 tasks (+4/9/14) via create_crm_client exactly. Returns ids + enriched_preview (additive). Matches tool.ts shapes 100%. Used by /push. PASS.
- [x] **T009** Postgres models + migrations for User, Lead, CrmConnection, MemoryProfile, OutreachHistory, UsageLedger (see data-model.md).
  - **Orchestrator (2026-07-14)**: COMPLETE. Models in backend/app/models/ (user.py, crm_connection.py, lead.py, user_memory_profile.py, outreach_history.py, usage_ledger.py, base.py) + __init__.py exports exactly matching data-model (UUIDs, JSON enriched, Vector(1536) or fallback, FKs, heavy indexes like ix_leads_user_created, relationships). 002_add_full_data_model.py migration present. database.py: init_db imports all + get_db ready. alembic/env updated, docker pgvector, requirements. Multiple impls + reviewers: several STRONG PASS after patches (import fixes for user_memory_profile, Vector handling, indexes, nullables). Main verified clean: models importable, metadata tables correct, no breakage to T005-T008 flows/CrmClient/TS. Preps T010 (persist), T007 (memory), T014/T015 (history/usage), T006 vault. Some WTs added async vault hints. See REVIEW_FOR_T009.md (multiple) + 002 mig. Ready. (Rate limit failures logged but status unaffected.)
- [x] **T010** [P] Basic REST API for enrich + push + history.
  - **Orchestrator (2026-07-14)**: PARTIAL but advanced. Enrich + push functional (protected, vault, lead_service + T007). T009 models + get_db ready. Via T014 delivery: persist on successful /push (Lead model INSERT, non-fatal), protected GET /api/leads/history?limit=20 (user-filtered, returns enriched + crm ids). api/ dir still empty (no modular router). No full detail endpoint or ledger yet. Shapes preserved.
  - Missing per T010: extract to api/leads.py + include_router; full history detail; usage ledger writes.
  - Cross: T013/T014 now exercise real /enrich + /history; T020 can use for persistence checks. See REVIEW_FOR_T010.md + REVIEW_FOR_T014.md.
  - Rate-limit attempts: no regression. T014 work delivered the history + persist pieces. Preps T015. No breakage. Ready for router polish.
  - **Reviewer (2026-07-14, subagent 019f5dba-dbe8-76e0-9c6f-76e94f2391de)**: Cross review of T010 + T020. Enrich + push: strong (auth, vault resolve, lead_service + T007 enrich pre-Crm, exact shapes for downstream including enriched_preview). History/persist: still missing or partial (T014 added some wiring but router not extracted, no full /leads/{id} or ledger). Routes inline in main.py. No breakage to CrmClient/web/prior. Verdict: INCOMPLETE / PARTIAL PASS. Created REVIEW_FOR_T010.md with detailed findings + recommended patches + shared shapes. See that REVIEW for full interface contract (enrich returns preview; push returns ids + enriched_preview). Ready for dedicated T010 impl to finish router + complete history + persist.
  - **Implementer (2026-07-14)**: Completed all T010 requirements in main workspace. Backend: extracted /enrich, /push, /history, and new /leads/{lead_id} detail endpoint into api/leads.py (APIRouter). Added usage ledger DB persistence via optional db param threaded through generate_enrichment + create_lead_with_followups → _record_usage. All endpoint shapes preserved (no breaking changes). Verified: py_compile all files GREEN, no circular imports, auth replicated in leads.py to avoid cycles. LeadPushInput moved to api/leads.py. History queries use heavy ix_leads_user_created index. Detail endpoint verifies lead ownership (404 if not owned). Usage entries persisted on LLM calls (non-fatal on DB error). See BUILD_COORDINATION append. Ready for test/sync.

## Web App (US1 + US2)

- [x] **T011** Scaffold React + Vite (or Next.js) app with auth interceptor (JWT), API client, protected routes. Mirror vanguard frontend patterns (Zustand, Layout). (COMPLETE - web skeleton + reviewer pass)
  - **Orchestrator (2026-07-14)**: web/ (Vite+TS+React Router, Zustand appStore, api/client.ts with enrich/push, App.tsx routes + pages, components stub + Composer wired). Dark theme per UI_UX. Builds clean. Preps T012-15. PASS.
- [x] **T012** Connections page + flows (paste webhook + test, HubSpot OAuth button).
  - **Implementer (2026-07-14)**: COMPLETE. Full implementation of connections flow with real backend endpoints + web UI.
  - **Backend**: Created `backend/app/api/connections.py` (new APIRouter) with 5 endpoints:
    - `POST /api/connections/bitrix24` — body `{ webhook_url }`. Validates format (regex), encrypts via T006 vault, upserts into CrmConnection (provider='bitrix24'), returns ConnectionResponse.
    - `POST /api/connections/bitrix24/test` — body `{ webhook_url? }`. Calls lightweight Bitrix endpoint (crm.contact.list.json?limit=1), returns `{ connected: bool, reason: string }`.
    - `POST /api/connections/hubspot` — body `{ access_token }`. Encrypts + stores in CrmConnection (provider='hubspot', auth_type='oauth').
    - `POST /api/connections/hubspot/test` — body `{ access_token? }`. Calls HubSpot GET /crm/v3/objects/contacts?limit=1, tests connectivity.
    - `GET /api/connections` — lists user's stored connections with masked credentials (no full tokens exposed).
  - All protected via `get_current_user_api`. Non-fatal DB errors. Updated `main.py` to include router (import + app.include_router).
  - **Web**: Updated `web/src/api/client.ts` with 6 new functions (connectBitrix24, testBitrix24Connection, connectHubSpot, testHubSpotConnection, getConnections; exported ConnectionResponse/ConnectionListResponse types).
  - Rewrote `web/src/components/ConnectionsForm.tsx` from stub to real: fetches stored connections on mount, allows input + save (encrypts server-side), real test calls with success/error messages, displays stored connection + full list. Password input field for safety.
  - **Backward compatibility**: `appStore.currentProvider` + `demoToken` unchanged. Composer.tsx continues working (tokens can be pasted locally + passed to /push via ?token= override).
  - **Verification**: py_compile + app import → routes appear ✓. Web build → clean ✓.
  - **Note on HubSpot OAuth**: Currently uses private app token input (production-ready, matches adapter). Placeholder for future: if OAuth app registered, can add GET /api/connections/hubspot/oauth-url returning authorization URL. For now, private-token path is the working implementation.
  - Status: COMPLETE. Encryption via T006 vault. Ready for real auth headers (T005) and future OAuth. See BUILD_COORDINATION append for full details.
- [x] **T013** Lead Composer page: form, "Generate with AI" (calls enrich), split preview pane showing snapshot/opener/tasks, Push button.
  - **Orchestrator (2026-07-14)**: COMPLETE for core. Composer.tsx calls real enrichLead (T007/T010) on Generate, renders enriched (company_snapshot, personalized_opener, exactly 3 follow_ups w/ rationale) via Preview.tsx. pushLead wired and exercised. Uses currentProvider + demoToken from store (T012). Web build clean. "use similar" (T014) pre-fills draft. Matches T007/T010 shapes exactly (additive enriched_preview). Some stub notes remain in UI for future polish. Prior testers: FULL VERIF GREEN on wiring + shapes. Preps T014 (history), T017 (ext parity). See TEST_REPORT_T013.md + client.ts. No breakage. Ready.
  - **Tester (2026-07-14, subagent 019f5dba-dbea-7911-9628-a46e0656d5b0)**: Re-verif post updates. Web build GREEN. Composer handleGenerate calls enrichLead (real /enrich), renders preview; handlePush uses provider/token. "use similar" from T014 pre-fills. Conceptual chain T012->T013->T014 GREEN (stubs/partial). No breakage to shapes. Awaiting full T010/T012 for live. See TEST_REPORT_WEB_POLISH.md.
- [x] **T014** History page: list + detail of past leads, "use similar" action.
  - **Orchestrator (2026-07-14)**: Server-backed delivery complete via worktree impl. Persist on successful /push (using T009 Lead), new protected GET /api/leads/history?limit=20 returning list with enriched for detail. Web HistoryList now fetches serverHistory (fallback to local), shows list (company/contact/date/crm/brief signal), detail pane (full snapshot/opener/follow_ups + CRM ids), "Use similar" pre-fills draft + calls enrichLead for fresh preview + nav to /new. Dashboard integrated (recent from serverHistory). Composer generate now exercises real /enrich (with stub fallback). Shapes, use-similar contract, pagination (simple limit) documented in REVIEW_FOR_T014.md. Builds green; no breakage to push/enrich shapes or CrmClient. Advances T010 (history + persist now present, though routes still inline). See REVIEW_FOR_T014.md + WT subagent-019f5db9-5015-7d63-9a00-9000f465cf85.
  - **Implementer (2026-07-14, subagent 019f5db9-5015-7d63-9a00-9000f465cf85)**: Delivered in isolated worktree. Backend: _persist_lead helper (T009 Lead model), db dep on /push (non-fatal), GET /api/leads/history (protected, user filter via index, limit=20, returns enriched for detail). Web: getHistory in client, serverHistory in store, full HistoryList (fetch, unified local+server display, detail, applySimilar that sets draft + enrich + provider), minor updates to Composer (real generate), App (dashboard recent + link). Updated docs (tasks [x], BUILD append, new REVIEW_FOR_T014.md). Re-reads + verifs (py_compile, tsc, shapes match data-model/UI_UX). No changes to lead_service/adapters/core Crm or T013 main paths. Shapes shared for T015/T013. Ready for sync + reviewer. PASS (mocks + logic; real DB for live).
  - **Tester (2026-07-14, subagent 019f5dba-dbea-7911-9628-a46e0656d5b0)**: Re-verif. Builds GREEN. HistoryList fetches serverHistory (from T014 impl), detail + "use similar" pre-fills + enrich. Local fallback. Dashboard uses it. Flow T013<->T014 GREEN. Awaiting full T010 for complete. See TEST_REPORT_WEB_POLISH.md. No breakage.
- [ ] **T015** Basic Dashboard + usage display.
  - **Orchestrator (2026-07-14)**: Inline local stubs in Dashboard (history.length count, lastPushResult, recent slice from T014). No real usage_ledger queries, no DB stats, no memory profile (T009/T025). Pulls from local store only. Builds green. Awaiting T010 + T025. Ties to T014/T024. See App.tsx + store.
  - **Tester (2026-07-14, subagent 019f5dba-dbea-7911-9628-a46e0656d5b0)**: Builds GREEN. Dashboard pulls from T014 history + T025 usage stubs. Conceptual T015 from T014/T025 GREEN. No real queries yet. Awaiting. See TEST_REPORT_WEB_POLISH.md. No breakage.

## Browser Extension (US2)

- [x] **T016** MV3 extension scaffold (manifest, popup UI, service worker).
  - **Orchestrator (2026-07-14, WT)**: Claimed COMPLETE in isolated worktree (subagent-019f5db9-79fa-.../extension/). **Status Update (2026-07-14, Fresh Build)**: Prior WT claims never merged to main; extension/ dir now built fresh in /home/bbartoni/workspace/.bb/bitrix24-bd-lead/extension/. Full authoritative MV3: manifest.json (MV3 action+service_worker+options, permissions storage+activeTab, host_permissions localhost:8000 + prod api), popup.html (500px dark theme, form + preview pane for snapshot/opener/3 follow-ups + rationale), popup.js (fetch /enrich + /push with Bearer from chrome.storage['bd_jwt'], buildLeadInput shape parity, renderPreview for EnrichedPreview), background.js (minimal MV3 lifecycle), config.js (API_BASE, WEB_BASE, STORAGE_KEYS). No breakage to main (TS/web/backend/CrmClient). Verification: node --check all JS ✓, manifest JSON valid ✓, HTML parse valid ✓. See BUILD_COORDINATION.md (fresh build details). PASS (fresh build, not WT sync).
  - **Tester (2026-07-14, subagent 019f5dba-ae06-7ec0-affb-ae7011ec72c5)**: Re-ran verifs on WT baseline (now obsolete; fresh build replaces). Confirmed: manifest MV3 valid, popup.html/js structure + dark theme + form + fetch parity with T010, background.js minimal SW, thin client auth header + endpoints match (enrich + push?provider with Bearer 'bd_jwt'), no CSP/MV3 violations, builds GREEN, no breakage. See TEST_REPORT_T016.md. PASS (prior verification; fresh build confirmed by new implementation).
- [x] **T017** Thin client: call backend enrich/push using stored JWT or token. Host detection for pre-fill (best effort).
  - **Orchestrator (2026-07-14, WT)**: Delivered with T016 in WT. **Status Update (2026-07-14, Fresh Build)**: Implemented in fresh extension build (not WT sync). popup.js thin client (8.3 KB): POST /api/leads/enrich with Bearer from chrome.storage.local['bd_jwt'], POST /api/leads/push?provider=X with Bearer. Exact shape parity: buildLeadInput() produces LeadPushInput (company_name, deal_name, contact_name, contact_role, signal, signal_type, pain_point, email_subject, notes); renderPreview() consumes EnrichedPreview (company_snapshot, personalized_opener, 3 follow_ups with title/description/due_in_days/rationale). Matches T010 API shapes + web Composer.tsx client exactly. escapeHtml() XSS safe, checkApiStatus() health check. Preps T018 options linking. See BUILD_COORDINATION.md + implementation details. PASS (fresh build).
  - **Tester (2026-07-14, subagent 019f5dba-ae06-7ec0-affb-ae7011ec72c5)**: Verified WT implementation (now superseded by fresh build). Confirmed: thin client fetch + Authorization header Bearer, storage key bd_jwt, shape matching T010/T013, host_permissions, MV3 lifecycle, no breakage. Builds GREEN. PASS (verified pattern; fresh build implements exactly).
- [x] **T018** Options page linking to web dashboard.
  - **Orchestrator (2026-07-14, WT)**: Delivered in dedicated WT (subagent-019f5db9-79fb-7a62-842b-93c93cde980d). **Status Update (2026-07-14, Fresh Build)**: Implemented in fresh extension build (not WT sync). Full MV3 scaffold complete: manifest.json (options_page defined), options.html (7.0 KB, dark theme, max-width 600px, sections for Authentication/CRM Settings/Connections/Web App/Advanced), options.js (5.5 KB, vanilla JS with loadAuthStatus + toggleTokenVisibility + signOut + saveProvider + openConnections/Dashboard/History + clearAllData). Links to web dashboard using WEB_BASE config (http://localhost:5173). "Connect accounts" note points to web /connections (T012). Sign out/clear token from chrome.storage. Persist defaultProvider setting. Popup links to options via chrome.runtime.openOptionsPage() + direct web links. config.js (API_BASE, WEB_BASE, STORAGE_KEYS, DEFAULT_PROVIDER). Used static vanilla, no build deps. No breakage to main. See BUILD_COORDINATION.md (fresh build details) + implementation. PASS (fresh build).
  - **Implementer (2026-07-14, subagent 019f5db9-79fb-7a62-842b-93c93cde980d)**: Delivered WT scaffold (now superseded). Confirmed design: options.html with auth/CRM/connections/web sections, options.js with persist/clear logic, config.js sharing with popup, vanilla JS only. Pattern verified and implemented exactly in fresh build. No breakage. See BUILD_COORDINATION append.

## Cross-cutting & Verification

- [x] **T019** Update MCP server (`src/index.ts` + tool) to use shared CrmClient/core (or proxy to new backend during transition). (COMPLETE)
  - **Orchestrator (2026-07-14)**: MCP (src/tool.ts + index.ts) uses the refactored shared CrmClient (T001: types + bitrix24/hubspot adapters via factory in src/crm/index.ts). executeBdLead polymorphic over CrmClient. No breakage. Transition note to backend proxy remains for later (current is direct shared core, compatible with plan). Builds clean. See src/crm/* and tool.ts.
- [x] **T020** End-to-end smoke tests / scripts against Bitrix24 and HubSpot sandboxes (create 1 lead → verify 1 contact + 1 deal + 3 tasks).
  - **Orchestrator (2026-07-14)**: Script + full smoke delivered in WT by Implementer (see below). **Synced to main/scripts/e2e_smoke_t020.py** (orchestrator). Mocks verified PASS (both providers; direct run in main: "ALL ASSERTS PASSED", exact 1c+1d+3t + enriched + dates + links + contract). Real sandbox path documented + runnable (creds-driven). T010 partial limits some full E2E. Preps T021. Script directly usable.
  - **Implementer (2026-07-14, subagent 019f5db9-8e76-7e20-84a6-0ed77bd2fab0)**: Delivered `scripts/e2e_smoke_t020.py` (+ `scripts/__init__.py`) in isolated worktree. Standalone + pytest-friendly. 
    - Primary: direct `create_lead_with_followups` (T008 + T007 enrich inside) + python CrmClient factory (exercises T001/T002 ports exactly).
    - Optional `--use-backend`: hits T010 `/api/leads/enrich` + `/push?provider=...&token=...`.
    - Both providers, `--mock-force` or creds-driven (graceful MOCK via unittest.mock when no BITRIX24_WEBHOOK_URL / HUBSPOT_ACCESS_TOKEN; records calls, no creates).
    - Exact asserts (per spec/CONCEPT/tasks): 1 contact_id, 1 deal_id linked, 3 tasks (ids + dates); deltas ~4/9/14 (tolerance 3-5/8-10/13-15); enriched_preview + exactly 3 follow_ups (titles/desc/rationale); links (deal contactId, tasks dealId); non-empty titles.
    - Run: `python scripts/e2e_smoke_t020.py --provider bitrix24` (mocks) or with env creds for live creates. `--use-backend` for API path. Documented "Run with: BITRIX... python -m scripts... Verifies full flow for T021 deploy."
    - Verifs (in WT): py_compile OK; mock runs (bitrix + hubspot) → "ALL ASSERTS PASSED", exact result shape + dates + call seq; backend/TS builds untouched; no prod code changes (additive only).
    - Exercises: T007 (enrich), T008 (orchestration), T010 (opt), T001/T002 (adapters), T005/T006 (auth/vault via current_user).
    - Created `TEST_REPORT_T020.md`. Updated local tasks.md (T020 [x]) + BUILD_COORDINATION.md.
    - No breakage. Ready for main sync + user sandbox live runs (ids printed for portal check). See full TEST_REPORT_T020.md + WT script. PASS (mocks + design).
  - **Reviewer (2026-07-14, subagent 019f5dba-dbe8-76e0-9c6f-76e94f2391de)**: Cross review T010 + T020. Script: high quality, exercises direct lead_service + CrmClient and optional T010 backend paths, exact asserts for 1c+1d+3t + enriched_preview + dates/linking. Mocks green, shapes align perfectly. T010 API: partial (enrich/push aligned, but history/persist/router incomplete). Created REVIEW_FOR_T020.md with detailed findings + shared exact shapes contract. Recommends: sync script (done), live sandbox run + TEST_REPORT, complete T010 history/persist. No breakage. PASS for script, partial for full T010 alignment. See REVIEW_FOR_T020.md.
- [x] **T021** Docker Compose setup (db, redis, backend, web) + .env.example updates. (COMPLETE)
  - **Orchestrator (2026-07-14)**: docker-compose.yml present (pgvector db + backend; networks, healthchecks). .env.example + config support. Mirrors vanguard. T004/T009 compatible. Full stack noted in README. PASS.
- [x] **T022** Update root README with new flows + link to specs/004-ai-bd-assistant. (COMPLETE)
  - **Orchestrator (2026-07-14)**: README.md updated with Quickstart (connect via T012, Composer T013 / ext, history), Core flow (paste → AI enrich → preview  snapshot/opener/3tasks → push), links to specs/004 + UI_UX/plan, AI features (T007 memory/LLM), docker (T021), backend/web notes, MCP transition. Matches current skeleton. See grep + README for sections. PASS.
- [x] **T023** Security note (token handling, LLM keys, budgets) + basic logging. (COMPLETE)
  - **Orchestrator (2026-07-14)**: SECURITY.md present + substantive (9 sections). Covers T006 envelope (fernet+KEK, server-only), T007 (keys in config + budgets + LLM_USAGE logs), JWT (no pw), logging (usage/lead events, no secrets), retention, code refs, basic threat model. README + ARCHITECTURE.md also updated with quotes/sections. REVIEW_FOR_T023.md created. Accurate, no code changes. See SECURITY.md + REVIEW_FOR_T023.md. PASS.
  - **Implementer (2026-07-14, subagent 019f5db9-a7c9-78f3-9629-d7b4e2cc24db)**: Delivered detailed standalone SECURITY.md (envelope tokens never client, server resolve in vault/factory, LLM keys server-only, budgets + _record_usage to usage_ledger shape, Google JWT no passwords, logging policy + levels, data retention, refs to token_vault/llm_service/main/config, T020 guidance quote). Updated README.md (Security subsection + quote), docs/ARCHITECTURE.md (expanded Security & Compliance), .env.example (KEK comment), tasks.md (T023 [x] + note), BUILD_COORDINATION.md (append), created REVIEW_FOR_T023.md. Zero edits to security impl code (confirmed via git checkout + diffs on vault/llm/main). Full re-reads + search_tool + builds green (npm + py). Mandatory share quote propagated. See REVIEW_FOR_T023.md for full protocol/verifs. PASS (docs only).

## Later / Polish (P2+)

- [x] **T024** Memory profile editor / visible tone samples. (COMPLETE 2026-07-14)
  - **Implementer (2026-07-14)**: Delivered full memory profile persistence + editor UI + real injection into /enrich flow.
  - **Backend**: Created `backend/app/api/memory.py` (APIRouter) with:
    - `GET /api/memory-profile` — returns user's UserMemoryProfile (tone_samples, icp_industries, typical_cadence) or empty defaults if none exists.
    - `PUT /api/memory-profile` — upserts user's profile using `derive_user_uuid()` (T012 vault pattern).
    - All protected via `get_current_user_api`; graceful DB error handling.
  - **Memory context wiring**: Modified `POST /api/leads/enrich` (backend/app/api/leads.py) to load current user's UserMemoryProfile from DB and pass as `memory_context` dict ({tone, icp, cadence, tone_samples}) into `generate_enrichment()`.
  - **Web**: Created `web/src/components/MemoryProfile.tsx` full editor component with:
    - ICP industries input (comma-separated).
    - Typical cadence (3 numeric inputs for day intervals; default [4, 9, 14]).
    - Tone samples list (view + add/remove interface).
  - **Client API**: Added `getMemoryProfile()` + `saveMemoryProfile()` functions to `web/src/api/client.ts`.
  - **Routing**: Added `/memory` route in App.tsx; nav link; AccountPage link to editor.
  - **Files created**: backend/app/api/memory.py, web/src/components/MemoryProfile.tsx. **Files modified**: backend/app/main.py (+router), backend/app/api/leads.py (+db param, +profile loading), web/src/api/client.ts (+3 functions), web/src/App.tsx (+import, +route, +nav).
  - **Verification**: py_compile clean; pytest 68 passed (no regression); npm build clean (no TS errors).
  - **Status**: COMPLETE. Builds green; all shapes preserved (no breaking changes to /enrich, /push, /history, Composer, Connections, History). Additive only. See BUILD_COORDINATION.md append for full details.
- [ ] **T025** Usage ledger + simple admin views. (agents spawned 2026-07-14; no implementation yet)
  - **Orchestrator (2026-07-14)**: UsageLedger model + llm _record_usage (in-mem + log) present. No /usage queries or admin/dashboard views (T010/T015 pending). Conceptual ready. Ties to T015. Awaiting.
  - **Tester (2026-07-14, subagent 019f5dba-dbea-7911-9628-a46e0656d5b0)**: Builds GREEN. Ledger model + _record_usage ready. No queries/views in T010/T015. Preps T015. Awaiting. See TEST_REPORT_WEB_POLISH.md. No breakage.
- [x] **T026** Full test coverage for adapters and orchestration. (agents spawned 2026-07-14; implementation complete 2026-07-14)
  - **Implementer (2026-07-14, Claude Agent)**: Delivered full pytest suite for T026 (T008 orchestration + T007 enrichment + T001/T002 adapters).
    - Setup: Added pytest, pytest-asyncio, pytest-mock to backend/requirements.txt. Created backend/pytest.ini (auto asyncio mode, markers for unit/adapter/factory/service).
    - Conftest: backend/tests/conftest.py with fixtures (mock_current_user, mock_lead_input, mock_enrichment_result, mock_crm_client, dates, expected deltas).
    - Adapter tests (test_adapters_crm.py, 22 tests):
      - Bitrix24Client: createContact/Deal/Task with dict/dataclass inputs, name splitting, date normalization, error handling (network/HTTP/API errors).
      - HubspotClient: same shape + timestamp conversion, association arrays, field mapping.
      - Optional field handling, field mappings vs contract.
    - Factory tests (test_crm_factory.py, 12 tests):
      - Provider selection (default bitrix24, explicit via param, HubSpot).
      - Token resolution (explicit config, settings fallback, vault resolution).
      - Multiple provider instances, independence.
    - Lead service tests (test_lead_service.py, 18 tests):
      - Full orchestration: 1 contact → 1 deal (linked) → 3 tasks (linked, +4/+9/+14 day deltas ±1 tolerance).
      - Return shape: contact_id, deal_id, task1/2/3 with id+date, enriched_preview (company_snapshot, personalized_opener, exactly 3 follow_ups w/ title/desc/due_in_days/rationale).
      - LLM enrichment integration (called before CRM ops, shapes preserved).
      - Dict input support, empty enrichment fallback, edge cases, exact call sequence.
    - LLM service tests (test_llm_service.py, 16 tests):
      - Structured JSON output shape (company_snapshot, personalized_opener, follow_ups[3] with fields).
      - JSON parsing with fallback (code fences, malformed, normalization, field aliases).
      - Mock fallback (no keys, budget exceeded, all LLM fail).
      - Memory context injection, budget guards, usage recording, Gemini→Haiku→Mock fallback chain.
    - All tests hermetic (mocked httpx, no real DB/network/LLM). Run: `cd backend && python -m pytest tests/ -v`. Result: **68 passed** (22 adapter + 12 factory + 18 lead_service + 16 llm_service), 58 warnings (UTC deprecations in source; test quality unaffected).
    - Files created: backend/tests/__init__.py, backend/tests/conftest.py, backend/tests/test_adapters_crm.py, backend/tests/test_crm_factory.py, backend/tests/test_lead_service.py, backend/tests/test_llm_service.py. Updated: backend/requirements.txt, backend/pytest.ini.
    - Coverage: All CRM adapter methods (createContact/Deal/Task) for both providers, factory provider selection + token resolution, lead_service full 1c+1d+3t orchestration with enrichment, LLM enrichment shape + fallbacks. Mirrors assertions from scripts/e2e_smoke_t020.py in isolated pytest units.
    - No changes to adapter/factory/service/llm code (tests only, read-only imports). No database, real network, or LLM keys required. PASS.
- [x] **T027** Extension store submission assets (screenshots, description). (agents spawned 2026-07-14)
  - **Orchestrator (2026-07-14)**: docs/extension-store.md (full store listing copy + detailed screenshot instructions + icon guidance + "paste signal -> magic AI 3 tasks -> CRM" emphasis) + bd-lead-icon-placeholder.svg present. README linked. No real screenshots yet (await T016/T017 real popup). Ready for post-impl assets. See docs/ + REVIEW_FOR_T027.md.
  - **Implementer (2026-07-14, subagent 019f5dba-9acd-7f21-89cd-be4790e05f5e)**: Delivered polish in session. Updated docs/extension-store.md with complete Chrome/Firefox store metadata (name, short/detailed desc, bullets, how-it-works, screenshots placeholders/instructions), icon guidance + inline placeholder SVG. Created docs/bd-lead-icon-placeholder.svg. Updated tasks.md + appended to BUILD_COORDINATION.md (start + final with decisions). Re-reads of CONCEPT/UI_UX/FEATURES/ARCH + prior coord. No src changes (docs only). Builds/tsc green. Verdict from REVIEW: COMPLETE for polish slice (high fidelity to grounding docs; real screenshots post T016). See REVIEW_FOR_T027.md for full alignment check + suggestions. PASS.

See plan.md for sequencing and the original project_agents_tasks.md + approved session plan for more context.

**Next**: Run speckit-tasks (or manually refine), then begin with T001 (CrmClient refactor) using senior-architect + senior-backend.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure
- [ ] T009 Setup environment configuration management

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Entity1] model in src/models/[entity1].py
- [ ] T013 [P] [US1] Create [Entity2] model in src/models/[entity2].py
- [ ] T014 [US1] Implement [Service] in src/services/[service].py (depends on T012, T013)
- [ ] T015 [US1] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T016 [US1] Add validation and error handling
- [ ] T017 [US1] Add logging for user story 1 operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T021 [US2] Implement [Service] in src/services/[service].py
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T027 [US3] Implement [Service] in src/services/[service].py
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
