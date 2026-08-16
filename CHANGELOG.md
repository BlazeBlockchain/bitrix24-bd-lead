# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.3] - 2026-08-16

Deployment release: what the team demo on the shared VPS needs in order to be reachable without
also being exposed. No change to enrichment, retrieval, or the CRM adapters.

### Added
- `AUTH_EMAIL_ALLOWLIST` — comma-separated full addresses (`rep@example.com`) or domains
  (`@example.com`), matched case-insensitively. Empty admits every Google account, which is right
  for a local checkout and wrong for anything reachable from the internet, where the daily cost
  guard would otherwise be the only thing between a stranger and the Gemini bill. The gate runs
  before the user row is created, so a refused address leaves no trace in `users`. When a list is
  configured it also requires Google's `email_verified` claim — a domain rule is only as
  trustworthy as the claim it matches on.
- `docs/DEPLOY.md` — the staging deploy end to end: the shared `bbspace_net` infrastructure it
  joins, the nginx location block, first-deploy prerequisites, the verification checklist, and an
  explicit "Not production" list. Records the outbound-egress requirement 010 introduced: the
  liveness probe `HEAD`s **arbitrary publisher domains**, so the container needs general HTTPS
  egress and not an allowlist of two Google hosts. Restricted egress makes citations vanish
  silently, with no error shown to the user.
- `GOOGLE_CLIENT_ID` in `.env.staging.example`, which it was missing entirely.

### Changed
- Deploy targets pull a branch on the server instead of rsyncing the working tree. rsync shipped
  whatever happened to be on the operator's disk, including uncommitted edits, so the running demo
  had no commit to point at. Pulling matches vanguard-game and makes the artifact reproducible.
- Compose publishes both ports on `127.0.0.1`. Local dev reaches `localhost:8000` and `:8080`
  exactly as before, but on a shared host the API is no longer an internet-facing FastAPI on port
  8000 bypassing TLS and the reverse proxy — the web container and the shared nginx stack already
  reach it over `bbspace_net`.
- Deploy passes `--env-file`. `env_file:` only injects variables into a running container; it does
  not feed `${VAR}` interpolation, and `VITE_GOOGLE_CLIENT_ID` is a **build arg** filled by
  interpolation. Without this the web bundle builds with an empty client ID and the Google sign-in
  button silently does nothing.
- `AUTH_EMAIL_ALLOWLIST`, `ENCRYPTION_KEK` and the `RETRIEVAL_*` kill switch are threaded through
  compose to the backend.

### Fixed
- The root logger had no handler, so every `logger.info` in app code was discarded. This was worse
  than silence: Python's lastResort handler still prints WARNING and above, so failures shouted
  while successes stayed quiet — exactly backwards for the `RETRIEVAL:` diagnostics, whose four
  outcomes (`found` / `empty` / `disabled` / `no_key`) are all INFO. A brief that lost its citation
  to blocked egress and a brief that correctly found nothing produced identical logs, which is the
  one distinction a deploy needs to make.
- SQL statements no longer log twice. `echo=settings.DEBUG` attaches SQLAlchemy's own handler to
  `sqlalchemy.engine`, which still propagates, so giving root a handler doubled every line.
  Propagation is muted only when echo is on — with echo off that logger has no handler of its own
  and cutting propagation would swallow SQLAlchemy's warnings.


## [0.2.2] - 2026-08-15

Feature 010 — a verifiable source for the buying signal. 009 made the buying-signal section real but
left `source` reading "reported in the lead brief" on 5 of 5 real leads: honest, and completely
uninformative, because it told the rep what they had typed. This adds live retrieval so the signal
carries links a rep can open.

Retrieval **relocates** the fabrication risk rather than removing it — the model can now cite a real
page that does not say what the brief claims, which is worse than no citation because the link looks
like proof. Most of the work below is defence against that, and every defence was added because live
testing produced the corresponding failure.

### Added
- `buying_signal.sources[]` — every source the grounded search actually leaned on, company's own
  domain first, `https` only, max 4. All of them render on both surfaces.
- `buying_signal.finding` — the grounded sentence attributed to those sources, and the same evidence
  text the enrichment model receives. Rendered as `Search found:`, never as a quotation: the API
  exposes spans of the model's own answer, not page text, so no page quote exists.
- `buying_signal.unverified_by_company` — an amber caution when no source is the company's own. Such
  a claim rests entirely on third parties who may be reporting each other.
- `buying_signal.search_suggestions` — Google's Search Suggestions block, rendered verbatim into a
  shadow root on both surfaces. The Gemini API terms require it wherever grounded results are shown
  and forbid modifying it, so it is server-checked and **refused rather than sanitised**; a refusal
  drops the whole citation. This is the one sanctioned `innerHTML` in the codebase, documented at
  both call sites. The shadow root keeps Google's unscoped `.container`/`.chip` CSS out of our layout
  — verified by breaking it on purpose.
- `backend/app/services/retrieval_service.py` — grounded Google Search as a pre-call, via REST on the
  existing `httpx` dependency. No new dependency.
- `RETRIEVAL_ENABLED`, `RETRIEVAL_TIMEOUT_SECONDS` (6s), and grounding list price in config.

### Changed
- Retrieval **verifies a claim about a named entity** rather than searching for news. Namesakes,
  subsidiaries, same-name entities in other jurisdictions and different events are mandatory
  rejections, and the verdict is a machine-checked `CONFIRMED:` prefix.
- Cited URLs are resolved from Google's redirect to the real publisher, then confirmed reachable and
  not bouncing off-host, so the link text is a publisher the rep recognises and the page opens.
- Retrieved text is fenced as untrusted input, placed last, delimiter-stripped, and scoped to the
  buying signal alone. The retrieval query carries company and signal only — no skill methodology.
- `max_output_tokens` 4096 → 8192. Evidence in the prompt lengthened responses past the old cap.
- A mock brief carries no citation at all.
- Backend suite 137 → 192; hermetic offline, verified with sockets poisoned and an API key set.

### Fixed
- A false signal ("Notion is filing for bankruptcy") cited a real federal court record for **"Get
  Notion, LLC"**, a different company — corroborating a false premise with official-looking
  evidence. Fixed by the verification framing above.
- Evidence in the prompt truncated the JSON mid-string, silently collapsing 3 of 7 leads to the mock
  — one of which paired a real court-records link with generic mock filler.
- A true Figma claim cited a URL that redirected to a broker's homepage with no mention of Figma.
- A Klarna citation asserted "Form F-1 … March 14, 2025" against a page carrying neither: the
  sentence was a synthesis across five sources and was attributed to one of them.

### Known
- **Google's Grounding with Google Search terms are only partly met.** Search Suggestions are now
  displayed as required. What remains is that resolving the grounding redirect to the publisher URL
  modifies the Link Google returned — kept deliberately, since the raw redirect hides the destination
  from the rep and defeats the point of the citation. Needs legal sign-off before real reps use this.
  See `specs/010-verifiable-signal-source/plan.md`.
- Source quality is uncontrolled where the company has no own-domain page in the results.
- Enrichment latency is now ~18s mean, ~23s max.


## [0.2.1] - 2026-08-15

Feature 009 — enrich/design parity. The four brief sections that 0.2.0 shipped inert now carry real
model output.

### Added
- **Buying signal, contact confidence, outreach email and CRM entry are populated.** 0.2.0 rendered
  these four as styled "not available yet" blocks, because fabricating a confidence pill would have
  contradicted the product's own trust principle. The gap was in the output contract, not the
  model's capability — `_build_prompt` already injected the full skill methodology and then asked
  for three fields, ending with "no extra keys". Widening that shape is the whole feature.
- **Anti-fabrication is now an explicit contract term.** The model is told to omit a source or a
  date it cannot support rather than guess, and never to complete a partial date. Server-side,
  `contact_confidence.level` is enum-validated, a signal dated in the future is dropped, and any
  field that fails validation is omitted so its section falls back to the 0.2.0 inert presentation.
  Absent, malformed and out-of-range are one case; nothing is ever derived client-side.
- **The outreach email is copyable in one action** from both the web app and the side panel.
- `LLM_PRICE_CENTS_PER_MTOK` in config — a per-model cost table, so a price change is a settings
  change rather than a code change, and an unpriced model is never silently free.

### Changed
- **The outreach email supersedes the "Suggested Opener" card** on both surfaces when one is
  present. Two different openings for the same lead invited sending a message that contradicted the
  one below it. `personalized_opener` is unchanged in the response and still builds the CRM deal
  comment; the card remains the email's fallback when no valid email was returned.
- Haiku's `max_tokens` 800 → 4096, matching Gemini. The widened contract would not fit in 800, which
  would have collapsed the fallback chain to mock on every Gemini failure.
- Enrichment costs roughly 12% more per lead (measured: input +14.8%, output +52.4%, total +11.7%,
  latency +0.8s). Output is the small half of this request — the skill methodology dominates the
  prompt — so the richer brief is cheap. Recorded in `specs/009-enrich-brief-parity/plan.md`.

### Fixed
- **The model fabricated signal dates.** A signal reading "hired a new CTO in March" — no year —
  produced `2024-03-15`, inventing both the year and the day. The server only rejected *future*
  dates, so a confidently-wrong past date passed. Partial dates must now be omitted, never
  completed.
- **The confidence pill was decorative.** Every lead scored `high`, including one whose signal was
  "something changed recently", with circular reasons ("Contact and role explicitly provided in the
  lead brief") — the model was assessing whether the form had been filled in. It now judges role fit
  against the pain point, and a brief too vague to judge yields `low`.
- **The usage ledger recorded fabricated token counts.** Every real call logged a hardcoded 400 in /
  250 out and a flat 1 cent, against a measured ~5,950 in / ~2,900 billable out — input
  under-recorded roughly 15×, leaving the daily budget guard watching a number unrelated to spend.
  Real provider counts are now recorded, priced from config, and accumulated as a float so that
  sub-cent calls actually move the total instead of rounding to zero.
- Both providers now log *why* they were skipped. An unset API key and a failing provider were both
  a bare `None`, which is how an empty `ANTHROPIC_API_KEY` went unnoticed.
- A missing f-string prefix emitted a literal `{signal_type}` to users on the mock path.


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
