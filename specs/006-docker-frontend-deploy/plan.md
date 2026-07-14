# Implementation Plan: Dockerize Frontend + Deployment

**Branch**: `ai-bd-assistant` | **Date**: 2026-07-14 | **Spec**: `specs/006-docker-frontend-deploy/spec.md`

## Summary

Containerize the React/Vite frontend behind nginx, add the web service to the existing Docker Compose, add staging override, and add deployment targets to the Makefile. The nginx container serves the SPA and reverse-proxies `/api` to the backend — eliminating CORS by using same-origin requests.

## Architecture

```
Browser ──→ bdlead-web:${WEB_PORT:-8080} (nginx:alpine)
                ├── /        → /usr/share/nginx/html (SPA)
                ├── /assets/* → immutable cache (1y)
                └── /api/*   → proxy_pass http://bdlead-backend:8000/api/
```

## Tech Stack

| Component | Image | Role |
|-----------|-------|------|
| Frontend build | node:20-alpine | npm ci → npm run build |
| Frontend serve | nginx:alpine | SPA + /api reverse proxy |
| Orchestration | Docker Compose v2 | 3-service stack on bbspace_net |
| Deploy | SSH + rsync + docker compose | make targets |

## Tasks

See tasks.md (T036+).
