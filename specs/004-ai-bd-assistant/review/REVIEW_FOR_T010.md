# REVIEW_FOR_T010.md: Basic REST API for enrich + push + history

**Reviewer**: Scrutinizer Agent (T010)
**Date**: 2026-07-14
**Impl worktree inspected**: /home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5db8-f5bf-7f92-9494-b255207f311c (pre-delivery snapshot; no T010-specific appends or new code in api/ or history)
**Baseline reviewed**: main workspace backend/app/ (current state after T007/T008/T009)
**Mandatory reads completed** (before review + edits):
- BUILD_COORDINATION.md (full + greps + recent T009 prep for T010)
- specs/004-ai-bd-assistant/{plan.md, spec.md, tasks.md, data-model.md}
- docs/{ARCHITECTURE.md, UI_UX.md, FEATURES.md, CONCEPT.md}
- backend: main.py (full), services/lead_service.py, llm_service.py, token_vault.py, models/lead.py + outreach_history.py + user.py + database.py + api/__init__.py, config.py
- src/tool.ts + web/src/api/client.ts + components (for shape expectations)
- Prior REVIEW_FOR_T00x.md (esp T009, T007, T008, T006, T005)

**Protocol followed**: Re-read coord immediately before edits; appended start + full log to BUILD; updated tasks.md; no source edits (only this REVIEW + .md); used run_terminal for verifs (git worktree, ls, py_compile, grep routes); search first for MCP if used (not needed).

## Summary Verdict: **INCOMPLETE / PARTIAL PASS**

- **Enrich + Push**: Strong match to spec/plan/ARCH/UI expectations. Correct auth (Depends(get_current_user)), vault (resolve_token(current_user)), lead_service + llm (enrich pre-Crm), pydantic models, error handling, protected routes. Endpoint shapes exact for downstream (enriched_preview etc).
- **History**: Not implemented (0 endpoints, 0 queries against Lead/OutreachHistory). Blocks T014 + full US3.
- **Structure/Completeness**: Routes still inline in main.py (plan calls for api/ (auth,leads,...)); no DB persistence of leads/usage/history on calls (T009 models ready per review but T010 scope includes wiring per coord notes). 
- **No breakage**: 100% (CrmClient, adapters, T005-9, TS src, web stubs, MCP all intact and exercised by /push).
- **Quality**: Good (comments, logging, additive fields); minor issues noted below.
- **Recommendation**: FAIL to mark [x] until history + persist + router extraction complete. Use patches below. After fixes + Tester green, sync + update T010.

**Key shared interface info** (for T012-15 web, T017 ext, T020 tests):
- POST /api/leads/enrich (no ?provider/token needed): 
  Body: {company_name, deal_name, contact_name, contact_role, signal?, signal_type?, pain_point?, email_subject?, notes?}
  Returns: {company_snapshot, personalized_opener, follow_ups: [{title,description,due_in_days,rationale}, ...3], model_used, memory_note, authenticated_as, provider_default}
  (T013 "Generate with AI" can POST this; preview pane renders snapshot/opener/follow_ups + rationale.)
- POST /api/leads/push?provider=bitrix24|hubspot&token=... (token override; auth Bearer separate):
  Same body.
  Returns: {contact_id, deal_id, task1:{id,date}, task2.., task3.., enriched_preview: {company_snapshot, personalized_opener, follow_ups, model_used, memory_note}, provider, authenticated_as, note: "..."}
  (Matches BdLeadResult in src/tool.ts + web expectations + T007 enriched; push works today for demo.)
- History (when implemented per data-model): GET /api/leads/history (current_user filter) -> list[ {id, company_name, contact_name, enriched, crm_*, created_at, ...} ]; GET /api/leads/{lead_id}. "use similar" loads the input fields from prior lead.
- Gotchas for downstream: Use /api prefix (health + current web client.ts); current_user["id"] is UUID str for FKs; no real persist yet (leads will appear in /history only after T010 persist); DEBUG allows headerless for now.
- T017 ext / T012: can use current /push with ?provider&token + JWT header later.
- T020: can smoke /push (exercises full 1c+1d+3t via service); enrich separate.

## Detailed Findings

### 1. Auth / Vault / Services Integration (PASS)
- push_lead: current_user: dict = Depends(get_current_user), effective_token = resolve_token(current_user, provider, override=token), core_result = await create_lead_with_followups(lead, provider, effective_token, current_user)
- enrich_lead: current_user only (no token), await generate_enrichment(..., current_user=...)
- Matches T005 (get_current_user returns id/email/display_name stub + JWT placeholder), T006 vault (current_user drives), T007 llm (memory injection), T008 orchestration exact.
- Preserves CrmClient factory usage inside service (no direct adapter).
- Protected: 401 on bad/no token (except DEBUG fallback).

### 2. Endpoint Shapes + Spec Match (PASS for enrich/push)
- LeadPushInput Pydantic: matches core of BdLeadSchema/tool.ts + data-model (company/contact/signal etc).
- enrich: returns enriched + extras (per FR-003, plan "returns enriched_preview", ARCH internal /api/enrich shape).
- push: ids + enriched_preview (per plan, UI_UX push result toast + preview).
- Paths: /api/leads/* (consistent in practice; plan omitted /api but web expects it).
- Error: 400 token, 502 crm/llm, 401 auth. Good.

### 3. History Endpoints + Models (FAIL / MISSING)
- No @app.get("/api/leads/history"), no query code.
- Models ready: Lead (with enriched JSON, user_id index), OutreachHistory (lead_id/user_id, action/outcome, embedding), relationships + indexes per data-model.
- T009 reviewer explicitly called out: "Prepares T010: ... ready for CRUD in API", "T010 use models (persist Lead+ledger, query...)"
- Per spec FR-009 "view basic history of their leads", US3 "browse past leads... list + detail", UI_UX /history table + "use similar".
- data-model: leads + outreach_history for queries.
- Also missing: persist on push (T010 scope).

### 4. Router / Modularity (Minor)
- main.py has inline routes + comment: "# Router placeholders ... from app.api import leads"
- Plan structure: backend/app/api/ (leads etc) + include.
- Current api/ only __init__.py stub. Should extract for cleanliness (no functional break).

### 5. Persistence (MISSING)
- lead_service: pure Crm + llm, no db param or Lead( ) insert.
- No usage_ledger insert (T007 budgets log to stdout only).
- On push/enrich: should create Lead(user_id=..., enriched=..., crm_*=...) + ledger entry (from T007 result).
- get_db ready in main (Depends in startup).

### 6. Other Quality / Edge
- Good: logging with user, DEBUG notes, additive enriched_preview (no break to old callers).
- Minor: LeadPushInput in main.py (could move to api or schemas); no pagination on future history; no auth on hypothetical history yet.
- No tests added (T020 later).
- Exact Crm flow untouched (1+1+3 calls, dates +4/9/14, string ids, both provs).

### 7. Verifs Performed (own)
- py_compile (3.12): all key files GREEN (main, lead/llm/vault services, lead/outreach models).
- Route/openapi static: enrich+push present, history absent.
- Shape sims (from code): match plan + web stubs + src/tool.ts.
- Wt inspection: no delta for T010 (use main as baseline).
- Grep: auth/vault/llm/lead_service calls correct; no CrmClient breakage.
- (Full runtime uvicorn bg + live calls skipped due to missing runtime deps in shell; compile+parse sufficient + prior T007/T008 integ verified.)

## Concrete Patch Suggestions (search_replace format; for Implementer post this review)

**Patch 1: Extract routes to api/leads.py (modularity per plan)**
```
# file_path: backend/app/api/leads.py (NEW FILE - allowed per T010 scope)
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Any
from app.main import LeadPushInput, get_current_user  # or move model here
from app.services.lead_service import create_lead_with_followups
from app.services.llm_service import generate_enrichment
from app.services.token_vault import resolve_token
from app.config import settings
from app.database import get_db
# ... (move push_lead, enrich_lead logic here; add history)

router = APIRouter(prefix="/api/leads", tags=["leads"])

@router.post("/enrich")
async def enrich_lead(...): ...

@router.post("/push")
async def push_lead(...): ...

@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user), limit: int = 20, db=Depends(get_db)):
    # query Lead where user_id == current_user["id"] order by created_at desc
    ...
```

Then in main.py:
```
from app.api.leads import router as leads_router
app.include_router(leads_router)
# remove inline defs
```

**Patch 2: Add persist + history queries (core T010 missing)**
In lead_service.py (add db: AsyncSession | None = None param):
```
# after core_result or in push/enrich
if db:
    lead = Lead(
        user_id=uuid.UUID(current_user["id"]),
        company_name=..., 
        ...,
        enriched= enriched or core_result.get("enriched_preview"),
        crm_provider=provider,
        crm_contact_id=core_result.get("contact_id"),
        crm_deal_id=core_result.get("deal_id"),
    )
    db.add(lead)
    await db.commit()
    # also UsageLedger from T007 _record_usage data
```

Add in main or api/leads:
```
from app.models.lead import Lead
from app.models.outreach_history import OutreachHistory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/api/leads/history")
async def list_history(current_user: dict = Depends(get_current_user), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    user_id = current_user["id"]
    stmt = select(Lead).where(Lead.user_id == user_id).order_by(Lead.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    leads = res.scalars().all()
    return [{"id": str(l.id), "company_name": l.company_name, "enriched": l.enriched, "crm_contact_id": l.crm_contact_id, ...} for l in leads]
```

Similar for detail + on push record a OutreachHistory(action="pushed", ...).

**Patch 3: Minor in main (if not extracted)**
Ensure /api/leads/history etc documented + auth.

See T009 REVIEW for model usage examples.

## Blockers / Opens for others
- Sandbox tokens still needed for real /push verif (T020).
- Real JWT (vs stub) for prod history queries (T005).
- Vector queries for memory in enrich (T009 + T007 hook).
- Web T013: update api/client.ts to call /enrich (not just push); T014 implement history UI + "use similar" from returned list.
- T017: extension uses same /enrich + /push.
- After: update openapi consumers, add basic pytest for routes (T020).

**All criteria from user query + specs checked**. Preserve intact: CrmClient/auth/llm/vault/lead_service.

**Ready for**: Implementer to apply + deliver in wt (update its coord + tasks), re-review, Tester (py + route sim + shape match + no-break Crm), sync to main.

**Final note**: T010 partial today enables demo push; full required for memory/history value prop + web pages. Re-read this + coord + specs before touching code.

## Additional Verifs + Findings (Reviewer follow-up 2026-07-14)
**Re-reads**: FULL BUILD_COORDINATION + specs (plan/tasks/data-model/spec/contracts) + ARCH/UI_UX + lead_service/main/models/adapters + web client + src/tool.ts + T010/T020 wts.
**Verifs run (run_terminal)**:
- py_compile backend/app/{main.py,services/lead_service.py,llm_service.py,adapters/crm/*,models/lead.py,database.py}: GREEN.
- Service smoke (mocked generate_enrichment + create_crm_client): both providers produce EXACT {contact_id, deal_id, task1/2/3:{id,date}, enriched_preview} + call seq + links + dates; PASS.
- API fn smoke (mocked deps): /enrich calls llm, /push resolves token + delegates lead_service + returns shape + provider/auth: PASS.
- Route list: GET /api/health, POST /api/leads/enrich, POST /api/leads/push. NO /history.
- T020 e2e_smoke script (from its wt): py_compile OK; exec --mock-force (bitrix): asserts PASS, prints exact smoke shape, records 1c+1d+3t linking, enriched, dates.
- Worktree: T010 wt (f5bf...) = pre-snapshot, no new history/routes delivered. T020 wt delivered scripts/e2e_smoke_t020.py (uses T010 paths + direct service).
- TS/web: npm run build + tsc clean; client.ts matches (enrichLead, pushLead expect ids+enriched additively); no TS breakage.
- docker compose config: valid.
**T010 + T020 cross alignment**: Confirmed. lead_service + CrmClient (factory only) 100% match to contracts + data-model (enriched JSON ready). API delegates exactly. T020 script designed to smoke T010 paths + core shapes. History + persist still missing per prior section (blocks full T014/US3).
**Exact shapes for smoke (shared)**: push returns contact_id, deal_id, task1/2/3 + enriched_preview (see full in new REVIEW_FOR_T020.md). Matches lead_service, web, tool.ts, spec US1.
**T010 status**: Enrich+push live/aligned (partial from T007+); history/persist/router extract pending.
**T020 status**: Script solid (PASS); needs main sync + live sandbox run + TEST_REPORT.
**No breaks**: Everything prior (Crm, T005-9, web, MCP) preserved.
**Updates**: Appended here + created REVIEW_FOR_T020.md + BUILD_COORDINATION + tasks.md note.

**Timestamp**: 2026-07-14. Additional verifs + cross review complete. Re-reads mandatory followed.
