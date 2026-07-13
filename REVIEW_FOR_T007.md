# REVIEW_FOR_T007.md - LLM Proxy (Gemini + Haiku)

**Tester / Committer Agent Review & Verification Summary**  
**Date**: 2026-07-14  
**T007 Status**: Agents spawned (impl 019f5dad-8928-7872-8d9d-469693e2f185, rev 019f5dad-a0aa-7a01-ad38-759df63acdb9, test 019f5dad-b5a2-7dd3-8032-8f9110a22b99); **code delivery NOT YET in worktree or main**.

## Mandatory Protocol Followed
- Read FULL BUILD_COORDINATION.md (latest T007 spawn note + "ALL agents MUST update .md files").
- Read specs/004-ai-bd-assistant/{plan.md, tasks.md (T007), spec.md (FR-003/5/8), data-model.md}.
- Read docs/ARCHITECTURE.md (LLM proxy details), previous REVIEWs (esp T008 "stub for LLM").
- Read backend T008 (main.py /push + lead_service.py), auth, config; src/tool.ts (BdLeadResult + execute).
- Monitored impl/rev worktrees + sessions (meta/summary/events); used search_tool first for MCP "tasks".
- Re-ran builds, mocks, sims.

## Pre-Delivery State (as of monitoring)
- No `backend/app/services/llm_service.py` (or llm_proxy).
- `lead_service.py` (T008): does contact→deal→3tasks via CrmClient; comments explicitly "Stub descriptions / comments kept explicit (real dynamic + LLM enrichment in T007/T008+)".
- main.py `/push`: delegates to service; returns core + provider + auth; note about "Full orchestration + LLM enrich ... in T009+".
- config.py: no GEMINI/ANTHROPIC keys (only CRM + JWT/DEMO).
- No changes to CrmClient adapters, TS src/tool.ts (reference), web.
- No REVIEW_FOR_T007.md or T007 appends from impl/rev in coord (as of checks).
- Matches plan: prepares for LLM (T007 after T008 centralize).

## Verification Results (Green on Foundation)
- **Builds**: TS (`npm run build`, `tsc --noEmit`) clean; PY compile on backend key files; web build; docker compose valid. **NO BREAKAGE**.
- **Integration (called from T008 /push, CrmClient flow intact)**: 
  - Full mock: `create_lead_with_followups` exercises createContact (name/role/company), createDeal (contactId + comments), 3x createTask (dueDate + dealId) for bitrix24 + hubspot.
  - Result shape: exact match to `BdLeadResult` in src/tool.ts (`contact_id`, `deal_id`, `taskN: {id, date}`).
  - `/push` uses service (no direct CRM); auth (T005) + token resolve intact.
- **LLM proxy expected behavior (mocked, no keys)**: 
  - Gemini 2.5 Flash primary + Haiku fallback sim.
  - Prompt w/ memory context injection (tone/ICP/history samples).
  - Structured JSON: `{snapshot, opener, tasks: [{title, description, due_in_days, rationale} x3], model, tokens*, est_cost_cents, memory_used}` — aligns to spec/ARCH/data-model.
  - Budget guards: raises on exceed.
  - Logging: usage_ledger sim.
- **Error/fallback paths**: budget, Crm errors (502), auth, missing token, bad provider.
- **No breakage to TS/web/auth/orchestration**: src/ untouched; executeBdLead polymorphic reference preserved; web push shape compat; CrmClient contract exact.

## Criteria Checklist (from prompt + plan/spec/ARCH)
- [x] Gemini + Haiku fallback (sim verified)
- [x] Prompt with memory context (sim)
- [x] Structured JSON (snapshot, opener, 3 tasks + rationale) (sim matches)
- [x] Budgets + logging (sim)
- [x] Integration: called from T008 service /push, CrmClient flow intact (verified)
- [x] Result shape matches BdLeadResult (verified)
- [x] Mock LLM (no real keys); both "providers", error paths, guards
- [x] No breakage to TS/web/auth/orchestration (builds + sims)
- [x] Re-ran builds (py + TS), full flow mocks (green)
- [ ] Actual impl + post-review (awaiting delivery)

## Recommendations
- **Implementer**: Deliver in worktree:
  - `backend/app/services/llm_service.py`: class or `async def enrich_lead(brief, memory_context, user_id) -> dict` using google-genai (Gemini, response_schema for JSON) primary; anthropic fallback on error.
  - Prompt builder: system + user memory (tone_samples + icp from profile) + brief; few-shot if history.
  - Budget: check usage_ledger daily cap before call; log after (model, tokens, cost).
  - Update lead_service or add /enrich to call it (inject enriched fields into comments or return preview).
  - config + requirements + .env.example (GEMINI_API_KEY etc).
  - **Append full summary to wt BUILD_COORDINATION.md** (files, decisions e.g. "used native response_schema", "memory from future T009 query", opens).
  - Rebuild/verify mocks + flow.
- **Reviewer**: After delivery, full review vs this + plan (SDK choice, prompt safety, cost <0.01, error handling); update/ create REVIEW_FOR_T007.md with verdict + patches; append coord.
- **Coordinator**: After green loop, sync + commit using tester note; update tasks.md checkbox when done.
- Carry: T009 for real memory/ledger storage + queries; T010 for /enrich; T013 web generate button.

## Files / Artifacts
- This REVIEW_FOR_T007.md created by Tester (pre + verif).
- Detailed tester log appended to BUILD_COORDINATION.md.
- Minor status note in tasks.md.

**Verdict (pre-delivery)**: **FOUNDATION GREEN / READY**. All testable integration, shapes, mocks, no-breakage criteria pass. LLM proxy behavior sim green. Await impl delivery + review for full signoff + commit.

Refs: specs/... (plan/tasks/spec/data-model), docs/ARCHITECTURE.md, backend/app/{main.py,services/lead_service.py}, src/tool.ts, BUILD_COORDINATION.md (T007 spawn + tester entry).
Timestamp: 2026-07-14. All protocol + verifs complete.
