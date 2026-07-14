# ARCHITECTURE: AI-Native BD Lead Assistant

**Project:** bitrix24-bd-lead  
**Status:** Draft (Phase 0)  
**Date:** 2026-07-13  
**Template:** Mirrors sibling `vanguard-game` (see `docs/architecture.md` and `docs/deploy.md` there) + guidance from `docs/development-options.md`

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Public / Marketing                       │
│   (bdlead.app landing, pricing, "Try it" demo without login) │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  Web App (React/Vite or Next.js)                             │
│  • Google OAuth login / signup                               │
│  • CRM Connections (Bitrix24 webhook / HubSpot OAuth)        │
│  • Lead Composer (paste + AI preview)                        │
│  • History + Memory profile                                  │
│  • Billing stub                                              │
└───────────────┬─────────────────────────────────────────────┘
                │  (same authenticated API)
┌───────────────▼─────────────────────────────────────────────┐
│  Browser Extension (MV3 - Chrome + Firefox)                  │
│  • Thin client: content script on CRM/LinkedIn tabs          │
│  • Popup composer (pre-fill where possible)                  │
│  • Calls same backend APIs + token from extension storage    │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│  Backend (VPS, Docker Compose)                               │
│  • Auth service (Google OAuth + JWT)                         │
│  • Per-user memory (Postgres + pgvector)                     │
│  • CRM token vault (envelope encryption per user)            │
│  • LLM proxy (Gemini Flash primary + Haiku fallback)         │
│  • CrmClient adapters (Bitrix24 + HubSpot v1)                │
│  • Lead orchestration + enrichment                           │
│  • Billing stubs / usage metering                            │
└───────────────┬───────────────────┬─────────────────────────┘
                │                   │
        ┌───────▼───────┐   ┌───────▼───────┐
        │  PostgreSQL   │   │     Redis     │
        │  (users,      │   │  (queues,     │
        │   leads,      │   │   cache,      │
        │   memory,     │   │   rate limits)│
        │   tokens)     │   └───────────────┘
        │  + pgvector   │
        └───────────────┘
                │
        ┌───────▼──────────────┐
        │  External Services   │
        │  • Google OAuth      │
        │  • Gemini API        │
        │  • Anthropic (Haiku) │
        │  • Bitrix24 REST     │
        │  • HubSpot v3 REST   │
        │  • Stripe (later)    │
        └──────────────────────┘
```

MCP server (current `src/`) remains as a thin stdio wrapper that reuses the same core orchestration and adapters.

---

## Tech Stack

| Layer          | Choice (v1)                              | Rationale / Notes |
|----------------|------------------------------------------|-------------------|
| Backend runtime| Python FastAPI (primary) + possible thin Node/Hono API layer | Matches vanguard-game (proven). Python excellent for AI orchestration workers. |
| Frontend (web) | React 18 + TypeScript + Vite (or Next.js if auth/billing simplifies) | Mirrors vanguard frontend. Zustand for state, Axios client reusable by extension. |
| Extension      | Manifest V3, TypeScript, Vite build      | Service worker + content scripts + popup. No heavy frameworks. |
| Database       | PostgreSQL 16 + pgvector                 | Structured + vector memory in one DB. Alembic migrations. |
| Cache/Queue    | Redis                                    | Rate limiting, background enrichment jobs, session if needed. |
| Auth (user)    | Google OAuth2 + JWT (short-lived)        | Lowest friction for non-technical SMB buyers. See "Google Auth" section. |
| CRM Auth       | Webhook (Bitrix) + OAuth2 (HubSpot)      | Tokens stored encrypted server-side. |
| LLM            | Gemini 2.5 Flash (primary) + Claude Haiku 4.5 (fallback) via server proxy | Cost target <$0.01/lead. Structured JSON outputs. T007 impl+tested (mocks, budgets, integration) complete. |
| Container      | Docker + docker-compose                  | Single VPS. External network (like bbspace_net). |
| CI/CD          | GitHub Actions or Gitea + SSH deploy     | Build, typecheck, compose up on VPS. |
| Observability  | Stdout + basic healthchecks + cost logs  | Per-user token budgets + LLM usage tracking from day 1. |

**No new top-level heavy frameworks** until after CrmClient refactor and backend split.

---

## Database Schema (High-Level Entities)

Full details will live in Speckit `data-model.md`. Initial entities (UUID PKs, created/updated timestamps):

- **users**
  - id, email (unique), google_sub (nullable), display_name, created_at
  - preferences (json: default_cadence, etc.)

- **user_memory_profiles**
  - user_id (FK)
  - tone_samples (json array of accepted openers + outcomes)
  - icp_industries (array)
  - typical_cadence_days (e.g. [4,9,14])
  - embedding (vector) — aggregated profile for semantic lookup

- **leads**
  - id, user_id (FK), company_name, contact_name, contact_role, signal, signal_type, pain_point, notes
  - enriched (json: snapshot, opener, tasks array with rationale)
  - (T007 impl: now populated via llm_service.generate_enrichment pre-Crm; see REVIEW_FOR_T007.md + lead_service)
  - crm_provider, crm_contact_id, crm_deal_id
  - created_at

- **crm_connections**
  - user_id, provider ('bitrix24'|'hubspot'), auth_type ('webhook'|'oauth')
  - encrypted_credentials (bytea or json with envelope)
  - scopes, expires_at, last_validated_at
  - UNIQUE(user_id, provider)

- **outreach_history**
  - id, lead_id (FK), user_id
  - action ('email_sent'|'linkedin'|'call'|'closed_won' etc.)
  - outcome, notes
  - embedding (vector) for recall
  - created_at

- **usage_ledger** (for billing + cost guardrails)
  - user_id, lead_id, model_used, input_tokens, output_tokens, cost_cents, created_at

Indexes: heavy on (user_id, created_at). Foreign keys with cascade where safe.

Migrations via Alembic (Python side) or equivalent.

**T009 note (2026-07-14)**: REVIEW_FOR_T009.md created; models must match data-model.md (users + user_memory_profiles + leads + crm_connections + outreach_history + usage_ledger; vectors on profiles/history). Current backend/app/models only stubs + 001_initial (pgvector ext). See BUILD_COORDINATION + tasks.md. Preps T010 API + persist. (Reviewer pre-delivery).
**Web + polish T012-15/T024-25 note (2026-07-14 Tester/Committer)**: T010 partial (/enrich /push present; /history + persist missing). Web T013 partial progress (Composer calls enrichLead + renders enriched in Preview per T007 shape); T012/14/15 remain local stubs (conn->composer->history->dash chain conceptual GREEN). T024/T025: T009 models (memory_profile + usage_ledger) + llm ctx/record ready; no editor or views yet. All builds (web/py) GREEN. Awaiting impl delivery from wts. "Web flows chain: T012 conn status feeds T013; T014 use-similar pre-fills T013; T015 pulls from T025 + T014. All use T010 API + T009 models." See TEST_REPORT_WEB_POLISH.md + BUILD_COORDINATION append. No breakage.

---

## Google Auth / Services

**User authentication (recommended):**
- "Sign in with Google" (OAuth2).
- Backend exchanges code → stores google_sub + email.
- Issues short-lived JWT (HS256, like vanguard) for subsequent API calls.
- Frontend stores JWT (localStorage or httpOnly as hardening later); extension uses chrome.storage.
- Refresh flow via Google refresh tokens or re-auth.

**Why Google over email/password for this audience:**
- Zero password friction.
- High trust signal for a new tool handling CRM tokens.
- Easy to add "Sign in with LinkedIn" or email later.

**Google services usage (LLM + future):**
- Primary LLM via Google Gemini SDK (`gemini-2.5-flash`).
- Optional later: Google Workspace export, Drive folder for saved plans, or additional signals via People API (with explicit consent).

**Security notes (mandatory before first users):**
- All CRM tokens envelope-encrypted at rest with user-specific key derived from JWT or separate KEK.
- Audit log for any read of another user's memory or token.
- Google client secrets in server env only (never client-side).

---

## API Integrations

### 1. CrmClient Abstraction (core contract — Phase 0 refactor target)
```ts
// Proposed (inspired by current Bitrix24Client + vanguard patterns)
interface CrmContact { name: string; role?: string; company: string; email?: string; linkedin?: string; }
interface CrmDeal { title: string; contactId: string; comments: string; }
interface CrmTask { title: string; description: string; dueDate: string; dealId: string; }

interface CrmClient {
  createContact(c: CrmContact): Promise<{id: string}>;
  createDeal(d: CrmDeal): Promise<{id: string}>;
  createTask(t: CrmTask): Promise<{id: string}>;
  // healthCheck(), disconnect() later
}
```

- `src/crm/bitrix24.ts` (refactor of existing).
- `src/crm/hubspot.ts` (new).
- Provider selector in backend (and MCP for back-compat).

**Bitrix24 specifics (preserve):**
- `crm.contact.add`, `crm.deal.add` (CONTACT_ID), `tasks.task.add` (UF_CRM_TASK: ["D_<id>"], DEADLINE ISO, RESPONSIBLE_ID).

**HubSpot specifics (v3):**
- `/crm/v3/objects/contacts`, `/deals`, `/tasks`.
- Associations array for linking.
- `hs_timestamp` = due date in ms since epoch UTC.
- Custom property `bd_signal_type` (create on first use or document manual setup).

### 2. LLM / Enrichment Proxy
- Internal endpoint: `POST /api/enrich`
- Input: lead brief + user memory context (recent tone samples + profile).
- Output: structured { companySnapshot, emailOpener, followUps: [{title, description, dueInDays, rationale}], confidence, modelUsed }
- Prompt engineering: system includes user profile + few-shot from history; cheap model first.
- Fallback + budget guard: hard cap per user per day + request size limit.

### 3. Auth & Connect
- `POST /auth/google` (or standard OAuth callback).
- `POST /crm/connect` (webhook URL for Bitrix; OAuth start for HubSpot).
- `GET /me`, `GET /connections`.

REST/JSON preferred (align to vanguard style).

---

## Deployment & Ops Config

The full stack runs via Docker Compose with three services sharing the external `bbspace_net` network:

| Service        | Image                            | Port(s)      | Role |
|----------------|----------------------------------|--------------|------|
| `bdlead-db`    | pgvector/pgvector:pg16           | —            | PostgreSQL 16 + pgvector |
| `bdlead-backend` | Python 3.12-slim (FastAPI)    | 8000         | REST API, LLM proxy, orchestration |
| `bdlead-web`   | node:20-alpine → nginx:alpine    | ${WEB_PORT:-8080}:80 | SPA + nginx reverse proxy for /api |

### Architecture: nginx /api Reverse Proxy

```
Browser ──→ bdlead-web:${WEB_PORT:-8080} (nginx)
                ├── /        → /usr/share/nginx/html (SPA — try_files /index.html)
                ├── /assets/* → immutable cache (1y)
                └── /api/*   → proxy_pass http://bdlead-backend:8000/api/
```

The frontend always calls same-origin `/api/...` — the `web/src/api/client.ts` derives its base URL from `import.meta.env.BASE_URL`. In dev, Vite's dev server proxies `/api` → `http://localhost:8000`. In production, nginx handles the same proxy pattern. This eliminates CORS entirely.

### Docker Compose

**Base compose** (`docker-compose.yml`): three services with healthchecks, restart policies, external network.

**Staging override** (`docker-compose.staging.yml`): isolated DB volume (`bdlead_db_staging_data`), container name suffixes (`-staging`), separate `.env.staging`, sub-path `VITE_BASE: /bd-lead-staging/`.

```bash
# Dev (full stack)
docker compose -p bdlead-dev up --build -d

# Staging (with override)
docker compose -f docker-compose.yml -f docker-compose.staging.yml -p bdlead-staging up --build -d
```

### Web Container (Multi-stage)

1. **Stage 1 — Build**: `node:20-alpine`, `npm ci`, `npm run build` (honors `ARG VITE_BASE`).
2. **Stage 2 — Serve**: `nginx:alpine`, copies `web/nginx.conf` and built `dist/`, `HEALTHCHECK curl -f http://localhost/`.

### Deploy (SSH)

```bash
make deploy-staging DEPLOY_USER=root DEPLOY_HOST=staging.example.com
make deploy-prod    DEPLOY_USER=root DEPLOY_HOST=prod.example.com
```

Both targets rsync the repo to the VPS, then run `docker compose up --build -d` with the appropriate compose files.

### Required Secrets

`.env` (never committed): `DATABASE_URL`, `GOOGLE_CLIENT_ID`/`SECRET`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `JWT_SECRET`, `ENCRYPTION_KEK`, `BITRIX24_WEBHOOK_URL`, `HUBSPOT_ACCESS_TOKEN`.

Staging uses a separate `.env.staging` file (see `.env.staging.example`).

**Cost & Scaling (day 1):**
- Hard per-user daily LLM budget + request size cap.
- Redis for hot memory cache / rate limit counters.
- No auto-scaling initially (single VPS sufficient for early users).

---

## BD Lead Research Engine

The product's core intellectual property is a proprietary B2B research methodology — the **BD Lead Research Engine** — encapsulated as a deterministic algorithm for transforming company signals into CRM-ready lead briefs.

**Architecture (T030):**
- **Storage**: Encrypted artifact at `backend/app/skills/bd_lead_research.md.enc` (Fernet cipher, Pkey-derived from `settings.ENCRYPTION_KEK`).
- **Loading**: `backend/app/services/skill_loader.py` decrypts on server startup, strips YAML frontmatter + MCP footer, caches plaintext in memory (one load per process).
- **Injection**: Plaintext skill is injected into the LLM system prompt (via `llm_service._build_prompt`) as the authoritative methodology — shapes the AI's reasoning for enrichment.
- **Client Isolation**: The skill is **never returned to clients**, never embedded in web/extension bundles, never in any API response. Server-only IP.
- **Plaintext Source**: `backend/app/skills/bd_lead_research.source.md` (git-ignored; never committed). Only the `.enc` artifact is in version control.
- **Decryption Fallback**: If decryption fails (bad key, missing file), `skill_loader` returns a minimal fallback instruction (preserves uptime; LLM output is less optimal but system remains operational).

**Versioning & Encryption (T031-T032):**
- When bumping the app version via `make bump-patch|minor|major`, CHANGELOG is updated.
- Before release, if the skill source changed: run `make encrypt-skill` (calls `scripts/encrypt_skill.py`) to re-encrypt the source with the current `ENCRYPTION_KEK` from `.env`.
- The updated `.enc` is committed as part of the release artifact; plaintext never leaves dev.

See root [SECURITY.md](../SECURITY.md) for key rotation and production guidance.

---

## Security & Compliance Highlights

- Encrypted CRM token storage (envelope).
- **Encrypted server-side skill IP** (Fernet, never client-side).
- JWT for session; short expiry + refresh.
- LLM calls server-side only (keys never leave backend).
- Data retention policy documented (user can request purge of history).
- GDPR-aligned (EU target users).
- One-page security note in docs before external launch.

See root [SECURITY.md](../SECURITY.md) (T023, T030) + detailed refs to `backend/app/services/token_vault.py` (T006 fernet+KEK), `backend/app/services/skill_loader.py` (T030 skill loading/decryption), `llm_service.py` budgets/ledger (T007/T009), `config.py`, protected `main.py`. Basic threat model for early users included. (Accurate to impl as of T030.)

---

## Open Decisions (to resolve in Speckit research or with user)

- Full backend language split (pure Python FastAPI vs hybrid Node API + Python workers).
- Exact vector usage (per-lead embeddings + profile vs. simpler full-text + recent N).
- Hosting during dev (share vanguard VPS?).
- Whether to use Auth.js / NextAuth if choosing Next.js for web.

See `CONCEPT.md` and `FEATURES.md` for product constraints that bound these choices.

---

**References**
- Sibling `vanguard-game/docs/architecture.md`, `deploy.md`, models/, services/ai_*.py, docker-compose.yml.
- `docs/development-options.md` §5 (target state diagram).
- Current `src/client.ts` + `src/tool.ts` (to be generalized).
