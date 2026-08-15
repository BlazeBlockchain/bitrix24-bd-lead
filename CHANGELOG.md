# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-15

### Added
- **Design system applied across every surface** — the web app, the extension side panel, the
  launcher popup, and the options page now render the `docs/design/` visual language:
  near-black navy (`#05070d`), translucent glass panels, hairline borders, the 8/10/14/18 radius
  ramp, and self-hosted Inter + JetBrains Mono.
- `design/tokens.css` — a single tracked upstream for every design token, with
  `scripts/sync_design_tokens.py` generating the token blocks in `web/src/index.css` and
  `extension/tokens.css`. `make check-tokens` fails on drift *and* on any reappearance of the
  retired palette, so the two files can no longer diverge unnoticed.
- `design/mark.svg` + `scripts/build_icons.py` — the real logo mark (a bolt on the brand gradient)
  and a rasterizer that drives headless Chrome to produce `extension/icons/{16,48,128}.png`. No npm,
  no ImageMagick, and no build step added to `extension/`. `make build-icons` / `make check-icons`.
- **A close control in the side panel**, in the footer as a labelled "Close panel" action —
  deliberately not an X in the top-right, where Chrome renders its own close control.
- `action.default_icon` in `extension/manifest.json`, so the toolbar and the side-panel header
  resolve the real artwork instead of a generated placeholder.
- **Inert brief sections** — buying signal, contact confidence, outreach email and CRM entry now
  appear in the designed visual language but are explicitly labelled unavailable. They are never
  filled with invented values, and never use a spinner or skeleton that would imply data is coming.
- Self-hosted `Inter` and `JetBrains Mono` woff2 in `extension/fonts/` and `web/public/fonts/`, so
  no surface fetches a font from a third-party CDN.
- `specs/009-enrich-brief-parity/` — a plan (spec, plan, contract) for filling the four brief sections
  that ship inert, by widening the enrichment output contract additively.

- **Browser extension: Chrome Side Panel workspace** (`extension/sidepanel.html`, `sidepanel.js`).
  The lead form and AI preview now live in a docked, resizable panel that stays open while you
  browse, replacing the 500px toolbar dropdown that Chrome dismissed on any outside click. Requires
  **Chrome 116+** (`chrome.sidePanel.open()`); the popup degrades with an explanatory notice below
  that. Form values and the generated preview survive page navigation and tab switches.
- **Real Google sign-in** via `chrome.identity.launchWebAuthFlow` (`extension/auth.js`), exchanged
  for a backend JWT through the existing `POST /api/auth/google`. Reuses the web app's OAuth client
  ID, because `verify_oauth2_token` pins a single audience — so this needed **no backend change**.
  One-time setup: register `https://<EXTENSION_ID>.chromiumapp.org/` as an authorized redirect URI
  and enter the client ID on the options page. See `specs/007-extension-side-panel/quickstart.md`.
- **"Grab from this page"** — on-demand page capture (`extension/capture.js`) via `chrome.scripting`
  against the active tab, prefilling company, signal, and source URL. Best-effort metadata
  heuristics; prefilled values stay editable and never overwrite existing input without confirmation.
  Contact name and role are deliberately never inferred.
- `extension/tokens.css` — design tokens and component classes shared by every extension screen,
  mirrored from `web/src/index.css`, replacing the `:root` blocks that were duplicated inline in
  `popup.html` and `options.html`.
- A pinned `key` in `extension/manifest.json`, so the unpacked extension ID is stable and the OAuth
  redirect URI does not break on reload.

### Changed
- **The brand accent is now the iris to violet to cyan gradient** (`#4a7cff` -> `#7c5cff` ->
  `#22d3ee`), replacing the orange `#f97316` on GitHub-dark `#0d1117`. The retired values are
  actively guarded against by `make check-tokens`. Note that `docs/UI_UX.md` still describes the old
  theme and is no longer the visual source of truth.
- The web app's header navigation is replaced by the design's 232px sidebar shell.
- `docs/extension-store.md` now points at the real `design/mark.svg` and the `make build-icons`
  workflow, instead of the orange placeholder SVG it used to embed.
- Buttons use a dedicated `--grad-btn` that stops at the violet. The full `--grad` ends in cyan,
  where white label text falls to a 1.81 contrast ratio and is effectively unreadable.
- The design handoff bundle moved from an untracked `design_handoff_bd_lead/` in the repo root into
  **`docs/design/`**, and is now tracked.
- `docs/UI_UX.md` carries a banner stating it is not the visual specification; its stale token block
  is replaced by a pointer to `design/tokens.css`, and its extension-surfaces section now describes
  the shipped side panel rather than the superseded compact-composer popup.
- Speckit skill frontmatter tiered by cost: the five `git-*` wrappers run on `haiku` with tools
  scoped to `Bash, Read`; `checklist`, `clarify`, `constitution` and `taskstoissues` run on `sonnet`;
  `specify`, `plan`, `tasks`, `analyze` and `implement` keep the session model. Skills that write to
  git, create GitHub issues, or edit code are now user-invocable only.

- The toolbar popup is now a **thin launcher** — open the panel, session state, backend reachability,
  and links out. The lead form and preview rendering moved to the side panel.
- Options page replaces the hand-pasted JWT with Google sign-in, and adds fields for the Google
  client ID and the (read-only, copyable) redirect URI. "Clear all data" now warns that it also
  clears the stored client ID.
- Preview rendering rebuilt with DOM construction instead of `innerHTML` string concatenation plus a
  manual escape helper, so escaping cannot be forgotten on a future field.
- New permissions: `sidePanel`, `identity`, `scripting`, `contextMenus`, `tabs`. **No new static host
  permissions** — page capture requests one origin at a time via `optional_host_permissions`, which
  produces no install-time warning. (`activeTab` alone is not enough: Chrome grants its host access
  only from the toolbar action, a context menu, or a keyboard shortcut — never from a button inside
  the side panel.)
- Extension body text raised to the dashboard's 15px base; the old 10-11px preview text is gone.

### Fixed
- **The API status dot never went green.** Both `lead-api.js` and `popup.js` probed the backend with
  `HEAD /api/health`, but the route only allows `GET`, so every check returned 405 — reporting the
  backend as unreachable and logging a console error on every panel and popup open. Now uses `GET`.
- Sub-12px text in the web app (`UsageView`, `HistoryList`, `MemoryProfile` each rendered 11px), and
  the hard-coded orange focus ring left in `sidepanel.html`.
- `web/public/favicon.svg` was still unmodified Vite/Tessl template artwork; it now carries the
  product mark.

- **The backend could never reach a real LLM under Docker.** `docker-compose.yml` passed no
  `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` to the backend service, so `generate_enrichment` fell
  through Gemini → Claude → `_mock_generate` and every preview was `model_used: "mock-llm"`,
  regardless of what was set in `.env`. Both SDKs were installed in the image; only the env
  passthrough was missing. Also passes `GEMINI_MODEL`, `ANTHROPIC_MODEL`, and
  `LLM_DAILY_BUDGET_CENTS` so they are tunable without a rebuild.
- **The extension could not authenticate at all.** `get_current_user_api` dropped its DEBUG stub-user
  fallback and now returns 401 whenever the `Authorization` header is absent, but `popup.js` still
  documented that fallback as live and treated the token as optional — so every Generate and Push
  returned 401 unless a JWT had been pasted by hand. Sign-in now supplies a real token.
- Corrected three README claims that the web app and extension "fall back to a stub demo user",
  including one in the setup instructions that led new users straight into an unexplained 401.
- `background.js` no longer logs every incoming message payload, which would have written
  credentials to the console once auth traffic existed.

## [0.1.3] - 2026-08-12

### Changed
- Moved the Changelog link out of the header nav into the footer, placed after the app version
- Decluttered the footer: removed the duplicate "BD Lead" brand (already the header logo), the
  "Google OAuth" implementation-status note, and a placeholder "docs" link that pointed at the
  generic github.com homepage instead of any real documentation

### Removed
- Per-task `REVIEW_FOR_*.md` / `TEST_REPORT_*.md` build artifacts under `specs/004-ai-bd-assistant/`
  — superseded by `docs/BUILD_COORDINATION.md` and the per-task notes in `tasks.md`, and partly
  stale (several described worktree code that never merged). Recoverable from git history.

### Fixed
- Stopped tracking 25 `.pyc` build artifacts that `.gitignore` already declared ignored, which kept
  the working tree permanently dirty
- Added `.env.staging` / `.env.production` to `.gitignore` (with `!*.example` negations) — the
  staging compose override expects a `.env.staging` holding DB credentials and `ENCRYPTION_KEK`,
  which could previously have been committed by accident

### Added
- Real PNG extension icons (16/48/128), replacing an inline SVG data URI that the Chrome Web Store
  does not accept and that provided no larger sizes


## [0.1.2] - 2026-07-14

### Added
- Full Google OAuth authentication (`POST /api/auth/google` + `GET /api/auth/me`)
- Frontend Google Sign-In via Google Identity Services (GIS) library
- Shared `get_current_user_api` auth dependency in `backend/app/api/auth.py` (single canonical implementation, replaces 4x duplication)
- JWT token issuance and verification with `python-jose` (HS256, short-lived tokens)
- `googLe-auth` library for server-side Google ID token verification
- `VITE_GOOGLE_CLIENT_ID` build arg for web Dockerfile
- User lookup/creation in `users` table on Google sign-in
- CORS origins now configurable via `CORS_ORIGINS` env var (restricted from wildcard)
- `web/src/api/auth.ts` — auth-specific API client (token storage, exchange, user fetch)
- `web/src/components/LoginPage.tsx` — login page with Google sign-in button
- `web/src/components/GoogleLoginButton.tsx` — Google Identity Services integration component
- `web/src/google-types.d.ts` — TypeScript declarations for GIS library
- `web/.env.example` with VITE_GOOGLE_CLIENT_ID documentation
- `__pycache__/`, `*.pyc`, `.venv/` patterns to root `.gitignore`

### Changed
- `backend/app/services/token_vault.py` — removed DEBUG fallback that bypassed encrypted vault (fail-closed per review A2)
- `backend/app/adapters/crm/__init__.py` — removed vault-resolve settings fallback in factory
- `backend/app/services/token_vault.py` — removed DEBUG ciphertext fallback in `decrypt_credentials`
- `specs/004-ai-bd-assistant/spec.md` — synced to reflect Python FastAPI reality (resolved language, Next.js, pricing open questions)
- All 4 API routers (`leads.py`, `connections.py`, `memory.py`, `usage.py`) — removed duplicated auth code, import shared dependency
- `backend/app/config.py` — added `GOOGLE_CLIENT_ID`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` settings
- `backend/app/main.py` — added auth router, restricted CORS from wildcard to configurable origins
- `docker-compose.yml` — added `GOOGLE_CLIENT_ID`, `JWT_SECRET`, `CORS_ORIGINS` env vars; added `VITE_GOOGLE_CLIENT_ID` build arg for web service
- `web/src/api/client.ts` — all protected API calls now include `Authorization: Bearer <jwt>` header
- `web/src/stores/appStore.ts` — replaced stub `login()` with `setAuthFromToken()` for real JWT auth flow
- `web/src/App.tsx` — replaced stub sign-in/logout with real Google Sign-In; added `RequireAuth` guard component; added `/login` route
- `docs/ARCHITECTURE.md` — updated status, Google Auth section with implementation details, resolved decisions
- `.env.example` — documented `GOOGLE_CLIENT_ID` and updated JWT section

### Fixed
- DEBUG vault bypass in `resolve_token` (A2) — no longer silently returns settings-based tokens
- 4x duplicated `get_current_user_api` code consolidated into single shared module
- CORS wildcard (`*`) restricted to configurable origins
- Token vault decrypt now fail-closed (no DEBUG ciphertext fallback)
- Factory vault-resolve fallback removed (fail-closed behavior)

## [0.1.1] - 2026-07-14

### Added
- Dockerized frontend (multi-stage node→nginx, SPA + /api reverse proxy)
- Staging compose override (isolated volume, container names, sub-path VITE_BASE)
- Makefile deploy targets (dev/up/down/build-web/logs/stop/clean/deploy-staging/deploy-prod)
- `.env.staging.example` documenting staging environment variables
- specs/006-docker-frontend-deploy feature spec kit
- Vite dev-server proxy for `/api` in development mode

### Changed
- `web/src/api/client.ts` derives base URL from `import.meta.env.BASE_URL` (same-origin)
- Web footer no longer hardcodes backend URL
- README.md: new Deployment section with full-stack/dev/deploy commands
- docs/ARCHITECTURE.md: dockerized nginx frontend topology documented
- `docker-compose.yml`: added bdlead-web service (nginx on port ${WEB_PORT:-8080}:80)
- New DB models: lead, outreach_history, usage_ledger, user_memory_profile
- Web components enhanced: Composer, HistoryList, Preview, store improvements

### Fixed
- Dockerfile build context corrected (was using root package.json instead of web/)
- docker-compose.staging.yml: removed obsolete `version` attribute


## [0.1.0] - 2026-07-14

### Added
- Fresh MV3 browser extension with auth-optional enrich and push flows
- Leads API router with full CRUD operations
- Leads detail endpoint with enriched preview data
- Async usage ledger persistence and tracking
- Connections page with real backend endpoints for multi-tenant CRM credential storage
- Encrypted credential storage for multi-tenant security (CRM token vault)
- Memory profile editor with tone_samples injection into LLM prompt
- Usage ledger API endpoints with admin views for cost tracking
- Dashboard integration with real connections, usage, and history data
- LLM proxy service with Gemini 2.5 Flash primary and Haiku fallback
- Comprehensive pytest test suite (68+ tests covering adapters, factory, and services)
- Docker Compose setup with PostgreSQL and healthcheck verification
- Full CRM adapter implementations for Bitrix24 and HubSpot

### Changed
- Resolved database migration crash-loop issues
- Updated Docker healthcheck for e2e testing reliability
- Migrated backend to fully async SQLAlchemy patterns
- Enhanced authorization with per-user tenancy validation across all endpoints
- Improved error handling and logging throughout LLM and CRM services

### Fixed
- Multi-tenant security fix for connections endpoints (user isolation)
- Database migration initialization and schema versioning
- Docker container startup and health verification
- FastAPI dependency injection for encrypted token vault
