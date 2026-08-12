# Phase 0 Research: Extension Side Panel Workspace

**Feature**: `specs/007-extension-side-panel` | **Date**: 2026-08-12

## R-001: Which persistent surface?

**Decision**: Chrome Side Panel API (`chrome.sidePanel`), with `popup.html` retained as a launcher.

**Rationale**:

| Criterion | (a) Side Panel | (b) Content-script drawer | (c) Expanded popup / tab |
|---|---|---|---|
| Persists across outside clicks | Yes | Yes | Tab: yes; window: yes but undocked |
| Persists across page navigation | Yes (panel is not part of the page) | **No** — re-injected, state lost | Yes |
| Docked beside the page | Yes, user-resizable | Overlays/covers page content | **No** — separate tab or floating window |
| CORS on API calls | **Bypassed** via `host_permissions` (extension page) | **Blocked** — page origin, and `CORS_ORIGINS` defaults to empty | Bypassed |
| CSS isolation work | None | Shadow DOM + host-page CSP fights | None |
| Buildless vanilla JS | Yes | Yes, but heavier | Yes |
| Browser support | Chrome/Edge 114+ | All | All |

The decisive factor is the interaction between gotchas: a content-script drawer loses its state on
every navigation *and* cannot call the API directly, because `backend/app/main.py:53` reads
`CORS_ORIGINS` with a default of `""`. Option (b) would therefore require a service-worker fetch
proxy plus a state-rehydration mechanism — significant machinery to end up with a surface that still
covers the page the user is reading. Option (c) does not dock, so it does not deliver the
side-by-side reading the user asked for.

A side panel is an extension page, so `host_permissions` grants it direct API access with no CORS
preflight involvement, and it keeps existing vanilla popup code essentially portable.

**Alternatives considered**: rejected as above. Firefox's `sidebarAction` is a different API and is
explicitly out of scope (spec A-001).

## R-002: How does the launcher open the panel?

**Decision**: Keep `action.default_popup = popup.html`. A primary button in the popup calls
`chrome.sidePanel.open({ windowId })`. Also register a context-menu item and a keyboard command.

**Rationale**: `chrome.sidePanel.open()` requires a user gesture, which a click inside the popup
satisfies. Note that `setPanelBehavior({ openPanelOnActionClick: true })` is mutually exclusive in
practice with `default_popup` — when a popup is declared, the popup wins and the behavior flag never
fires. Since the user chose to keep the launcher, we declare the popup and open the panel explicitly.

**Constraint**: `chrome.sidePanel.open()` landed in Chrome 116, later than the 114 that introduced
the API. The effective floor for this feature is therefore **Chrome 116+**, not 114. Recorded in the
plan's Technical Context, and feature-detected at runtime (R-007).

**Alternatives considered**: dropping `default_popup` and using `openPanelOnActionClick` — one fewer
surface, but the user explicitly chose to keep the launcher.

## R-003: Google sign-in without a build step, matching the existing backend

**Decision**: `chrome.identity.launchWebAuthFlow` against Google's OAuth 2.0 authorization endpoint
with `response_type=id_token`, reusing the **same** Google client ID as the web app, then
`POST /api/auth/google` with the resulting `id_token`.

**Rationale**: `backend/app/api/auth.py:160-164` calls
`google_id_token.verify_oauth2_token(body.id_token, ..., settings.GOOGLE_CLIENT_ID)`, which pins the
token's `aud` claim to exactly one client ID. Any extension-specific OAuth client would produce an
ID token with a different audience and be rejected with 401. Reusing the web client ID means **zero
backend code changes** (spec A-005 holds).

To make that work, `https://<EXTENSION_ID>.chromiumapp.org/` must be added as an authorized redirect
URI on the existing Google web OAuth client — a Google Cloud Console configuration step, not a code
change. `chrome.identity.getRedirectURL()` returns exactly that URI.

**Implications and required setup**:
- The extension ID must be **stable**, or the redirect URI changes on every reload. For an unpacked
  extension this requires pinning a `"key"` in `manifest.json`. Documented in `quickstart.md`.
- `response_type=id_token` requires a `nonce` parameter. Generate it with `crypto.randomUUID()` and
  verify it round-trips in the returned token before accepting it.
- Scopes: `openid email profile`.
- The redirect returns the token in the URL **fragment**, not the query string.

**Risk**: Google has, in some configurations, restricted implicit `id_token` responses for Web
application clients. **Contingency if that surfaces**: add an `extra_audiences` setting to the
backend and accept a list in `verify_oauth2_token`. This is a small, additive backend change and is
noted as a fallback only — it is not part of the planned work, and it must not alter the response
shape of `/api/auth/google`.

**Alternatives considered**:
- `chrome.identity.getAuthToken` — Chrome-signed extensions only, returns an *access* token rather
  than an ID token, and requires a Chrome App OAuth client type. Wrong token type for this backend.
- Web-app handoff via `externally_connectable` — still requires the user to visit the dashboard, and
  the user rejected it.

## R-004: Page capture without a persistent content script

**Decision**: `chrome.scripting.executeScript` with an injected function, on demand, against the
active tab. Add the `scripting` permission; keep the existing `activeTab`.

**Rationale**: `activeTab` grants temporary host access to the current tab following a user gesture,
so no broad `<all_urls>` host permission is needed (NFR-004). Because injection happens only when the
user clicks capture, there is no always-on content script, no CORS exposure (the injected function
returns data and performs no network calls), and nothing persistent in the page.

**Extraction heuristics**, in priority order, all best-effort (spec A-004):
- Company: `og:site_name` → `application-name` meta → JSON-LD `Organization.name` → hostname minus
  public suffix, title-cased.
- Signal: user-selected text if present, else `og:description` / `meta[name=description]`, truncated.
- Notes / source: page title plus canonical URL.
- Contact and role are **not** guessed — too error-prone, and a wrong name is worse than a blank.

**Failure modes handled**: restricted URLs (`chrome://`, Web Store, PDF viewer, `file://` without
permission) throw on `executeScript`; catch and report "can't read this page" while leaving the rest
of the panel functional (spec edge case 1). If every heuristic misses, change nothing and say so
(edge case 2).

**Merge policy** (FR-007): prefill only empty fields by default. If fields already hold values, show
a non-destructive confirm listing what would be overwritten.

## R-005: Sharing code across popup, panel, and options without a bundler

**Decision**: Plain classic scripts exposing globals, loaded via `<script src>` in dependency order —
the pattern `config.js` already uses. No ES modules, no bundler.

**Rationale**: NFR-001 forbids a build step. Classic scripts keep `background.js` as a non-module
service worker and avoid `"type": "module"` churn. New shared files:

| File | Exposes | Consumers |
|---|---|---|
| `tokens.css` | CSS custom properties + base component classes | all HTML |
| `auth.js` | `BDAuth.signIn/signOut/getSession/authHeaders` | panel, popup, options |
| `lead-api.js` | `BDApi.enrich/push/health` | panel |
| `capture.js` | `BDCapture.fromActiveTab()` | panel |

`lead-api.js` centralises the request shape so the enrich/push contracts live in exactly one place
(NFR-002), and centralises error classification into the three states FR-014 requires.

## R-006: Design token consolidation

**Decision**: Extract `extension/tokens.css` carrying the same custom properties as
`web/src/index.css`, and delete the duplicated `:root` blocks from `popup.html` and `options.html`.

**Rationale**: The extension already declares byte-identical values for `--bg`, `--surface`,
`--surface-2`, `--border`, `--text`, `--muted`, `--accent`, `--accent-2`, `--accent-3`, `--danger`,
`--radius`, `--font-sans`, `--mono` — duplicated inline in two HTML files. FR-015 asks for one
source. The base size moves from 13px (and 10-11px for preview text) to the dashboard's 15px/1.5,
satisfying NFR-008.

Values are copied, not imported: `web/src/index.css` is not reachable from the extension directory,
and the alternative — a build step to sync them — is forbidden by NFR-001. A comment in `tokens.css`
names `web/src/index.css` as the upstream source so drift is at least visible.

## R-007: Graceful degradation on unsupported browsers

**Decision**: Feature-detect `typeof chrome.sidePanel?.open === 'function'`. When absent, the popup
hides the "Open panel" button and shows a short notice naming the required Chrome version; the popup
keeps its own link out to the web dashboard so the user is not dead-ended.

**Rationale**: Spec A-001 and the "must not appear broken" edge case. Feature detection is preferred
over user-agent version parsing.

## R-008: State persistence across navigation and panel close

**Decision**: Keep the live lead draft in `chrome.storage.session`, written debounced on input and on
preview generation; clear it after a successful push.

**Rationale**: A side panel does not reload on page navigation, so in-memory state already survives
FR-005's main case. But the panel *is* torn down when closed and reopened, and `storage.session` is
memory-backed and cleared when the browser closes — which matches "within a browsing session"
exactly, and avoids persisting prospect data to disk. One draft per window, per spec A-003 and A-007.

## R-009: Version field

**Decision**: Do not touch `"version"` in `manifest.json`. Other manifest keys (`permissions`,
`side_panel`, `commands`, `key`) are edited freely.

**Rationale**: `scripts/sync_versions.py` generates it from the root `VERSION` file; use
`make bump-patch` if a bump is wanted. Independently confirmed by the concurrent session that just
released v0.1.3.

## Resolved unknowns

| Unknown | Resolution |
|---|---|
| Minimum Chrome version | 116 (not 114) — `sidePanel.open()` availability (R-002) |
| Which OAuth client ID | Reuse the web app's; backend pins a single audience (R-003) |
| Backend changes needed | None; only a Google Console redirect-URI entry (R-003) |
| Extension ID stability | Requires pinned `key` in manifest for unpacked loads (R-003) |
| New permissions | `sidePanel`, `identity`, `scripting` — justified in R-002/R-003/R-004 |
