# REVIEW_FOR_T005.md

**Reviewer / Scrutinizer Agent Review**  
**Phase**: T005 (auth stub / JWT placeholder + protected + /push update)  
**Date**: 2026-07-14  
**Implementer ID**: 019f5d9f-59b1-7ec3-9544-4d634c8882ad (in isolated worktree)  
**Worktree Inspected**: `/home/bbartoni/.grok/worktrees/workspace-bitrix24-bd-lead/subagent-019f5d9f-59b1-7ec3-9544-4d634c8882ad`  
**Main Workspace**: `/home/bbartoni/workspace/.bb/bitrix24-bd-lead` (T001-T003 + backend skeleton + web committed; pre-T005 state)  
**Coordination**: Re-read full BUILD_COORDINATION.md (main + worktree) multiple times. T005 Implementer, Reviewer, Tester spawned by Coordinator. Implementer delivered code changes but has not yet appended required "What I built / Files touched / Decisions / Open questions" summary to worktree BUILD_COORDINATION.md.

**Status**: Code changes appeared in worktree (backend/app/main.py, config.py, requirements.txt + pyc updates). Full review via file reads, git diff/status/worktree polls, AST/parse checks, Crm flow verification, cross-refs to specs. TS/web sources untouched.

## Mandatory Reads + Monitoring (followed exactly)
- FULL latest BUILD_COORDINATION.md (main + worktree copy) — T001/T002/backend/T003/web complete; "T005 (auth stub / JWT in backend + basic protected)"; "T005 auth implementer (019f5d9f-59b1-7ec3-9544-4d634c8882ad)"; "simple auth (token or placeholder JWT), protected deps, update /push to require/use auth"; "All agents re-reading this coord".
- specs/004-ai-bd-assistant/{plan.md, data-model.md, contracts/crm_client.py, contracts/crm-client.md, tasks.md (T005: "Implement Google OAuth + JWT auth service (login, /me, protected dependency). Store minimal user record."), spec.md (FR-001 Google OAuth + JWT)}
- docs/ARCHITECTURE.md (full: "Google OAuth2 + JWT (short-lived)", "server env only", "CRM tokens envelope-encrypted", "CrmClient server-side", "no client-side secrets", user auth vs CRM creds orthogonal)
- Backend pre-T005 (main): backend/app/{main.py (comment "Auth is stubbed (no JWT dep yet; T005)"), config.py, database.py, models/{user.py, crm_connection.py}, adapters/crm/* (CrmClient factory), api/__init__.py}
- Backend post (worktree): updated main.py (get_current_user + protected push), config.py (JWT_SECRET + DEMO_AUTH_TOKEN), requirements.txt (+python-jose)
- TS/web pre/post: src/crm/*, src/tool.ts, src/index.ts, web/src/* (App.tsx, stores/appStore.ts with "Stub auth (no real JWT)", api/client.ts with "?token" + "JWT will go here later T005+", components using demoToken/isLoggedIn)
- Prior reviews: REVIEW_FOR_BACKEND_SKELETON.md (flagged auth stub + token injection open Q), REVIEW_FOR_WEB_SKELETON.md, REVIEW_FOR_T003.md etc.
- Supporting: docker-compose.yml, .env.example, package.json (root+web), git worktree/status/diff, python AST + string verification (3.12), npm build/tsc (TS side).

**Monitoring actions** (repeated polls):
- `git worktree list`, `git status --porcelain`, `git diff --stat` + targeted diffs on wt.
- `tail/grep` on BUILD_COORDINATION.md (IDs + "T005" + "auth" + "JWT").
- File mtimes, ls on backend/app, repeated diff after changes detected.
- Confirmed src/ and web/src/ unchanged in both main and wt.

## Worktree State Observed
- Modified in worktree (post-T005 impl):
  - backend/app/main.py (large: added ~100 lines for security + get_current_user stub + push update)
  - backend/app/config.py (+ JWT_SECRET, DEMO_AUTH_TOKEN)
  - backend/requirements.txt (+ python-jose[cryptography])
- Unchanged: backend/app/adapters/crm/*, models/*, database.py, api/, docker-compose.yml, .env.example (no JWT_ added), src/*, web/*
- git HEAD in wt: post-web commits (no T005 commit yet).
- No changes whatsoever to TS (src/crm, tool, index) or web (src/*, stores, api/client, App, components) — 100% unaffected.
- BUILD_COORDINATION.md in wt: only Coordinator spawn note (Implementer did not append per "Information Sharing Rule").

## Review Criteria Applied
(From user directive, plan.md, tasks.md T005, ARCHITECTURE.md, data-model.md, prior skeleton notes, contracts):
1. Auth stub (token/JWT placeholder): YES. get_current_user + placeholder decode (stdlib .split base64 for JWT shape) + DEMO_AUTH_TOKEN + DEBUG fallbacks. Comments reference real Google + python-jose + HS256 later.
2. Protected dependency: YES. FastAPI HTTPBearer + Depends(get_current_user) returning minimal user dict (id/email/display_name) per data-model User.
3. /push update: YES. Signature now includes `current_user: dict = Depends(get_current_user)`, docstring updated, log with user email; CRM ?token logic + CrmClient calls untouched.
4. No breakage to CrmClient flow: YES. create_crm_client(provider, token) + full contact→deal(assoc)→3x task(cadence) + return shape identical. Auth check is orthogonal (CRM token separate from user JWT).
5. Alignment to plan/ARCH (server-side, stub for T006 vault): YES. Server-only (no secrets to client). JWT stub for user auth; CRM token resolution remains settings/?token (explicitly "separate from user JWT"; T006 vault will replace for per-user encrypted). Prepares for CrmConnection lookup using current_user.
6. Web/TS/demo flow compatibility: YES (DEBUG fallback when no Bearer header allows existing web demoToken/?token calls to succeed without change).
7. Minimal + future-proof: python-jose added to reqs (with comment); no full /auth/google/login/me or DB user lookup yet (stub per "T005" scope in coord); no impact to adapters or orchestration.
8. Security notes respected: no client secrets, WWW-Authenticate headers, DEBUG-only looseness documented.

## Verdict: **PASS** (high quality stub implementation; ready for feedback incorporation + tester; minor polish items)

Strong alignment:
- Exactly delivers "auth stub (token/JWT placeholder), protected dep, /push update".
- CrmClient flow pristine (verified via AST + string match + prior sim patterns).
- Server-side only; stub nature for T006 vault explicit.
- Web stub (demoToken + ?token CRM) continues working in DEBUG (critical for no-regression).
- TS/web 100% unaffected (builds clean; zero source edits).

Minor findings (non-blocking for T005 slice; low risk):
- No new router files or /me/login endpoints (tasks.md lists "login, /me"; coord scoped to "simple auth... protected deps, /push update" — this slice satisfies the latter).
- Placeholder JWT decode is a stdlib hack (no signature verify, manual padding) — acceptable for stub but could use jose early for the decode path.
- DEBUG fallback is very permissive ("any non-empty token in debug") — convenient but document risk.
- .env.example, docker-compose, and main .env not updated for JWT_SECRET/DEMO_AUTH_TOKEN (should propagate for dev).
- Implementer did not append mandatory coord summary entry.
- Health check remains open (intentional; only /push protected).
- current_user logged but not yet used to select CRM creds (correct for stub; T006/T008 will).

All mandatory criteria passed at high fidelity. No breakage. Builds/typechecks green on TS side.

## Concrete Findings + Issues (with patches)

**#1 Add JWT/DEMO vars to .env.example (and comment in docker-compose) for discoverability**
Current .env.example has "# Future placeholders (T005+)" section but no actual keys. Devs running docker will not see JWT_SECRET.

Suggested patch (edit main workspace after sync or instruct Implementer):
```diff
# file_path: .env.example
# after the HUBSPOT line and before "# Future placeholders..."
+JWT_SECRET=change-me-in-prod
+DEMO_AUTH_TOKEN=demo-stub-jwt
+
 # Future placeholders (T005+)
 # JWT_SECRET=change-me
 # ...
```

Also update docker-compose.yml env section similarly (non-blocking).

**#2 Minor: make get_current_user accept optional demo_auth Query for explicit testing (parity with early diff) + tighten non-DEBUG**
Current sig omits the query fallback variant. Web/testers may want ?demo_auth=... without header.

```diff
# file_path: backend/app/main.py  (inside get_current_user def)
-async def get_current_user(
-    credentials: HTTPAuthorizationCredentials | None = Depends(security),
-) -> dict[str, Any]:
+async def get_current_user(
+    credentials: HTTPAuthorizationCredentials | None = Depends(security),
+    demo_auth: str | None = Query(default=None, include_in_schema=False),
+) -> dict[str, Any]:
     ...
     token = credentials.credentials if credentials else None
+    if not token and demo_auth:
+        token = demo_auth
```

(Keep the rest; this makes ?demo_auth explicit for protected route testing while preserving header priority.)

**#3 Use python-jose for the placeholder decode path (now that dep is present) for better fidelity to future**
Instead of stdlib hack, import and use (with try/except for when not installed or stub mode).

Patch sketch:
```diff
# file_path: backend/app/main.py
+try:
+    from jose import jwt as jose_jwt
+except Exception:
+    jose_jwt = None
...
-    # Attempt placeholder JWT decode (stdlib...)
-    try:
-        parts = token.split(".")
-        ...
+    if jose_jwt is not None:
+        try:
+            payload = jose_jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"], options={"verify_signature": False})
+            ...
+        except Exception as e:
+            ...
```

(Still no sig verify in stub; but consistent.)

**#4 Implementer process: append to BUILD_COORDINATION.md in wt**
Per mandatory rule (see top of file and all prior agent entries):
Add block like:
```
**2026-07-14 [Implementer T005 ID 019f5d9f-59b1-7ec3-9544-4d634c8882ad]**
T005 COMPLETE. Delivered auth stub in backend/app/main.py (get_current_user protected dep + placeholder JWT + DEBUG fallback), config.py (JWT_SECRET/DEMO), requirements (python-jose). Updated /push to require auth while preserving exact CrmClient contact/deal/3task flow + ?token CRM. No TS/web edits. Builds green. See diff for decisions (separate user JWT vs CRM token, DEBUG compat for web stub, stdlib placeholder for skeleton).
Files touched: backend/app/main.py, config.py, requirements.txt
```

**#5 (Optional polish) Add a minimal health note or /me stub route**
Not required, but easy win for "login/me" spirit:
```python
@app.get("/api/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user, "note": "T005 stub"}
```

## Actions Taken
- Mandatory full re-reads of coord + specs + ARCH + backend pre/post + web stubs + prior REVIEWs at start and on change detection.
- Worktree monitoring via repeated git/fs/poll + targeted diff extraction.
- AST parse + string verification (3.12) + logic presence checks for Crm flow preservation.
- TS build (`npm run build`, `npx tsc --noEmit`) confirmed clean on main (no breakage).
- Python source checks (no runtime full deps needed for skeleton).
- Created this REVIEW_FOR_T005.md (full protocol, criteria checklist, verdict, 5 findings + patches, recs).
- This detailed log will be appended to BUILD_COORDINATION.md (main).
- No source edits performed (reviewer role only; patches are guidance).

## Recommendations
- **Implementer**: Apply #1 (env), #2 (demo_auth), #3 (jose import) or equivalent polish in wt. Append the required coord summary entry (exact "What I built", "Files touched", "Decisions made" e.g. "DEBUG fallback for web compat", "CRM token ?token kept orthogonal", "stdlib placeholder", open Qs). Re-verify python syntax + that web demo still hits /push successfully via current DEBUG path. Rebuild if needed.
- **Coordinator**: After impl polish + append, sync wt backend/ changes to main. Update tasks.md T005 check. Spawn or continue Tester (ID 019f5d9f-7256-7f11-8325-7d611fc73f87).
- **Tester**: Re-verify: python syntax, /health still open, /push returns 401 without token in non-DEBUG, succeeds with DEMO_AUTH_TOKEN or DEBUG fallback; full CrmClient 1+1+3 exercised same as pre; web composer push still works (no header change); no TS impact; prepare for real JWT header later.
- **Web (future, not now)**: When T005 real, update web/api/client.ts to send Authorization: `Bearer ${jwt}` (keep ?token for CRM provider token). Store stub JWT from login. But per directive: ensure unaffected now.
- **Open clarifs carried**:
  - Exact timing for full Google OAuth callback + real /auth routes vs this stub.
  - When current_user drives CRM token decrypt (T006) vs query/env.
  - Python contract still in specs/ vs backend copy.
  - Sandbox tokens for T020 (now auth-protected calls will need valid Bearer or DEBUG).

**Files by this agent**: REVIEW_FOR_T005.md (created), BUILD_COORDINATION.md (append only).  
**Timestamp**: 2026-07-14. All instructions + mandatory protocol followed. T005 criteria satisfied with high quality. Re-read everything before future action.

**TS/Web note (explicit)**: Confirmed zero edits to src/ or web/. Stub compat via DEBUG path preserved. MCP Bitrix flow untouched. CrmClient abstraction respected.
