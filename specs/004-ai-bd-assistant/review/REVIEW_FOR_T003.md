# REVIEW_FOR_T003.md — Selector + MCP Wiring (T003/T019)

**Reviewer / Scrutinizer Agent** (for T003 Implementer ID 019f5d95-311f-7850-aeae-8744a43ca682)  
**Date**: 2026-07-14  
**Role Protocol**: Followed exactly (re-reads, monitor worktree, cross-check plan/contracts/ARCH, no src edits by reviewer, feedback + patches in style, update coord + this file).

## MANDATORY PROTOCOL FOLLOWED
- Read FULL BUILD_COORDINATION.md (T001/T002/backend complete; T003 in progress per "Next: T003 (selector + MCP wire)"; Implementer + spawn notes).
- Read specs/004-ai-bd-assistant/{plan.md, tasks.md (explicit T003 "Add provider selector / factory for CrmClient (Bitrix24 default for back-compat)", T019 "Update MCP server (`src/index.ts` + tool) to use shared CrmClient/core"), contracts/crm-client.md, contracts/crm_client.py, spec.md, data-model.md, research.md}.
- Read docs/ARCHITECTURE.md (full; CrmClient abstraction, "Provider selector in backend (and MCP for back-compat)", env notes, no client-side secrets, MCP as thin stdio wrapper reusing adapters).
- Read pre-T003 state (main workspace): src/crm/* (types.ts exact contract, bitrix24.ts, hubspot.ts, index.ts with T002 minimal factory), src/tool.ts (polymorphic executeBdLead over CrmClient), src/index.ts (hardcoded `new Bitrix24Client(webhookUrl)` + BITRIX24_WEBHOOK_URL only + validation + "Bitrix24" strings in output/errors).
- Monitored T003 Implementer worktree: `/home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5d95-311f-7850-aeae-8744a43ca682` (repeated `git worktree list`, `git diff --stat`, `git diff`, file mtimes, ls, cat, status).
- Additional: package.json, tsconfig.json, .env.example (DEFAULT_CRM_PROVIDER + HUBSPOT_ACCESS_TOKEN), backend/app/adapters/crm/__init__.py + config.py + main.py (for cross-layer consistency / no backend contract impact), build/ artifacts, prior REVIEW_*.md + TEST_REPORT_T002.md.
- Used required MCP "tasks" discovery via `search_tool` before any potential use (not needed for fs/git monitoring; used git + reads exclusively).
- Verifications: repeated builds/tsc, logic sims (pre + post), diffs vs contracts/types/ARCH, export/runtime smoke, Bitrix exact path preservation.

**Worktree state observed**:
- Uncommitted changes (implementer): src/crm/index.ts (major: full selector/factory + env support + createCrmClientFromEnv + SUPPORTED), src/index.ts (MCP wiring: CRM_PROVIDER branching + exact Bitrix compat block + use of createCrmClient), src/tool.ts (docstring only).
- git diff --stat (wt): 3 files, +110/-32.
- No changes to: contracts/, types.ts, bitrix24.ts, hubspot.ts, README, .env.example, backend/, build/ (will regen), tool logic or BdLeadSchema.
- BUILD_COORDINATION.md in wt: no Implementer append yet (per "Information Sharing Rule").
- Main workspace: still pre-T003 state at review time (HEAD d537eba "docs: spawn T003 + web agents"; src/index.ts direct Bitrix).

**Key diffs captured** (summarized; full via `git -C <wt> diff`):
- src/crm/index.ts: header update, resolveConfigFromEnv, enhanced createCrmClient (config defaults '', resolve + validate), createCrmClientFromEnv (CRM_PROVIDER parse + aliases), SUPPORTED_CRM_PROVIDERS, detailed JSDoc.
- src/index.ts: replace direct import/ctor with createCrmClient; full branching on rawProvider (isHubspot); **exact** Bitrix error texts/exits/URL check in else; hubspot token path; client typed via ReturnType; execute + output unchanged.
- src/tool.ts: comment update only ("via CrmClient (Bitrix24 or HubSpot)"; "MCP surface ... unchanged").

## Review Criteria (from prompt + plan/contracts/ARCH)
- Exact CrmClient use: YES (factory returns Bitrix24Client | HubspotClient; both `implements CrmClient`; executeBdLead receives abstract; all paths go through interface methods).
- No breakage to Bitrix: YES (default/!hubspot path byte-identical for validation, messages, URL parse, exit, ctor call pattern; direct `new Bitrix24Client` + re-exports preserved; tool name/output text same).
- Support for both providers: YES (CRM_PROVIDER=bitrix24|hubspot|hs|bitrix + aliases; explicit createCrmClient(p, cfg); env-driven; .env vars respected).
- Minimal changes: YES (only src/crm/index.ts + src/index.ts + 3-line comment in tool; no touch to orchestration, schemas, contracts, adapters, types).
- Env handling: Good (config precedence > env; resolve per provider; strict throw on missing like old code). See findings.
- Check vs plan/contracts/ARCH: Matches (T003 selector/factory default bitrix; T019 MCP use shared CrmClient; ARCH "Provider selector in ... MCP for back-compat"; contracts source of truth; no client secrets; backend Python factory mirrors shape; preserve MCP observable for default).
- No impact on backend contracts or prior foundation: YES (Python adapters/contracts untouched; TS CrmClient surface identical; backend main.py /push uses its own create_crm_client mirroring; foundation from T001/T002 preserved exactly).

**Pre-T003 baseline verifs (main, repeated)**:
- `npm run build` + `./node_modules/.bin/tsc --noEmit`: exit 0.
- src/index direct Bitrix path + execute flow: confirmed via prior sims + reads.

## Post-Change Verifs (worktree + temp overlay)
- Full sources from wt overlaid to /tmp/t003_review + `./node_modules/.bin/tsc --noEmit`: 0.
- Full `tsc` build in overlay: 0.
- Runtime smoke (node on built):
  - SUPPORTED_CRM_PROVIDERS, Bitrix24Client export: OK.
  - createCrmClient() / createCrmClientFromEnv() → correct classes (Bitrix default, Hubspot when CRM_PROVIDER=hubspot).
  - Explicit config + env precedence: works.
  - Mock full executeBdLead via factory clients: string IDs, +4/+9/+14 dates, 1c+1d+3t, polymorphic: PASS.
- Bitrix compat path (no CRM_PROVIDER or bitrix): exact stderr + exit behavior reproduced in analysis.
- No new deps; native fetch paths untouched.

**Files read/inspected in depth**:
- Main (pre): src/crm/index.ts (minimal T002), src/index.ts (hardwire), src/tool.ts, src/crm/{types,bitrix24,hubspot}.ts, .env.example, BUILD_COORDINATION.md, plan/tasks/contracts, ARCHITECTURE.md.
- Worktree (post): all above + full diffs + updated src/index.ts + src/crm/index.ts + src/tool.ts.
- Cross: backend/app/adapters/crm/__init__.py (factory), config.py (DEFAULT_CRM_PROVIDER), main.py (/push), contracts/*, prior REVIEWs.

## Review Verdict: **PASS WITH MINOR FINDINGS** (high quality, contract-exact, back-compat preserved, minimal + correct env wiring).

Strong adherence to "exact CrmClient", "no breakage to Bitrix", "support both", "minimal changes". Factory + MCP wiring enable T008/T019/T020 cleanly. Builds + loads + sims green. Ready after addressing notes (mostly polish + consistency).

## Detailed Findings + Actionable Patches (search_replace style)

1. **Env var naming inconsistency (CRM_PROVIDER vs DEFAULT_CRM_PROVIDER) — non-blocking for T003 but affects docs/consistency**
   - **Description**: Implementer introduced/used `CRM_PROVIDER` (MCP + fromEnv). .env.example + backend use `DEFAULT_CRM_PROVIDER=bitrix24`. ARCH/.env notes don't specify exact var for MCP layer.
   - **Impact**: Works independently (MCP is separate stdio process); users set per-process. Minor doc friction.
   - **Contract/plan/ARCH**: No mandate on exact name; "env handling".
   - **Suggested**:
     - Update .env.example to document both (or prefer CRM_PROVIDER for MCP, DEFAULT_ for backend).
     - Or align to one (e.g. keep CRM_ for thin MCP wrapper).
     - Add comment in src/crm/index.ts + src/index.ts referencing .env.example.
   - No code change required for T003 scope.

2. **MCP success/error output strings still hardcode "Bitrix24" (observable for HubSpot users)**
   - **Description**:
     - `✅ Bitrix24 entry created successfully`
     - `Bitrix24 error: ${message}`
     - Tool name/desc in BD_LEAD_TOOL remains "bitrix24_create_bd_lead" + "in Bitrix24".
   - **Good**: Preserves 100% for default Bitrix users + tool name (per spec compat). Minimal change.
   - **Issue**: When CRM_PROVIDER=hubspot, output misleads (says Bitrix24 but used HubspotClient).
   - **ARCH/plan**: "MCP server ... thin stdio wrapper"; T019 "update ... to use shared"; back-compat focus on existing flow.
   - **Suggested patch** (in src/index.ts, for future-proofing; keep minimal now):
     ```diff
     const providerLabel = isHubspot ? 'HubSpot' : 'Bitrix24';
     ...
     const output = [
     -  '✅ Bitrix24 entry created successfully',
     +  `✅ ${providerLabel} entry created successfully`,
     ...
     -  return { content: [{ type: 'text', text: `Bitrix24 error: ${message}` }], isError: true };
     +  return { content: [{ type: 'text', text: `${providerLabel} error: ${message}` }], isError: true };
     ```
     (Tool name/desc left as-is for compat; update description in BD_LEAD_TOOL optionally later.)
   - **Action**: Low priority for T003; consider in T019 polish or T020. Current acceptable for back-compat gate.

3. **Implementer did not append to BUILD_COORDINATION.md (per mandatory rule)**
   - **Description**: Changes present + code good, but no "What I built", "Files touched", "Decisions made" (e.g. "kept exact Bitrix error texts", "used createCrmClient not always FromEnv", "aliases for CRM_PROVIDER", "ReturnType for typing"), "Open questions".
   - **Impact**: Violates "Information Sharing Rule (mandatory for all agents)".
   - **Suggested**: Implementer must append before sync/commit (see examples in coord).
   - No patch; process item.

4. **Minor: createCrmClient signature change (config now optional default '')**
   - **Description**: Pre (T002 stub): `config: string` (required). Now `= ''`. Callers in wiring use explicit 2 args; FromEnv uses 1 arg.
   - **Good**: Enables env resolution. Matches Python factory.
   - **Risk**: If any external code did `createCrmClient('hubspot')` (1 arg), would have been TS/runtime error before; now works (but was never wired).
   - **Impact**: None (no prior consumers of factory per T002 reviews).
   - **Action**: None. Good evolution.

5. **No other issues**
   - Exact use of CrmClient (no direct adapter calls in index/tool post-wiring).
   - URL validation only for Bitrix (correct; tokens not URLs).
   - No secret in code; all via process.env.
   - Barrel re-exports preserved.
   - Python backend unaffected (different process + its DEFAULT_ + factory).
   - Matches contracts (CrmClient shapes), types, ARCH selector requirement.
   - Tool surface (name, schema, result shape) 100% unchanged.

**Build/type/runtime clean**. No new deps. Future-proof for T008 (orchestration can use createCrmClientFromEnv or explicit), web/ext, backend parity.

## Recommendations
- **Implementer (ID ...ca682)**: 
  - Append full entry to worktree BUILD_COORDINATION.md NOW (timestamp, "What I built" = factory enhancements + MCP wiring in index + tool comment; "Decisions": exact compat block copy for Bitrix errors/exits, provider aliases support, config precedence, keep tool name+strings for compat, createCrmClientFromEnv for future; "Open Qs": env var name align with DEFAULT_ ?; output strings dynamic?).
  - Rebuild + re-smoke in wt.
  - Consider patch #2 (output labels) if scope allows, or note for later.
- **Coordinator**: After append + re-verif, sync wt changes to main. Update tasks.md checkboxes for T003/T019. Spawn Tester for T003 (smoke with real tokens in T020).
- **Tester/Committer**: 
  - Re-run full verifs post-sync (build, tsc, execute sims for both providers using real envs if sandbox, direct Bitrix path).
  - Confirm no regression in MCP observable for default (no CRM_PROVIDER).
  - Test hubspot path (requires token; expect HubSpot records + associations).
  - Prepare commit e.g. "feat(mcp): T003/T019 provider selector + MCP wiring (CRM_PROVIDER, env, both CRMs via CrmClient; Bitrix 100% compat; builds+sims green)".
- **General**: 
  - Update .env.example + docs (README, ARCH) to show CRM_PROVIDER example for MCP (parallel to DEFAULT_).
  - T020 will validate live both providers + assoc correctness.
  - Carry prior open items (HubSpot token type, sandbox, Python contract loc).
  - No backend contract impact — Python factory mirrors (provider, config str) shape.

**Timestamp**: 2026-07-14. All mandatory reads + worktree monitoring + cross-spec checks + verifs complete. T003/T019 criteria satisfied at high fidelity with the 2-3 notes above. Foundation preserved; ready for next (T008 reuse, web, T020).

**Files modified by this agent**: REVIEW_FOR_T003.md (new), BUILD_COORDINATION.md (this append only). No source changes.

**References in this review**:
- Pre state vs post diffs.
- contracts/crm-client.md + types.ts (exact match).
- src/crm/index.ts (new), src/index.ts (wired).
- .env.example + backend config (env cross-check).
- ARCHITECTURE §CrmClient + MCP + env.
- BUILD_COORDINATION.md history (T001/T002 patterns for compat).

---
End of REVIEW_FOR_T003.md
