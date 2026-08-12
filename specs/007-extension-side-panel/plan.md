# Implementation Plan: Extension Side Panel Workspace

**Branch**: `ai-bd-assistant` | **Date**: 2026-08-12 | **Spec**: `specs/007-extension-side-panel/spec.md`

## Summary

Replace the cramped 500px toolbar popup with a docked, resizable **Chrome Side Panel** workspace that
persists while the user browses. `popup.html` is rebuilt as a thin launcher. Along the way: extract
shared design tokens so every extension screen matches the web dashboard, add on-demand page capture
via `chrome.scripting`, and replace the hand-pasted JWT with real Google sign-in through
`chrome.identity.launchWebAuthFlow` → the backend's existing `POST /api/auth/google`.

No build step is introduced. No API contract changes. No backend code changes.

## Architecture

```
                          ┌──────────────── Chrome ────────────────┐
  toolbar click ──▶ popup.html  (thin launcher)                    │
                      │  · Open panel  · sign-in state  · API dot  │
                      │  · settings / dashboard links              │
                      │                                            │
                      ▼ chrome.sidePanel.open({windowId})          │
                   sidepanel.html  ◀── docked right, resizable ────┤
                      │  lead form · [Grab from this page]         │
                      │  AI preview (snapshot/opener/3 follow-ups) │
                      │  sticky action bar: [Generate] [Push]      │
                      └────────────────────────────────────────────┘
                          │                    │                │
      chrome.scripting ───┘                    │                └─── chrome.storage.session
      (activeTab, on demand)                   │                      (lead draft)
                                               │
                              extension page ⇒ host_permissions
                                     ⇒ NO CORS involvement
                                               │
                                               ▼
                          POST /api/leads/enrich      (contract UNCHANGED)
                          POST /api/leads/push?provider=…  (contract UNCHANGED)
                          POST /api/auth/google  ◀── id_token from launchWebAuthFlow
                          GET  /api/auth/me      ◀── session validation
```

**Why the panel and not a content-script drawer**: a side panel is an extension page, so
`host_permissions` covers its fetches and the empty-by-default `CORS_ORIGINS` never applies. A
content script runs at the *page* origin and would be blocked, forcing a service-worker proxy — and
it would still lose all state on every navigation. Full comparison in `research.md` R-001.

## Tech Stack

| Concern | Choice | Notes |
|---|---|---|
| Workspace surface | `chrome.sidePanel` | **Chrome 116+** (`open()`, not the 114 of the API itself) |
| Launcher | existing `action.default_popup` | popup wins over `openPanelOnActionClick`; open panel explicitly |
| Sign-in | `chrome.identity.launchWebAuthFlow`, `response_type=id_token` | reuses the **web app's** client ID |
| Page capture | `chrome.scripting.executeScript` + `activeTab` | on demand only, no persistent content script |
| Draft state | `chrome.storage.session` | memory-backed, cleared on browser close |
| Styling | `extension/tokens.css` | values mirrored from `web/src/index.css` |
| Module system | classic scripts exposing globals | same pattern as today's `config.js`; **no bundler** |

## Key constraint discovered

`backend/app/api/auth.py:160-164` verifies the Google ID token against a **single** audience,
`settings.GOOGLE_CLIENT_ID`. The extension must therefore obtain an ID token minted for that *same*
client ID — so it reuses the web app's OAuth client rather than registering its own. The only
external change is a Google Cloud Console entry adding
`https://<EXTENSION_ID>.chromiumapp.org/` as an authorized redirect URI. **No backend code changes.**

This also means the extension ID must be stable, which requires pinning a `"key"` in `manifest.json`
for unpacked loads. See `quickstart.md`.

## Second constraint discovered: the extension is currently broken, not merely drifted

`backend/app/api/auth.py:63-70` — `get_current_user_api` now raises 401 whenever the `Authorization`
header is absent ("Debug fallback removed per review (no silent stub users in production)"). Both
`/api/leads/enrich` and `/api/leads/push` depend on it.

`extension/popup.js:135-137` and `:178` still assert the opposite in comments — "backend falls back
to a DEBUG stub user when no Authorization header is sent" — and treat the token as optional. That
assumption expired when the stub was removed. **With no token pasted, every Generate and Push from
the extension returns 401 today.**

Consequence for this plan: sign-in (FR-008..FR-011) is not an optional cleanup that could be deferred
behind the UI work — it is what makes the new surface function at all. Tasks are ordered so auth
lands before the panel's generate/push path is verified, and the stale comments are deleted rather
than carried forward.

## File plan

| File | Action | Notes |
|---|---|---|
| `extension/tokens.css` | **new** | tokens + base components; upstream noted as `web/src/index.css` |
| `extension/auth.js` | **new** | `BDAuth`: sign-in, sign-out, session read, `authHeaders()` |
| `extension/lead-api.js` | **new** | `BDApi`: `enrich`/`push`/`health`; sole owner of the API contracts |
| `extension/capture.js` | **new** | `BDCapture.fromActiveTab()`; injected extractor + merge policy |
| `extension/sidepanel.html` | **new** | the workspace markup + panel-specific CSS |
| `extension/sidepanel.js` | **new** | form, preview render, generate/push, draft persistence |
| `extension/manifest.json` | edit | `+sidePanel/identity/scripting` perms, `side_panel`, `commands`, `key`. **Never `version`.** |
| `extension/background.js` | edit | panel registration, context menu, command handler |
| `extension/config.js` | edit | `GOOGLE_CLIENT_ID`, OAuth constants, new storage keys |
| `extension/popup.html` | rewrite | thin launcher; drop inline `:root`, use `tokens.css` |
| `extension/popup.js` | rewrite | open panel, show session + API state |
| `extension/options.html` | edit | restyle; paste-token UI → sign-in UI |
| `extension/options.js` | edit | wire `BDAuth`; remove the paste path |

`extension/icons/*` untouched. Nothing outside `extension/` and `specs/007-*` is modified.

## Permissions delta

| Permission | Why | Narrower alternative rejected |
|---|---|---|
| `sidePanel` | required to declare/open the panel | none exists |
| `identity` | `launchWebAuthFlow` for Google sign-in | none exists |
| `scripting` | on-demand extraction from the active tab | content script would need broad host access |

`activeTab` and `storage` are already present. **No new `host_permissions`** — notably no
`<all_urls>`; capture rides on `activeTab`'s gesture-scoped grant (NFR-004).

## Constitution Check

No `.specify/memory/constitution.md` exists in this repository, so the gates below are the repo's
standing conventions, taken from the spec's non-functional requirements and `CHANGELOG`/`Makefile`
practice.

| Gate | Status | Evidence |
|---|---|---|
| Buildless extension preserved | PASS | no bundler/transpiler; classic scripts only (R-005) |
| API contracts unchanged | PASS | request/response shapes centralised in `lead-api.js`, copied verbatim from `popup.js` |
| Preview shape unchanged | PASS | `company_snapshot`, `personalized_opener`, `follow_ups[3]` |
| Skill content stays server-side | PASS | no skill text read, embedded, or shipped |
| Least privilege | PASS | 3 permissions, each justified; no new host permissions |
| No XSS surface | PASS | all API/page/user content set via `textContent`; no `innerHTML` with interpolation |
| Version not hand-edited | PASS | `manifest.json` `version` untouched (R-009) |
| Backend tests / web build green | PASS by construction | no backend or `web/` files modified |

**Post-design re-evaluation**: unchanged. The design adds no backend dependency; the one external
requirement (an OAuth redirect URI) is configuration, documented rather than coded.

## Risks

| Risk | Mitigation |
|---|---|
| Google restricts implicit `id_token` for Web clients | Fallback: additive backend `extra_audiences` setting. Not planned work; documented in R-003 |
| Unpacked extension ID changes → redirect URI breaks | Pin `key` in manifest; `quickstart.md` documents generating it |
| Chrome < 116 | Feature-detect `sidePanel.open`; popup degrades with a notice (R-007) |
| Concurrent session touching the repo | Peer confirmed it is done with `extension/` and will not touch `specs/007-*` |

## Phases

- **Phase 0** — research → `research.md` (complete)
- **Phase 1** — design → `data-model.md`, `contracts/`, `quickstart.md` (complete)
- **Phase 2** — tasks → `tasks.md` via `/speckit-tasks`
- **Phase 3** — implement → agent loop, sequenced by file overlap; then load unpacked and drive it

## Tasks

See `tasks.md`.
