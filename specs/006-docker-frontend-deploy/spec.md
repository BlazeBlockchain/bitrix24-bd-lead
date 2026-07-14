# Feature Specification: Dockerize Frontend + Deployment

**Feature Branch**: `ai-bd-assistant`
**Created**: 2026-07-14
**Status**: Complete
**Input**: Plan from `~/.claude/plans/velvet-growing-gray.md`

## User Story

As a developer, I want the frontend containerized and the full stack deployable via Docker Compose so that:
- Dev: `docker compose up --build` starts the full stack (db + backend + web)
- Prod: nginx serves the SPA and reverse-proxies `/api` to the backend (no CORS)
- Staging: isolated environment with override compose file
- Deploy: `make deploy-staging` / `make deploy-prod` via SSH

## Requirements

### Functional

- **FR-001**: Web frontend MUST be served by nginx in a Docker container (multi-stage: node build → nginx serve)
- **FR-002**: nginx MUST serve the SPA with `try_files` fallback for client-side routing
- **FR-003**: nginx MUST proxy `/api/*` requests to the backend service
- **FR-004**: Vite dev server MUST proxy `/api` to localhost:8000 for native development
- **FR-005**: The API client (`client.ts`) MUST derive base URL from `import.meta.env.BASE_URL` for same-origin calls
- **FR-006**: The Docker Compose MUST include all three services (db, backend, web)
- **FR-007**: A staging override compose file MUST isolate DB volume and container names
- **FR-008**: The Makefile MUST provide dev/build/deploy targets
- **FR-009**: A `.env.staging.example` MUST document staging environment variables

### Non-Functional

- **NFR-001**: Static assets MUST be cached with 1y immutable headers
- **NFR-002**: The nginx container MUST have a healthcheck
- **NFR-003**: The web service MUST restart unless stopped
- **NFR-004**: All existing version management (`make bump-*`, `make release`) MUST remain unchanged

## Success Criteria

- `docker compose up --build` starts all three services healthy
- `curl http://localhost:8080/` serves the SPA
- `curl http://localhost:8080/api/health` proxies to backend
- `npm run dev` in `web/` still works with Vite proxy
- `docker-compose.staging.yml` merges cleanly
- `make dev` / `make build-web` / `make logs` / `make down` all work
- `make version` still prints `0.1.0`
