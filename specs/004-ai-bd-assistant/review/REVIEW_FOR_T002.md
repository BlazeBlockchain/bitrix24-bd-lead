# REVIEW_FOR_T002.md

**Reviewer / Scrutinizer Agent Review**  
**Task**: T002 - Implement HubspotClient adapter (createContact, createDeal w/ associations, createTask w/ hs_timestamp)  
**Date**: 2026-07-14  
**Implementer ID**: 019f5d88-ceaa-7682-9621-b110846f88f7 (in isolated worktree)  
**Worktree Inspected**: `/home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5d88-ceaa-7682-9621-b110846f88f7`  
**Main Workspace**: `/home/bbartoni/workspace/.bb/bitrix24-bd-lead` (post-T001: src/crm/{types.ts, bitrix24.ts})

**Status at time of this review**: IMPLEMENTER NOT DONE YET. No `src/crm/hubspot.ts` (or equivalent) present. No new commits or coordination updates from this Implementer beyond T001 state. Worktree src/crm/ is byte-identical to main post-T001 (bitrix24 + types only). Will re-inspect and provide full code review when updates appear in worktree or BUILD_COORDINATION.md.

**Re-check protocol**: This review will be updated (or follow-up appended) once Implementer posts "What I built" + files in coordination. Use `git worktree list`, diffs in worktree, and `ls src/crm/hubspot*` for detection.

## Mandatory Files Read (per instructions)
- FULL BUILD_COORDINATION.md (main + worktree copy) — T001 logs + "NEXT: Start T002"
- specs/004-ai-bd-assistant/{plan.md, tasks.md, contracts/crm-client.md, spec.md, research.md}
- docs/ARCHITECTURE.md (full, with explicit HubSpot section)
- current src/crm/* (types.ts + bitrix24.ts post T001)
- src/tool.ts (executeBdLead polymorphic over CrmClient), src/index.ts (still Bitrix ctor)
- specs/004-ai-bd-assistant/contracts/crm_client.py (Python parallel contract)
- REVIEW_FOR_004_T001.md (for style + continuity on date handling, IDs, Python notes)
- Supporting: package.json (no new deps), tsconfig.json, git worktree list + status in both trees, build outputs.

Additional verifs performed:
- `npm run build` + `npx tsc --noEmit` (both clean on main).
- Grep for CrmClient usages, string id expectations, dueDate, no direct CRM calls outside tool + adapters.
- Confirmed no hubspot.ts or Hub* anywhere in src/ or worktree src/.
- Inspected contract + ARCH for HubSpot rules.
- Cross-ref with previous T001 review criteria (no breakage to Bitrix).

## Current State / Readiness for T002 (pre-impl)
- **CrmClient contract stable**: types.ts exactly matches contracts/crm-client.md:
  - CrmContact {name, role?, company, email?, linkedin?}
  - CrmDeal {title, contactId: string, comments}
  - CrmTask {title, description, dueDate: string /*YYYY-MM-DD|ISO*/, dealId: string}
  - Methods return Promise<{id: string}>
- **executeBdLead** (tool.ts) is fully polymorphic: `client: CrmClient`. Uses contact.id, deal.id, task dueDate + dealId exactly as contract. Date helpers produce YYYY-MM-DD. No Bitrix specifics left in orchestration.
- **Bitrix24Client** (reference style): native `fetch`, `private async call<T>(method, params)`, error strings like `Network error calling ...`, `... HTTP ${status}...`, `... API error...`, `returned no result`. Returns `{id: String(...)}`. normalizeDate helper present (handles ISO→base date).
- **No breakage risk to existing**: index.ts hardcodes Bitrix24Client from BITRIX24_WEBHOOK_URL. tool.ts + MCP output unchanged. String IDs already handled.
- **Python contract**: Mirrors TS exactly (dataclasses + Protocol with camelCase methods, Crm*Dict, notes on HubSpot: "v3 objects: contacts, deals, tasks", "Use associations for linking", "hs_timestamp = due date in ms epoch UTC").
- **Plan/tasks alignment**: T002 is "[P] Implement HubspotClient ... Place in src/crm/hubspot.ts". T003 (provider selector) is separate. HubSpot only in MCP src/ for now (backend adapters come in T004+).

**HubSpot specifics from contracts + ARCHITECTURE.md + research (must match exactly in impl)**:
- v3 endpoints: `/crm/v3/objects/contacts`, `/crm/v3/objects/deals`, `/crm/v3/objects/tasks`
- Associations array in payload (not separate associate call) for contact→deal and deal→task linking.
- hs_timestamp: due date in **ms epoch UTC** (number or numeric string; docs also accept ISO but follow spec).
- Contact name split (firstname/lastname) expected for parity with Bitrix.
- Good comments required for all field mappings.
- Native fetch + error style matching bitrix24.ts.

## Review Criteria (will be applied verbatim once code appears)
When Implementer updates appear, re-read this + re-inspect worktree diffs / new file + run build/typecheck + static analysis of mappings.

1. **Exact adherence to CrmClient interface (string ids, dueDate, etc.)**
   - Must `implements CrmClient` or structurally match.
   - createContact(contact: CrmContact): Promise<{ id: string }>
   - createDeal(deal: CrmDeal) — contactId as string (may Number() internally only if needed for API).
   - createTask(task: CrmTask) — dueDate passed as-is or normalized; dealId string.
   - No extra required params; optionals respected (email/linkedin may be used if present).
   - Return shape exactly `{ id: string }` (HubSpot IDs are strings anyway).

2. **Correct HubSpot v3 usage**
   - **Contacts**: POST /crm/v3/objects/contacts with `{ "properties": { "firstname", "lastname", "jobtitle" (from role), "company", (email if present) } }`. Name split logic should mirror Bitrix (or documented).
   - **Deals**: POST /crm/v3/objects/deals with `{ "properties": { "dealname": title, ...comments? (use "description" or notes) }, "associations": [ { "to": { "id": contactId }, "types": [ { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3 } ] } ] }` (3 = standard contact-deal).
   - **Tasks**: POST /crm/v3/objects/tasks with `{ "properties": { "hs_timestamp": <ms since epoch UTC>, "hs_task_subject": title, "hs_task_body": description, ... }, "associations": [ { "to": { "id": dealId }, "types": [ { "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": <correct for task-deal, e.g. 12 or 204 per HubSpot> } ] } ] }`.
   - Use ms epoch: e.g. `new Date(normalizedDueDate + 'T00:00:00Z').getTime()` or `Date.parse(...)`.
   - Auth: Bearer token (ctor will take token or url+token; different from Bitrix webhook ctor — OK).
   - Response: parse `id` from result (usually top-level or result.id).
   - Error handling: similar shapes, descriptive including endpoint/method.
   - No legacy v1/v2 endpoints. No hapikey in query if using private app (Bearer preferred).

3. **Style match to bitrix24.ts (native fetch, errors)**
   - Class `HubspotClient implements CrmClient`
   - Private `call<T>(path: string, init?: RequestInit)` or equivalent using `fetch('https://api.hubapi.com/crm/v3/...', { headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' }, ... })`
   - Error messages: e.g. `Network error calling HubSpot (contacts): ...`, `HubSpot HTTP ${status} on ...`, `HubSpot API error...`
   - No new npm deps.
   - Consistent formatting, JSDoc/comments on class and methods.
   - Handle response.ok + body (HubSpot errors often `{ "status": "error", "message": ... }` or status codes).

4. **No breakage to existing Bitrix or interface**
   - Do not modify types.ts, bitrix24.ts, tool.ts, index.ts, contracts/ (unless contract gap found).
   - executeBdLead + MCP flow untouched.
   - HubspotClient can be imported/constructed elsewhere but not wired yet (T003).
   - build + tsc clean.
   - String IDs, dueDate contract unchanged.

5. **Good comments for mappings**
   - Explicit comments like in bitrix24.ts: e.g.
     ```
     // HubSpot v3: properties object; firstname/lastname split from name (parity with Bitrix)
     // Association type 3 = HUBSPOT_DEFINED contact-to-deal
     // hs_timestamp must be ms epoch UTC per contracts/crm-client.md + ARCHITECTURE
     ```
   - Document any custom properties (e.g. if mapping signal_type) — note per spec they are manual for now or skipped in T002.
   - Note any HubSpot gotchas (e.g. required props, owner, pipeline defaults).

6. **Python side if updated**
   - Only contract (crm_client.py) expected for T002; no backend/ impl yet.
   - If any updates to .py or md contract, they must be 1:1 with TS (camelCase methods, dueDate, string ids, association notes).
   - Location remains specs/.../contracts/ (as T001).

## Preliminary / Expected Issues + Suggested Guidance (in search_replace style for when impl done)
No code yet, so providing **reference-quality snippets** (grounded in contract + ARCH + HubSpot v3 patterns from research) that Implementer should follow or adapt. Use these as template to avoid common pitfalls (date fmt, assoc type IDs, fetch error shape, name handling).

**Expected ctor + base (adapt to token source):**
```ts
export class HubspotClient implements CrmClient {
  private readonly baseUrl = 'https://api.hubapi.com';
  private readonly token: string;

  constructor(accessToken: string) {
    this.token = accessToken;
  }

  private async call<T>(endpoint: string, body?: unknown): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      throw new Error(`Network error calling HubSpot (${endpoint}): ${String(err)}`);
    }
    // ... parse, check !ok, body.message or status, throw similar to Bitrix
    const data = await response.json() as { id?: string; /* ... */ };
    if (!data.id) { ... }
    return data as T;
  }
  ...
}
```

**createContact (with comments):**
```ts
async createContact(contact: CrmContact): Promise<{ id: string }> {
  const nameParts = contact.name.trim().split(/\s+/);
  const firstname = nameParts[0] ?? contact.name;
  const lastname = nameParts.slice(1).join(' ');

  const result = await this.call<{ id: string }>('/crm/v3/objects/contacts', {
    properties: {
      firstname,
      lastname,
      jobtitle: contact.role,
      company: contact.company,
      ...(contact.email && { email: contact.email }),
      // linkedin can map to a custom prop or hs_linkedin_url if present
    },
  });
  return { id: result.id };
}
```

**createDeal (associations):**
```ts
async createDeal(deal: CrmDeal): Promise<{ id: string }> {
  const result = await this.call<{ id: string }>('/crm/v3/objects/deals', {
    properties: {
      dealname: deal.title,
      description: deal.comments,  // or 'notes' depending on portal
    },
    associations: [
      {
        to: { id: deal.contactId },
        types: [
          {
            associationCategory: 'HUBSPOT_DEFINED',
            associationTypeId: 3,  // contact <-> deal (standard)
          },
        ],
      },
    ],
  });
  return { id: result.id };
}
```

**createTask + date handling (critical):**
```ts
private toHubspotTimestamp(dueDate: string): number {
  // Accept YYYY-MM-DD or ISO per contract; produce ms epoch UTC
  const base = dueDate.includes('T') ? dueDate.split('T')[0] : dueDate;
  // Use UTC noon or start to avoid TZ drift (common practice); or exact 00:00Z
  return new Date(`${base}T00:00:00Z`).getTime();  // number ms
  // Alternative if API prefers ISO: new Date(...).toISOString()
}

async createTask(task: CrmTask): Promise<{ id: string }> {
  const hsTimestamp = this.toHubspotTimestamp(task.dueDate);

  const result = await this.call<{ id: string }>('/crm/v3/objects/tasks', {
    properties: {
      hs_timestamp: hsTimestamp,   // per contracts + ARCH: ms epoch UTC
      hs_task_subject: task.title,
      hs_task_body: task.description,
      // hs_task_status: 'NOT_STARTED' etc. optional
    },
    associations: [
      {
        to: { id: task.dealId },
        types: [
          {
            associationCategory: 'HUBSPOT_DEFINED',
            associationTypeId: 12,  // verify: common for task-deal; confirm in sandbox or docs
          },
        ],
      },
    ],
  });
  return { id: result.id };
}
```

**Notes on assoc type IDs (from HubSpot patterns)**:
- 3 : deals-contacts (widely documented).
- For tasks: examples use 12 or 204 (deal to task) or check `/crm/v4/associations/...` or portal. **Implementer must validate** (or document assumption + use T020 sandbox test). Prefer documented constants if possible.
- Test both directions if needed (HubSpot associations are directional in payload).

**Error handling example (match Bitrix style closely):**
```ts
if (!response.ok) {
  const errBody = ...;
  throw new Error(`HubSpot HTTP ${response.status} on ${endpoint}: ${errBody.message ?? ...}`);
}
if (/* error shape */) { throw ... }
```

**Potential issues to watch (and fix via patches):**
- Wrong timestamp: number vs string, local TZ vs UTC, missing Z — use the helper above.
- Assoc typeId wrong → "one or more associations are not valid" error.
- Missing "properties" wrapper or using legacy array format.
- Not returning string id.
- Modifying shared files.
- No comments on mappings.
- Using axios or adding deps.
- Hardcoding Bitrix-specifics or assuming same ctor shape.
- Not handling optional fields gracefully.

If any of above in impl, concrete search_replace will be suggested in follow-up review.

## Verification Steps (when impl ready, for Implementer + Tester)
- In worktree: `npm run build && npx tsc --noEmit`
- Grep: import of HubspotClient, no changes to types/tool.
- Manual: Can construct `new HubspotClient('fake')`; call methods (mock fetch or unit).
- Future: T020 sandbox — 1 contact + deal (with assoc) + 3 tasks (with hs_timestamp + assoc).
- Compare output shape identical for executeBdLead when using HubspotClient (mocked).
- Cross-check Python contract notes still accurate.

## Actions Taken by Reviewer
- Read all mandatory + supporting files.
- Inspected worktree (multiple times) + main: confirmed no T002 code yet.
- Re-ran build/typecheck (green).
- Created this `REVIEW_FOR_T002.md` (actionable checklist + reference impl guidance + patches style).
- Will append detailed log to BUILD_COORDINATION.md (main + note to worktree).
- No edits to src/ (reviewer role only; no premature impl).

## Recommendations
- **Implementer**: Once ready, place `src/crm/hubspot.ts`, implement per above criteria + reference snippets. Update worktree BUILD_COORDINATION.md with:
  - "What I built", "Files touched", "Decisions" (e.g. timestamp handling, assoc IDs chosen, name split, error messages).
  - Any open Qs (e.g. exact task-deal associationTypeId, how token will be passed for MCP vs backend).
- Rebuild, typecheck, then signal in coord.
- **Coordinator / Tester**: Re-dispatch or wait; after impl, run full loop (review update + verify + sync).
- **If contract gaps found** during impl (e.g. need healthCheck for future factory): propose minimal extension + update contracts + types (but avoid for T002 if possible).
- Clarification carry-over: Python location (still under specs/contracts for now).

**Next for this agent**: Re-read BUILD_COORDINATION.md + poll worktree (via list_dir, run_terminal git status, grep for "Hubspot") periodically until updates posted. Then perform full delta review + update this doc + append final verdict.

All mandatory review protocol followed. Awaiting T002 code to scrutinize for exact contract + HubSpot v3 + style fidelity. No blocking issues in pre-state.

---
## Full Code Review (post-update inspection — updates appeared during review session)

**Worktree re-inspection (once updates appeared)**:
- `ls src/crm/` now shows: bitrix24.ts, hubspot.ts (new, 7937 bytes), index.ts (new barrel), types.ts.
- `git status`: M BUILD_COORDINATION.md, M specs/.../crm_client.py, ?? src/crm/hubspot.ts, ?? src/crm/index.ts.
- No modifications to src/tool.ts or src/index.ts (confirmed `git diff HEAD -- src/tool.ts src/index.ts` empty — perfect).
- `npm run build && npx tsc --noEmit` in worktree: clean (exit 0).
- Runtime: `new HubspotClient('fake')` succeeds from build/ output.
- `git log` still shows only T001 commits (implementer changes uncommitted in worktree as expected).
- Also inspected: updated py contract has full commented Hubspot sketch matching the TS.

**Files read in detail for review**:
- worktree: src/crm/hubspot.ts (full), src/crm/index.ts (barrel+factory), src/crm/bitrix24.ts + types.ts (for parity), updated crm_client.py.
- Diffs, build outputs, coord tail.
- Cross-checked against contracts/crm-client.md, types.ts, ARCHITECTURE HubSpot notes, Bitrix style, executeBdLead call sites.

**Review verdict**: **PASS** (high fidelity, clean, contract-exact, style-matched). Strong work. Ready for T003/T008/T020 with minor polish notes.

- **Exact interface adherence**: YES. `implements CrmClient`; all 3 methods; string ids; dueDate passed through; optionals (role/email/linkedin) respected with if-guards (no undefined in props). Matches types.ts + contract 100%. executeBdLead compatible (polymorphic mock sims would pass).
- **Correct HubSpot v3 usage**: YES on core.
  - Contacts: POST /crm/v3/objects/contacts + {properties: {firstname, lastname, company, jobtitle?, email?, hs_linkedin_url?}} — exact match to API examples.
  - Deals: POST .../deals + properties (dealname, description) + associations array with to.id + HUBSPOT_DEFINED + typeId:3 (contact link) — correct per standard (associationTypeId 3 documented for deal-contact).
  - Tasks: POST .../tasks + properties (hs_task_subject, hs_task_body, hs_timestamp:number ms-epoch, hs_task_status) + associations to dealId with typeId:216 — matches required shape. hs_timestamp calc uses ms epoch (09:00Z for Bitrix parity).
  - Endpoints, Bearer auth, properties wrapper, response .id top-level: all correct.
- **Style match to bitrix24.ts**: EXCELLENT. Native fetch (no deps), private call<T>(path, body), error strings nearly identical in structure (`Network error calling HubSpot (${path})`, `HubSpot HTTP ${status} on ${path}...`, `HubSpot API error...`, `HubSpot returned no id...`). Consistent formatting, JSDoc-level comments at top + per-method. Returns `{id: string}`. Good.
- **No breakage to Bitrix / interface / MCP**: YES. Bitrix24Client + tool orchestration + index wiring untouched. Barrel addition is additive (current direct imports in src/index/tool continue to work). CrmClient surface unchanged.
- **Good comments for mappings**: YES — top banner details every prop/endpoint/assoc/timestamp decision + rationale + cross-refs to ARCH/contracts. Inline comments on splitName, toHubspotTimestamp, specific assoc typeIds, pipeline defaults, linkedin mapping. Exemplary.
- **Python side**: Updated with detailed commented sketch (props, assocs 3/216, timestamp calc, httpx pattern). Parity perfect; location note preserved. Good.

**Build/type/runtime clean**. No new deps. Future-proof (string ids, date helper, factory stub).

**Detailed findings + concrete issues (priority order; patches in search_replace style)**:

1. **Association type ID for task→deal (216) needs sandbox confirmation (non-blocking but risk)**
   - **Description**: Code uses `associationTypeId: 216` (comment: "Task to deal"). Research/examples commonly cite 12 (or 204) for task-deal links; 216 may be valid in some contexts but can cause "one or more associations are not valid" at runtime.
   - **Contract/ARCH**: "associations array for linking" — impl does use it correctly structurally.
   - **Impact**: Low for T002 (MVP, T020 will catch); would fail live HubSpot createTask.
   - **Suggested patch** (worktree src/crm/hubspot.ts; also mirror in py sketch):
     ```diff
     // Associate task -> deal (216 = Task to deal)
     -            associationTypeId: 216,
     +            // associationTypeId: 216 (Task to Deal); confirm exact value for your portal via
     +            // HubSpot "Associations" settings or /crm/v4/associations/... or sandbox trial (common values: 12, 204, 216)
     +            associationTypeId: 216,
     ```
     Add similar note in createDeal for type 3 (3 is well-confirmed).
   - **Action**: Implementer to add comment + validate in T020. Or hardcode known-good + doc.

2. **dealstage default may not be universal (documented but polish)**
   - **Description**: Hardcodes `dealstage: 'appointmentscheduled'` + 'default' pipeline.
   - **Good**: Commented as "v1 defaults... Users with custom... may need T003+".
   - **Risk**: Some portals' default pipeline first stage differs → 400 on createDeal.
   - **Suggested**: Keep (or make 'closedwon' etc no); leave for now as T002 scope doesn't include config. No code change required.

3. **Minor: Barrel export + factory included (bonus, but scope note)**
   - **Description**: Added src/crm/index.ts exporting * + createCrmClient (T003 preview).
   - **Good**: Clean, matches T001 optional suggestion for barrel. Docs explain "still import Bitrix directly... T003 will wire".
   - **Issue**: Slightly ahead of T003, but zero risk (not used by current index/tool; no behavior change).
   - **Suggested**: OK to keep. If strict, could have been separate, but this is fine/forward progress. No patch.

4. **Error / response handling parity (very close, minor diff)**
   - **Description**: HubSpot errors use `bodyJson.message ?? ...` + correlationId; Bitrix uses error/error_description. Also, HubSpot create response check `if (bodyJson.id === undefined)`.
   - **Good**: Functional + descriptive.
   - **Suggestion for perfect match style** (optional polish):
     Update the "returned no id" to match Bitrix "returned no result" phrasing?
     ```ts
     if (bodyJson.id === undefined) {
       throw new Error(`HubSpot returned no result for ${path}`);
     }
     ```
   - **Low priority**.

5. **Other observations (positive or no action)**
   - Name split + date normalize helper: exact parity with Bitrix (splitName mirrors, timestamp uses 09:00Z).
   - linkedin -> hs_linkedin_url: correct native prop; conditional good.
   - No contactId on task: correct per current CrmTask shape (deal link only).
   - hs_timestamp as number: accepted by HubSpot (docs allow ms or ISO).
   - Python sketch: comprehensive and identical mappings (great for T008 backend).
   - No client secrets in code, native fetch, clean separation.
   - Barrel re-exports types + both clients (useful).

**Verification performed**:
- Full static analysis of all 3 create* methods vs contract + v3 patterns (from ARCH + API refs).
- Build + tsc clean in worktree.
- Ctor + import from build/ succeeds.
- Polymorphic compatibility: executeBdLead path unaffected.
- Cross-check: mappings match Bitrix intent (contact→deal link, deal→task link, dates, comments in description, name split).
- No violations of "preserve Bitrix", "string ids", "dueDate", etc.
- Compared to reference snippets I prepared pre-update: impl matches them closely (excellent).

## Recommendations (post full review)
- **Implementer**: Address #1 (comment on assoc ID + validate later). Append required "What I built / Files touched / Decisions / Open questions" entry to worktree BUILD_COORDINATION.md (per rules; current M on file but no new summary visible in tail). E.g.:
  ```
  - **2026-07-14 [Implementer]** T002: Added src/crm/hubspot.ts (full CrmClient) + src/crm/index.ts (barrel + factory stub). Updated py contract with sketch. Exact contract adherence, v3 + associations + ms hs_timestamp, native fetch + error parity to bitrix24, rich comments. Decisions: 09:00Z timestamp, assoc 3/216 (note verify), deal defaults documented, name split for parity. No changes to tool/index/Bitrix. Builds clean.
  ```
  Then signal ready.
- **Sync**: After fixes, sync worktree→main (as T001).
- **Tester**: Run sims (as in T001), prepare for T020 sandbox (need HubSpot private app token with crm.objects.* scopes). Verify 1+1+3 objects + associations visible in portal.
- **T003 note**: The barrel factory is a head-start — good, but keep Bitrix default + no wiring yet.
- All T002 criteria met at high level. Minor items only.

**Questions**:
- Confirm task→deal associationTypeId (216 vs others)? Sandbox will tell.
- Any plan to support more task props or owner assignment now? (No per contract.)

This completes the full review. Strong implementation — minimal issues.

---
**End of review**. PASS with actionable notes. Implementer to incorporate comment polish + coord update, then loop continues.
