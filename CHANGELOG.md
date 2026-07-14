# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
