# REVIEW_FOR_T020.md: End-to-end smoke tests / scripts (Bitrix24 + HubSpot sandboxes)

**Reviewer**: Scrutinizer Agent (T020 + cross T010)
**Date**: 2026-07-14
**Impl worktree inspected**: /home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5db9-8e76-7e20-84a6-0ed77bd2fab0 (T020 script delivered)
**Baseline**: main (no scripts/ or e2e yet); T010 API state in backend/app/main.py + lead_service
**Mandatory re-reads completed FIRST** (repeated via read_file + grep + run_terminal):
- FULL BUILD_COORDINATION.md (T001-T009 complete notes, spawn for T010/T020, "exact shapes" shared, re-read rule, prior T009 prep for T010)
- specs/004-ai-bd-assistant/{plan.md, tasks.md (T010/T020), spec.md (US1 P1, FR-004/009), data-model.md}
- docs/{ARCHITECTURE.md, FEATURES.md, UI_UX.md, CONCEPT.md}
- backend/app/{main.py (routes), services/lead_service.py (create_lead_with_followups + shape), llm_service.py, adapters/crm/* (factory + CrmClient), models/lead.py + outreach_history.py + database.py}
- src/tool.ts (BdLeadResult / execute shape ref), web/src/api/client.ts (PushResult + EnrichedPreview)
- T010 worktree + T020 wt (script + BUILD copies), prior REVIEWs (esp T009 T008 T007 T010)
- Used search_tool first for "tasks" MCP (schema ok; not used further).

**Protocol**: Re-read BUILD+specs before any action/append. No source edits (reviewer). Ran verifs via run_terminal (py_compile, script exec mock, service smoke, route grep, worktree ls). Created this REVIEW + appended to BUILD_COORDINATION + tasks notes. Share "exact shapes".

## Summary Verdict: **PASS (script) + T010 API PARTIAL ALIGNMENT**

- **T020 script**: Delivered + high quality. Exercises exact lead_service + CrmClient (direct path) + optional backend T010 paths (/enrich + /push). Mocks always, real creds create records (intended). Asserts 1 contact + 1 deal + 3 tasks, +4/+9/+14 dates, enriched_preview, call sequence + linking. Syntax + run (mock) green. Aligns 100% to lead_service/CrmClient/data-model + T010 API.
- **T010 API**: Enrich + push present and aligned (see REVIEW_FOR_T010.md + below). History endpoint + persistence MISSING (T010 still partial per prior review). No breakage.
- **Cross alignment**: Script + API + service use shared shapes; CrmClient only via factory; data-model Lead.enriched + ids ready (persist pending in T010).
- **No breakage**: TS/web/MCP/Crm/auth/llm/vault/lead_service 100% intact (mocks exercise full 1c+1d+3t + enriched).
- **Recommendations**: Sync script/ to main (add scripts/ dir); fix utcnow deprecation; add TEST_REPORT_T020.md after live sandbox run; implement missing history/persist for T010; run with real sandbox creds (T020 purpose). Mark T010 [x] after history; T020 [x] after sync + report.

**Key shared "exact shapes for smoke: push returns contact_id, deal_id, task1/2/3 + enriched_preview"** (for T010/T020/T013/T014/T017):
- From lead_service.create_lead_with_followups + /push:
  ```
  {
    "contact_id": "<string from CrmClient>",
    "deal_id": "<string>",
    "task1": {"id": "<string>", "date": "YYYY-MM-DD"},  # +4 days
    "task2": {"id": "<string>", "date": "YYYY-MM-DD"},  # +9
    "task3": {"id": "<string>", "date": "YYYY-MM-DD"},  # +14
    "enriched_preview": {
      "company_snapshot": "...",
      "personalized_opener": "...",
      "follow_ups": [ {"title": "...", "description": "...", "due_in_days": 4, "rationale": "..."}, ... x3 ],
      "model_used": "gemini-2.5-flash" | "mock" | ...,
      "memory_note": "..."
    },
    "provider": "bitrix24" | "hubspot",
    "authenticated_as": "..."
  }
  ```
- Matches: src/tool.ts BdLeadResult (ids + tasks), web PushResult (additive), T007/ARCH/FR-003/004, data-model leads.enriched JSON, T020 asserts.
- /enrich returns the inner enriched_preview shape (no ids).
- Used in T020 direct + backend paths; web composer preview + history "use similar".

## Detailed Findings (T020 script review + T010 cross)

### 1. Script Structure + Coverage (PASS)
- Direct path: calls create_lead_with_followups (exercises T007 enrich + T008 orchestration + create_crm_client factory + adapters).
- Backend path: httpx to /api/health + /api/leads/enrich + /api/leads/push?provider&token (T010).
- Mocks: force_mock records calls, asserts seq ["createContact","createDeal","createTask"*3], linking (contactId, dealId), dates deltas.
- Real: passes token to service/adapters (will hit sandbox APIs).
- Contract: also calls create_crm_client + isinstance checks (CrmClient protocol parity).
- Args: --provider, --mock-force, --use-backend, BACKEND_URL env.
- Docs: usage, env, warnings for live creates. Good.

### 2. Alignment with lead_service / CrmClient (EXACT)
- Verif run (mock): produced {contact_id,deal_id,task1/2/3 + enriched_preview}; 5 calls + links asserted; dates ~+4/9/14.
- Service code: exactly 1 createContact({name,role,company}), 1 createDeal({title,contactId,comments w/ snapshot+opener}), 3 createTask({title/desc from follow_ups, dueDate, dealId}).
- Both providers exercised (script + my service smoke).
- Crm adapters untouched; factory used; string ids; YYYY-MM-DD dueDates.
- Matches contracts/crm-client.md + python types + TS src/crm.

### 3. Alignment with data-model + T010 API (GOOD + GAPS)
- enriched_preview shape matches leads.enriched JSON in model.
- T010 routes: /enrich + /push present, delegate exactly, return shape match (my smoke + script backend path).
- Missing for full T010: GET history (query Lead by user_id + enriched), persist of Lead + ledger on push/enrich (get_db + current_user["id"] ready from T009).
- T020 script notes T010 paths explicitly; can drive full e2e once history added.
- web client.ts + Composer: calls match (enrich for preview, push for result); local history stub until T014 + T010 history.

### 4. Verifs Performed (this review)
- py_compile on e2e_smoke_t020.py: OK.
- Exec script --mock-force (bitrix24): ALL ASSERTS PASSED; printed exact shape + calls + enriched; dates correct.
- Service smoke (python -c): shapes + both provs + pre-crm enrich: PASS.
- API route inspect: /health + /leads/enrich + /leads/push (history absent).
- Worktree/main: script only in T020 wt; no main sync yet. T010 wt no new API changes (enrich/push from baseline).
- Builds: npm run build (root) + tsc clean (TS no impact); docker compose valid.
- No real net: all via mocks; live requires sandbox + export (documented).
- Cross: CrmClient shapes (TS+py), web PushResult/EnrichedPreview, src/tool.ts ref: all consistent.

### 5. Issues / Polish (non-blocking for script)
- Deprecation: datetime.utcnow() -> datetime.now(timezone.utc). (in _run_direct_smoke)
- Backend path: requires httpx + running server (graceful skip if !HAS_HTTPX).
- No TEST_REPORT_T020.md yet (create after real run).
- Script not present in main/ (additive, sync needed).
- T010 gap: history not wired affects "full" e2e verification per US3; script focuses on push/create (core US1).

## Concrete Recommendations
- Implementer (T020): append full "what built" to wt BUILD_COORDINATION; create TEST_REPORT_T020.md with sample real run output (sanitized ids).
- Coordinator: cp -r scripts/ to main; update .gitignore if needed; commit script.
- T010: complete history endpoint + persist (see patches in REVIEW_FOR_T010.md); then T020 can add history list assert.
- Tester: re-run script w/ real BITRIX/HUBSPOT creds (check portal records match: 1 contact, linked deal, 3 tasks on deal, due dates, AI comments); verify backend path if server up.
- Update tasks.md: note T010 partial (enrich+push live, history pending); T020 script delivered (ready for live + sync).
- Share shape + script usage in BUILD + quickstart.

**All mandatory protocol + cross-task alignment verified**. No breaks to CrmClient/lead_service/data-model/web/MCP. Ready for sync + live T020 sandbox + T010 completion.

**Timestamp**: 2026-07-14. Re-reads + verifs (compile, script run, shape smokes) complete.
