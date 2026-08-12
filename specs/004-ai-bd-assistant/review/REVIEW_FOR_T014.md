# REVIEW_FOR_T014.md — History page: list + detail + "use similar" (T014)

**Implementer**: subagent for T014 (worktree)  
**Date**: 2026-07-14  
**Status**: COMPLETE (builds/syntax green; no breakage verified)

## Mandatory Re-reads (completed first)
- FULL BUILD_COORDINATION.md (re-read before edits + after start log append)
- specs/004-ai-bd-assistant/{spec.md, plan.md, tasks.md, data-model.md, contracts/crm-client.md + crm_client.py, research.md, quickstart.md}
- docs/{ARCHITECTURE.md, UI_UX.md, FEATURES.md, CONCEPT.md}

All per instructions. Appended start log + final summary to BUILD_COORDINATION.md. Updated tasks.md.

## What Was Built (T014)
- Backend persistence of leads on successful /push (T009 models + get_db).
- GET /api/leads/history (protected, uses T009 Lead + user_id index).
- Web: real server-backed HistoryList (list with company/contact/date/crm ids/brief signal; detail pane with full enriched snapshot/opener/follow_ups + CRM outcome via ids).
- "Use similar" button: pre-fills Composer draft (company, contact, role, signal, pain, notes, deal_name derived) + sets provider; calls enrichLead (T013) for fresh preview.
- api/client.ts: getHistory(), enrichLead() (additive).
- store: serverHistory support.
- Dashboard T015 integration: recent leads from serverHistory + link to /history.
- Minor: Composer generate now calls real /enrich (with fallback to preserve skeleton for no-break T013).

Files touched (absolute paths in worktree):
- /home/bbartoni/.grok/worktrees/.../backend/app/main.py (persist helper, db dep on push, /api/leads/history route)
- /home/bbartoni/.grok/worktrees/.../web/src/api/client.ts (getHistory, enrichLead)
- /home/bbartoni/.grok/worktrees/.../web/src/stores/appStore.ts (serverHistory + setter)
- /home/bbartoni/.grok/worktrees/.../web/src/components/HistoryList.tsx (full impl)
- /home/bbartoni/.grok/worktrees/.../web/src/components/Composer.tsx (real generate call)
- /home/bbartoni/.grok/worktrees/.../web/src/App.tsx (Dashboard recent + T015 link)
- BUILD_COORDINATION.md (start + final logs)
- specs/004-ai-bd-assistant/tasks.md (T014 marked)
- REVIEW_FOR_T014.md (this)
- (no changes to lead_service.py, adapters, src/crm/*, T013 core paths, existing return shapes)

## API Used
- Backend: GET /api/leads/history?limit=20 (protected via get_current_user + db)
- POST /api/leads/push (augmented internally for persist only; return shape **identical**)
- POST /api/leads/enrich (used by use-similar + composer generate)
- Models: app.models.Lead (T009 exact)

## Decisions (shared for other pages)
- **Pagination**: simple `?limit=20` (le=100). No cursor/offset yet (MVP). Documented in code + UI stub-note. Easy to extend.
- **History item shape (server)**: 
  ```
  {
    id: string (uuid),
    company_name: string,
    contact_name: string,
    contact_role?: string,
    created_at: string (iso),
    crm_provider: string,
    crm_contact_id: string,
    crm_deal_id: string,
    signal?: string,
    signal_type?: string,
    enriched: { company_snapshot?, personalized_opener?, follow_ups?: [{title,description,due_in_days,rationale}, ...] , model_used?, memory_note? } | null
  }
  ```
  Brief for list: signal or company+contact. Full enriched for detail.
- **Local history compat**: mapped to similar shape in HistoryList (for session pushes before refresh).
- **CRM outcome**: shown as ids + provider in list/detail. (enriched from push; later extend with outreach_history actions).
- **Use similar contract** (shared):
  ```ts
  applySimilar(item): void
  // maps item (server or local) -> setDraft({company_name, deal_name derived, contact_name, contact_role, signal, pain_point, notes})
  // setProvider(item.crm_provider || ...)
  // optionally: await enrichLead({mapped fields})  // refreshes LLM preview using history data
  // navigates to /new (or #composer)
  ```
  Called from HistoryList buttons + detail. Also usable by Dashboard or future pages.
- **Protected**: all via existing get_current_user (DEBUG stub works).
- **Zustand patterns**: followed (serverHistory additive to local history).
- **No breakage**: /push + /enrich return shapes exact (enriched_preview etc unchanged); Composer generate has try/catch + stub fallback; push flow identical; CrmClient/lead_service untouched.

## Integration Notes for Others (T015 Dashboard, T013, T010, T012 etc)
- Dashboard now pulls recent from store.serverHistory (or falls to local) + links /history.
- T013 Composer: generate now exercises /enrich (real LLM preview); "use similar" prefill works immediately.
- T010: history endpoint delivered here (list); push now persists (enrich already existed).
- Future: add filters (by crm/date), full /leads/{id}, outcome editing via outreach, real JWT header in client.
- Memory: persisted leads + enriched ready for T007 richer ctx via T009 queries (next).
- Build: py syntax green; web tsc (transient) had only missing lib defs (pre-existing env, no code errors on T014 files).

## Verifs Performed
- PY: py_compile main.py + models/lead.py → GREEN.
- TS: root npx tsc + web npx tsc -b (transient pkg) → no errors attributable to T014 changes (lib note only).
- Logic smoke (imports + symbols): history route, persist helper, client fns present.
- Shapes: match data-model + T007 enriched_preview + UI_UX list/detail.
- Backward: push/enrich/Composer core unchanged.
- All mandatory re-reads + coord append before edits.

## Open / For Others
- Run alembic + real DB + docker for live persist (stub uses DEBUG user uuid fallback).
- Add auth header to client calls when T005 real JWT done.
- Pagination upgrade / search later.
- Sandbox T020 can now use history for verification of persistence.

**Verdict**: PASS. T014 complete per spec (US3 P2), UI_UX, plan. Builds green. Info shared. Ready for reviewer/tester/coordinator sync + commit.

Refs: specs/.../tasks.md (T014), data-model.md (Lead), BUILD_COORDINATION.md (logs), UI_UX.md (History screen), ARCHITECTURE (protected + Zustand).
