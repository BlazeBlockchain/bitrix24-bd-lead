# REVIEW_FOR_004_T001.md

**Reviewer / Scrutinizer Agent Review**  
**Task**: T001 - CrmClient refactor (CrmClient interface + Bitrix24 adapter)  
**Date**: 2026-07-14  
**Implementer**: subagent 019f5d81-3dd1-7151-9463-cfc248337599 (in isolated worktree)  
**Worktree Inspected**: `/home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5d81-3dd1-7151-9463-cfc248337599`  
**Main Workspace**: `/home/bbartoni/workspace/.bb/bitrix24-bd-lead` (unchanged src/ at time of review)

## Mandatory Files Read (per instructions)
- BUILD_COORDINATION.md (full, including implementer's appended log in worktree)
- specs/004-ai-bd-assistant/plan.md
- specs/004-ai-bd-assistant/tasks.md
- specs/004-ai-bd-assistant/contracts/crm-client.md
- docs/ARCHITECTURE.md
- src/client.ts (original), src/tool.ts, src/index.ts (both main pre-refactor + worktree post-refactor versions)
- Also: worktree src/crm/types.ts, src/crm/bitrix24.ts, build/ outputs, specs/.../contracts/crm_client.py, package.json, tsconfig.json, data-model.md (cross-checks), git status in worktree.

Additional verifications:
- `git worktree list` (main shows only primary; worktree isolated)
- Re-ran `tsc --noEmit` in worktree (exit 0)
- Inspected `build/crm/bitrix24.js` and `build/tool.js` for emitted behavior
- Grep across src/ and build/ for field names (UF_CRM_TASK, DEADLINE, CONTACT_ID, NAME/LAST_NAME, error strings), imports, Crm* types
- Cross-compared every mapping, error path, date logic, orchestration flow vs original src/client.ts + tool.ts

## Overall Assessment
**Strong pass on core requirements.** The refactor is high-quality, minimal, and faithful.

- **Exact Bitrix24 behavior preserved**: Field names (NAME, LAST_NAME, POST, COMPANY_TITLE, TITLE, CONTACT_ID, COMMENTS, DEADLINE, RESPONSIBLE_ID, UF_CRM_TASK), error messages/paths (`Network error calling Bitrix24 (...)`, `Bitrix24 HTTP ${status}...`, `Bitrix24 API error...`, `Bitrix24 returned no result`), date formatting (`${dueDate}T09:00:00+00:00`), linking (`D_${dealId}`), name splitting, fetch call(), webhook userId extraction, task result shape handling — all identical on the wire and in source/build.
- **Contract adherence**: src/crm/types.ts matches `contracts/crm-client.md` 1:1 (CrmContact with optionals, CrmDeal/CrmTask with string ids + dueDate, CrmClient 3 methods returning `{id: string}`).
- **No breaking changes for future**:
  - MCP tool (`bitrix24_create_bd_lead`) observable behavior 100% same (text output, errors, payloads).
  - String IDs align with data-model.md (crm_contact_id etc. as string) and JSON-friendly for web/extension/backend.
  - Native fetch, no new deps (package.json unchanged).
  - executeBdLead now takes `CrmClient` (polymorphic for T002 HubSpot, T008 orchestration, T019 MCP).
- **Clean interface + types**: Properly exported in `src/crm/types.ts`. Bitrix24Client implements it. Good separation (types vs impl).
- **Error handling**: Preserved exactly; no regressions.
- **Plan/ARCHITECTURE alignment**: Foundational only (no memory/LLM/auth premature). Matches "src/crm/" layout, "CrmClient abstraction", "preserve existing Bitrix24 logic", Python parallel contract. Good.

Build clean, reversible, documented in code and coordination log.

**Main workspace observation**: src/ still contains original `client.ts` + direct imports in `tool.ts`/`index.ts`. Implementer's work isolated to worktree (as instructed). Integration step (copy/merge changes to main + update coordination) will be needed before T002 or commit.

## Concrete Issues / Actionable Items
List is ordered by priority/impact. Most are minor polish / future-proofing. No blockers for T001 acceptance.

### 1. Python interface file location (ambiguous per instructions)
- **Description**: `specs/004-ai-bd-assistant/contracts/crm_client.py` created co-located with .md contract. Implementer documented assumption ("placed here... per 'e.g. in a new backend/contracts or docs'"; "move if preferred").
  - Plan.md: "parallel TypeScript + Python interface definitions", backend target `backend/app/adapters/crm/`, contracts in specs/.
  - ARCHITECTURE.md + tasks reference future `backend/`.
  - This may be premature or need coordination once backend scaffolding (T004) starts.
- **Impact**: Low for now (definition file only, no code exec); high if wrong location causes copy-paste later.
- **Suggested change** (or decision): Clarify location. Recommend either:
  - Keep for now (specs/ as "shared contracts" source of truth).
  - Or move to `backend/contracts/crm_client.py` (or `shared/contracts/`) when T004 creates backend dir.
  - Update plan.md / quickstart.md / this review if changed.
- **Action for Implementer**: Document decision in next BUILD_COORDINATION update. If ambiguous, ask Coordinator.

### 2. Date input robustness in adapter (dueDate handling)
- **Description**: `bitrix24.ts:109`:
  ```ts
  DEADLINE: `${task.dueDate}T09:00:00+00:00`,
  ```
  Contract: `dueDate: string; // YYYY-MM-DD or ISO`
  Current tool.ts always passes YYYY-MM-DD (from addDays). If full ISO (e.g. from future web/LLM or other callers) or date with time passed, produces malformed deadline like `2026-07-18T10:00:00+00:00T09:00:00+00:00`.
- **Preservation**: Current behavior exact match to original.
- **Future risk**: Breaks HubSpot adapter expectations or backend date handling (T002/T008). Python side will need equivalent.
- **Suggested change** (search_replace style for worktree src/crm/bitrix24.ts):

```diff
diff --git a/src/crm/bitrix24.ts b/src/crm/bitrix24.ts
index ...
--- a/src/crm/bitrix24.ts
+++ b/src/crm/bitrix24.ts
@@
+  private normalizeDate(d: string): string {
+    // Accept YYYY-MM-DD or ISO; always return YYYY-MM-DD for deadline base
+    return d.includes('T') ? d.split('T')[0] : d;
+  }
+
   async createTask(task: CrmTask): Promise<{ id: string }> {
     ...
     const result = await this.call<...>('tasks.task.add', {
       fields: {
         ...
-        DEADLINE: `${task.dueDate}T09:00:00+00:00`,
+        DEADLINE: `${this.normalizeDate(task.dueDate)}T09:00:00+00:00`,
         ...
```

(Also consider adding similar helper comment or shared util later. Update Python contract notes too.)

- **Alternative**: Normalize at call sites in tool.ts (but adapter is better place for CRM-specific formatting).
- **Action**: Implementer to apply or equivalent before T002 (HubSpot uses different timestamp format).

### 3. String ID change in exported BdLeadResult (observable typing)
- **Description**: `tool.ts:159` (and returns):
  ```ts
  export interface BdLeadResult {
    contact_id: string;  // was number
    ...
  }
  ```
  MCP output text is unchanged (interpolation). Internal to `executeBdLead`. Contract requires string returns.
- **Impact**: Low (no external consumers of this type besides the MCP handler itself). Aligns with data-model strings + Python.
- **Suggested change** (if wanted for clarity): Add JSDoc.
  ```ts
  /**
   * Result of executeBdLead. IDs are strings per CrmClient contract
   * (Bitrix24/HubSpot IDs are numeric but represented as string for portability).
   */
  export interface BdLeadResult { ... }
  ```
- **No code change required** if behavior same. Note in docs.

### 4. Barrel / clean re-exports for crm module (minor cleanliness)
- **Description**: Consumers do `import type { CrmClient } from './crm/types.js'` and `import { Bitrix24Client } from './crm/bitrix24.js'`.
  - No `src/crm/index.ts`.
  - Future web/extension/backend sharing of types may benefit from single import point.
- **Impact**: None for T001/MCP. Nice-to-have.
- **Suggested** (optional):
  Create `src/crm/index.ts`:
  ```ts
  export type { CrmClient, CrmContact, CrmDeal, CrmTask } from './types.js';
  export { Bitrix24Client } from './bitrix24.js';
  ```
  Then update imports to `from './crm/index.js'`.
- **Action**: Low priority; consider for T003 (provider selector) or when exposing to other packages.

### 5. Minor: Role optionality + undefined handling in payloads
- **Description**: CrmContact.role? (per contract) vs old ContactFields role: string. In adapter:
  `POST: contact.role` → if undefined, JSON.stringify omits key (correct, Bitrix ignores absent).
  Tool.ts always supplies role (from input).
- **Good**: Backward and forward safe.
- **Suggested**: Add test comment or small explicit:
  ```ts
  ...(contact.role && { POST: contact.role }),
  ```
  in fields (defensive). Optional polish.
- **Action**: Not blocking.

### 6. Other observations (no action)
- Error paths, fetch, no-result checks, response.ok + body.error: identical.
- No premature memory/LLM/orchestration beyond the lead flow (which was already in tool).
- UF_CRM_TASK linking exact (`["D_..."]`).
- Python mirrors with good notes on mappings (camelCase intentional).
- Types exported properly for TS consumers.
- No new runtime deps, native fetch preserved.
- Worktree git status confirms targeted changes (client.ts deleted, crm/ added, minimal edits to tool/index, py contract).
- MCP server entrypoint (index.ts) + validation + error wrapping unchanged.

## Verification Performed
- Field-by-field + error string match between original `src/client.ts` (main) and worktree `src/crm/bitrix24.ts` + build/.
- Contract md == types.ts (exact).
- Full call flow: contact → deal (with contactId link) → 3 tasks (with dueDate/UF_CRM/deadline) unchanged in tool.ts except interface keys.
- Ids: string at Crm boundary, Number() coercion only for Bitrix numeric fields where needed.
- Build + typecheck green.
- No other files import old paths in worktree src/.

## Recommendations Before Proceeding
1. Implementer: Incorporate #1 (clarify Python loc) + #2 (date normalize) via search_replace in worktree.
2. Sync changes to main workspace (e.g. via patch, git worktree merge, or manual apply) + update main BUILD_COORDINATION.md.
3. Tester/Committer: Run full `npm run build`, any existing smoke (if .env present), manual Bitrix24 sandbox test if possible (T020 later).
4. Coordinator: Mark T001 complete in tasks.md / coordination after fixes + sync.
5. For T002 (HubSpot): Use same types + implementer should verify against contract notes (associations, hs_timestamp).

## Questions for Clarification (per instructions)
- Interface location / Python side: Where should the canonical Python CrmClient live long-term (`specs/.../contracts/`, `backend/`, shared dir)? Confirm before T004/T008.
- Any desire to keep old *Fields interfaces temporarily for compat (unlikely needed)?
- Should CrmClient gain optional `getProviderName(): string` or `healthCheck()` now, or strictly later?

This review is concrete and actionable. All mandatory review criteria passed with only polish suggestions.

**Files for Implementer to reference**:
- Worktree: `src/crm/bitrix24.ts`, `src/tool.ts`
- Contracts: `specs/004-ai-bd-assistant/contracts/crm-client.md` and `.py`
- This: `REVIEW_FOR_004_T001.md`
- Coordination append to follow.

---
**End of review**. Ready for Implementer response + Tester.
