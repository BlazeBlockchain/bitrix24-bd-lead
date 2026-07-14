# Tasks: Dockerize Frontend + Deployment

**Input**: Plan from `~/.claude/plans/velvet-growing-gray.md`

## Stream 1 — Frontend container + compose + Makefile

- [x] **T036** Create `web/Dockerfile` — multi-stage node:20-alpine build → nginx:alpine serve with healthcheck
- [x] **T037** Create `web/nginx.conf` — SPA `try_files`, `/api` reverse proxy to backend, gzip, asset caching
- [x] **T038** Create `web/.dockerignore` — node_modules, dist, .env
- [x] **T039** Update `web/src/api/client.ts` — use `import.meta.env.BASE_URL` derived same-origin `/api`
- [x] **T040** Update `web/vite.config.ts` — add `server.proxy` for `/api` → localhost:8000
- [x] **T041** Update `web/src/App.tsx` — footer no longer hardcodes backend URL
- [x] **T042** Update `docker-compose.yml` — add `bdlead-web` service with nginx config
- [x] **T043** Create `docker-compose.staging.yml` — isolated volume, container name suffixes, sub-path VITE_BASE
- [x] **T044** Update `Makefile` — add dev/up/down/build-web/logs/stop/clean/deploy-staging/deploy-prod targets (preserving existing version targets)
- [x] **T045** Create `.env.staging.example` — document staging environment variables

## Stream 2 — Docs + Speckit

- [x] **T046** Update `README.md` — add Deployment section with dev/deploy commands and nginx proxy architecture
- [x] **T047** Update `docs/ARCHITECTURE.md` — add dockerized frontend topology, nginx reverse proxy, compose services table
- [x] **T048** Create `specs/006-docker-frontend-deploy/` — spec.md, plan.md, tasks.md

## Verification

- [ ] **T049** Verify `docker compose up --build` — all three services healthy, SPA serves at :8080, /api/health proxies correctly
- [ ] **T050** Verify `npm run dev` still works with Vite proxy
- [ ] **T051** Verify Makefile targets: `make help`, `make version`, existing bump targets remain functional
