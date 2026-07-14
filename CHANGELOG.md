# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-07-14

### Added
-

### Changed
-

### Fixed
-

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
