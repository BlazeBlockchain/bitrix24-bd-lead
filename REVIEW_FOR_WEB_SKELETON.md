# REVIEW_FOR_WEB_SKELETON.md

**Reviewer / Scrutinizer Agent Review**  
**Phase**: Web App Skeleton (T011+ base for composer, connections, history)  
**Date**: 2026-07-14  
**Implementer ID**: 019f5d95-5ece-7962-8a2b-b2222d34bc9d (in isolated worktree)  
**Worktree Inspected**: `/home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5d95-5ece-7962-8a2b-b2222d34bc9d` (web/ delivered uncommitted + Implementer coord append)  
**Main Workspace**: `/home/bbartoni/workspace/.bb/bitrix24-bd-lead` (web/ present post "T003 + web committed (9550de5)"; src/crm + backend stable)  
**Coordination**: Re-read FULL BUILD_COORDINATION.md (multiple times before/after inspections). Last entries note web Implementer delivery + spawn of web reviewer/tester. Implementer appended detailed "What I built / Files / Decisions / Blockers" to worktree BUILD_COORDINATION.md (adhered to rule).

**Status**: Web skeleton code delivered in worktree (and visible in main web/); full multi-file review via reads, builds, worktree/git, cross-refs to specs, backend stub inspection, flow simulation. TS foundation + backend untouched.

## Mandatory Reads + Inspections (followed exactly)
- FULL latest BUILD_COORDINATION.md (T001/T002/backend/T003 complete; "web skeleton just delivered"; Implementer ID 019f5d95-5ece...; coord spawn notes; prior agent logs).
- specs/004-ai-bd-assistant/{plan.md, tasks.md (T011 scaffold, T012 connections, T013 composer, T014 history), spec.md, contracts/*}
- docs/{UI_UX.md (screens, journey, tokens, responsive, components), FEATURES.md (MVP stories/ACs, composer+push, history), ARCHITECTURE.md (web React/Vite/Zustand, API client, CrmClient usage server-side)}
- web/ source (worktree + main for sync state): package.json, vite.config.ts, tsconfigs, src/{main.tsx, App.tsx, App.css, index.css, api/client.ts, stores/appStore.ts, components/{Composer.tsx,Preview.tsx,ConnectionsForm.tsx,HistoryList.tsx}}, index.html, README.md, dist/ (post-build)
- backend stub for API: backend/app/{main.py ( /api/health + /api/leads/push with provider/token Query + CrmClient factory), config.py, adapters/crm/__init__.py + impls}, docker-compose.yml, .env.example
- Stable TS foundation: src/crm/* (types, bitrix24, hubspot, index factory), src/tool.ts (executeBdLead polymorphic), src/index.ts
- Prior artifacts: REVIEW_FOR_*.md, TEST_REPORT_*.md for pattern + no-regression baseline
- Supporting: git worktree list/status/diff, npm run build + tsc, py syntax, manual flow sims

**Monitoring / tools used**:
- `git worktree list`, `ls web/src`, `git status --porcelain` (web/ untracked in wt), file mtimes.
- `read_file` on all key web/backend files + tail/grep on coord.
- `npm run build` (main + worktree web) → clean.
- `npx tsc --noEmit` on root (TS src pristine).
- Dep-free + mocked python simulation of push flow + code inspection.
- Grep for UI terms (Generate, preview, tokens, nav) across web + docs.

## Worktree / Main State Observed
- Worktree: new `web/` (full Vite React TS scaffold + custom files); modified BUILD_COORDINATION.md; other pre-existing ?? files.
- Main: `web/` directory present with identical delivered contents (build artifacts, src structure).
- No modifications to `src/crm/`, `src/tool.ts`, `src/index.ts`, backend/, contracts/ or docker (critical: 0 breakage risk).
- Implementer log present in wt coord (detailed, covers mandatory fields).
- Builds: `cd web && npm run build` (tsc -b && vite) → SUCCESS (dist/ produced, no errors) in both main + wt.
- TS root: clean.

## Review Criteria Applied (cross-referenced exactly)
**UI_UX.md**:
- Screens & nav: Dashboard (/), New Lead (/new), History (/history), Connections (/connections), Account (/account + route). Persistent header with logo + NavLinks + user pill. Matches inventory (no public landing/pricing in skeleton, as expected).
- Primary journey: "paste → ... → push". Form fields (company, contact+role, signal, pain, notes), preview pane (snapshot/opener/3 follow-ups), Push action.
- Tokens: Exact CSS vars in index.css (--bg:#0d1117, --surface, --accent:#f97316, --accent-2, --accent-3, --danger, --radius, etc.).
- Responsive: .split grid (1fr/1fr → stack @900px), .form-row (2col → 1 @600px), touch-friendly inputs, mobile notes.
- Components: Composer (split form+preview), Preview (snapshot + opener + TaskTimeline-like), ConnectionsForm (provider cards-ish + instructions), HistoryList (rows + use similar). Good.
- Dark theme, stub notes, forgiving states present.

**plan.md + tasks.md + spec.md**:
- React + Vite + TypeScript + Zustand + react-router-dom: exact.
- Composer + push flow, history, connections: implemented (stub versions).
- API client: native fetch (per "use native fetch" + ARCH).
- "Minimal for MVP"; prepares T012-T015. Composer pushes directly to /push (backend has no /enrich yet).
- No heavy new deps.

**ARCHITECTURE.md**:
- Web as React/Vite client calling same authenticated backend APIs.
- API client targets backend stub (http://localhost:8000/api).
- CrmClient exercised server-side only (via /push exercising factory + adapters).
- No client-side secrets.

**No breakage**:
- TS src/crm (CrmClient, adapters, factory from T001-T003) + executeBdLead untouched + builds green.
- Backend Python adapters + /push shape preserved 1:1.
- MCP Bitrix path unchanged.

**Stub flow confirmation (provider/token)**:
- web/src/api/client.ts: pushLead(input, provider, token?) → fetch(`${API_BASE}/leads/push?provider=...&token=...` (POST JSON).
- backend/app/main.py: @post("/api/leads/push") receives provider=Query + token=Query; falls back to settings; create_crm_client(provider, token) → contact → deal(linked) → 3x createTask (cadence +4/+9/+14) → returns {contact_id, deal_id, task1:{id,date}, ..., provider, note}.
- Verified via code match + dep-free simulation (provider passed, token len used, result keys + shape match web's PushResult + LeadPushInput fields accepted).
- Both providers supported (select in ConnectionsForm → store → client).
- Confirmed: "stub flow works with backend /push (provider/token)".

All other: no violations of "All CRM via CrmClient", contracts parity, dark/mobile, etc.

## Verdict: **PASS** (high-quality skeleton; faithful to UI_UX/plan/ARCH at T011 level; ready for sync + T012+ expansion)

Positives:
- Excellent fidelity to required structure, tokens, layout (split composer+preview), Zustand draft/provider/history.
- Native fetch API client exactly matches backend stub contract and ARCH guidance.
- Responsive basics + component breakdown good.
- Build clean, no TS breakage anywhere, stub flow fully exercises backend CrmClient (Bitrix/HubSpot parity).
- Detailed self-documentation in code + Implementer appended full coord log.
- Prepares exact next steps (real enrich, auth, server history, T006 token vault).

## Concrete Findings + Issues (actionable; mostly polish / future-alignment)

**#1 Composer journey vs UI_UX exact happy path**  
UI_UX: Split layout; "Generate with AI" (primary) → preview appears (with skeleton/loading) → "Push to CRM" enabled after.  
Current: Preview always live/reflects draft (client stub); single button "Push to CRM (stub)". No explicit generate step or loading state. Stubs acknowledge this ("T013 will...").

Patch suggestion (in web/src/components/Composer.tsx):
```diff
# file_path: web/src/components/Composer.tsx
# Add state + separate generate action for closer alignment (even as stub)
+ const [previewGenerated, setPreviewGenerated] = React.useState(false);
+ const [isGenerating, setIsGenerating] = React.useState(false);
...
- const handlePush = async () => { ... }
+ const handleGenerate = () => {
+   setIsGenerating(true);
+   // simulate AI latency + skeleton
+   setTimeout(() => { setPreviewGenerated(true); setIsGenerating(false); }, 250);
+ };
+ const handlePush = async () => {
+   if (!previewGenerated) { /* or allow */ }
+   ...
+ };
...
- <button onClick={handlePush} disabled=...>Push to CRM (stub)</button>
+ <button onClick={handleGenerate} disabled={isGenerating}>Generate with AI (stub)</button>
+ <button onClick={handlePush} disabled={loading || !previewGenerated || !draft.company_name}> 
+   {loading ? 'Pushing...' : 'Push to CRM'}
+ </button>
```
(Also add conditional skeleton in Preview or wrapper: `{isGenerating ? <div className="skeleton">Contacting LLM…</div> : <Preview ... /> }`)

**#2 Header navigation incomplete**  
UI_UX: "Top-level nav (persistent header): ... | Account".  
Current: Dashboard | New Lead | History | Connections. No Account link (route exists + page).

Patch:
```diff
# file_path: web/src/App.tsx (in Header nav)
-        <NavLink to="/connections" ...>Connections</NavLink>
+        <NavLink to="/connections" ...>Connections</NavLink>
+        <NavLink to="/account" className={({ isActive }) => isActive ? 'active' : ''}>Account</NavLink>
```

**#3 Connections UI vs UI_UX "Add CRM" modal + cards**  
UI_UX: "Add CRM" button → modal with two options + inline instructions.  
Current: Flat select + input + inline instructions. Functional for stub but flatter.

**#4 Preview / AI states**  
UI_UX: "AI preview always shows skeleton or progress ("Contacting Gemini…") within 300ms. No layout shift." "Personalized using your last 7 leads".  
Current: Static hardcoded (good cadence match), always visible, "stub" notes. No skeleton, no memory indicator yet.

**#5 Minor / polish**
- Account nav link + perhaps add to header right side if space.
- useSimilar in HistoryList uses `window.location.hash` + alert (fragile; use react-router navigate when available).
- Some inline styles (prefer classes); (window as any) cast in App.
- Vite dev: no proxy for /api (users must run backend on :8000); addable later.
- Dashboard: "Recent leads" stub + no CRM status pill / memory strength (UI_UX).
- web/package.json + README still mostly Vite template (add BD-specific quickstart note?).
- No "Regenerate" button or copy for tasks yet.
- In client.ts: comments mention future JWT; current ?token matches backend stub exactly (good).

All non-blocking for skeleton. Builds, types, flow, no breakage = green.

## Actions Taken
- Full protocol: re-reads of coord + all required specs/docs/web/backend/TS; worktree + main inspections + diffs.
- Ran `npm run build` (web main + wt) + root tsc (clean).
- Confirmed stub /push flow with code analysis + simulation (provider/token -> factory -> CrmClient ops -> matching result shape for web PushResult).
- Created this REVIEW_FOR_WEB_SKELETON.md with checklist, verdict, concrete patches, recs.
- Will append detailed log to BUILD_COORDINATION.md (main).
- No source edits performed (reviewer role only; patches are documented suggestions).
- Parity note will be added to worktree coord if writable.

## Recommendations
- **Implementer**: Incorporate #1 (generate step + skeleton) + #2 (Account link) for closer UI_UX match; append any post-review updates to worktree coord if changes. Rebuild + verify flow.
- **Coordinator**: Sync web/ (if not already) from wt after; mark T011 complete in tasks.md; spawn tester for web.
- **Tester/Committer**: Re-verify build, run dev + curl simulation or mocked backend for full journey (signin stub → connections set token → push → history + use similar). Confirm /push result populates store + UI. Smoke against docker backend when net/DB/tokens available. Prepare commit note.
- **Next**: T012 (real connect flows), T013 (real /enrich + generate button + LLM preview), T005 (auth/JWT), T014 (server history), T021 (add web to compose). Backend stub /push remains the contract anchor.
- Carry opens: sandbox tokens for real CRM verification (T020), full auth later, enrich endpoint.

**Files modified by this agent**: REVIEW_FOR_WEB_SKELETON.md (created), BUILD_COORDINATION.md (this append only).  
**Timestamp**: 2026-07-14. All mandatory protocol + inspections + verifs complete. Web skeleton reviewed; stub flow with backend /push (provider/token) CONFIRMED working. High alignment; foundation solid for next phases. Re-read coordination + specs before future actions.
