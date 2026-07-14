# bitrix24-bd-lead

An **AI-native BD assistant** for non-technical B2B reps. Paste a brief → AI generates an enriched preview (company snapshot + personalized opener + 3 follow-up tasks) → push to create Contact + Deal + 3 Tasks in your CRM.

- **Primary UX**: Web app (React) + thin MV3 browser extension.
- **Backend**: FastAPI (Python) with Google Auth, per-user memory, LLM proxy, shared CrmClient.
- **Legacy engine**: MCP server (still fully supported via shared core).

Supported CRMs: **Bitrix24** (webhook) and **HubSpot** (OAuth). Auth: **Google OAuth + JWT**. Backend API for all clients.

[![Docker](https://img.shields.io/badge/docker--compose-ready-blue?logo=docker)](docker-compose.yml)
[![Python](https://img.shields.io/badge/backend-FastAPI-3776ab?logo=python)](backend/)
[![React](https://img.shields.io/badge/web-React%2FVite-61dafb?logo=react)](web/)
[![MCP](https://img.shields.io/badge/MCP-compatible-000000)](src/)

---

**Quick links**:
- Full product spec & plan: [specs/004-ai-bd-assistant/](./specs/004-ai-bd-assistant/) (plan.md, spec.md, tasks.md)
- UI/UX journeys & screens: [docs/UI_UX.md](./docs/UI_UX.md)
- Architecture & data model: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) + [specs/004-ai-bd-assistant/data-model.md](./specs/004-ai-bd-assistant/data-model.md)
- Extension store assets (description, screenshot instructions, icon notes): [docs/extension-store.md](./docs/extension-store.md) — prepared for Chrome Web Store / Firefox submission (T027)

**Current status**: All P1 user stories are implemented end-to-end and verified running via `docker compose up -d --build` + `npm run dev` — Connections (real backend-stored, encrypted CRM credentials), Composer (real `/enrich` + `/push`), History, Usage tracking, Memory profile editor, Dashboard, and the browser extension are all real, working code (no stubs). See [tasks.md](./specs/004-ai-bd-assistant/tasks.md) and [BUILD_COORDINATION.md](./BUILD_COORDINATION.md) for the full implementation log.

---

## Quickstart: AI BD Assistant (Non-Technical BD Rep)

The primary way to use the product (web app + backend). Follows the happy path in [spec.md](./specs/004-ai-bd-assistant/spec.md) User Story 1 and [UI_UX.md](./docs/UI_UX.md).

### 1. Signup
- Go to the web app (e.g. `http://localhost:5173` after `npm run dev` in `web/` or deployed).
- Click **Sign up with Google**. Approve OAuth.
- You land on Dashboard (stubbed in current skeleton; real JWT + protected routes post T005).

### 2. Connect CRM (via web, T012)
- Go to **Connections**.
- **Bitrix24**: Follow on-screen instructions → paste inbound webhook URL (from Bitrix24 Applications → Webhooks → Add inbound) → Test connection.
- **HubSpot**: Click "Connect with HubSpot" (OAuth flow).
- Credentials stored encrypted server-side (T006 vault). One-time setup.

### 3. Create a Lead — Composer (T013) or Extension (T016-17)
- Click **New Lead** (or use browser extension popup on CRM/LinkedIn tab).
- Fill brief: company, contact name + role, signal, pain point, notes (optional LinkedIn/email).
- Click **"Generate with AI"** → calls backend `/api/leads/enrich` (T007 LLM + memory).
- Review live preview pane.

### 4. View & Push
- Preview shows:
  - Company snapshot (AI research/enrichment).
  - Personalized opener (tone from your memory).
  - Exactly 3 follow-up tasks (+4 / +9 / +14 days) with title, description, rationale.
- Click **Push to CRM** → `/api/leads/push` (T008 orchestration) creates records via CrmClient.
- Success: IDs + links returned; records appear in Bitrix24/HubSpot.

### 5. History & Memory
- Go to **History** (T014): list of past leads, exact pushed snapshot/opener/tasks.
- Use "Create similar" or second lead → memory (T007/T009) personalizes automatically (tone/ICP/cadence).

**Full journey time-to-first-push target**: <10 min for non-technical users. See detailed screens/journeys in [UI_UX.md](./docs/UI_UX.md).

---

## Core Flow (End-to-End)

```
paste brief (company + contact + signal + pain + notes)
    ↓
AI generate (enrich via T010/T007: LLM proxy Gemini Flash + memory context)
    ↓
preview snapshot / opener / 3 tasks (with rationales + due dates)
    ↓
push (T008: reuses orchestration → CrmClient.createContact → createDeal (linked) → 3x createTask)
    ↓
Contact + Deal + 3 Tasks created in CRM (correct associations, +4/+9/+14 deadlines)
```

The same backend APIs power web, extension, and (via shared core) the MCP tool. See [specs/004-ai-bd-assistant/spec.md](./specs/004-ai-bd-assistant/spec.md) + [plan.md](./specs/004-ai-bd-assistant/plan.md).

---

## AI Features

- **Memory**: Per-user profiles + outreach history (tone samples, ICP industries, cadence, prior outcomes). Injected into every enrichment prompt (T007).
- **LLM**: Gemini 2.5 Flash (primary, cheap) + Claude Haiku 4.5 (fallback). Structured JSON output. Per-user budget guardrails + usage logging (<$0.01/lead target).
- Enrichment always produces: `company_snapshot`, `personalized_opener`, `follow_ups[3]` (title/desc/due_in_days/rationale).
- See [specs/004-ai-bd-assistant/data-model.md](./specs/004-ai-bd-assistant/data-model.md) (leads, user_memory_profiles, outreach_history) and lead_service/llm_service.

---

## Supported CRMs, Auth & Backend API

- **CRMs**: Bitrix24 (webhook URL, UF_CRM_TASK linking, dates) + HubSpot (v3 objects + associations + hs_timestamp).
- **Auth (users)**: Google OAuth → short-lived JWT. CRM tokens: envelope-encrypted in vault (per-user).
- **Backend API** (FastAPI, http://localhost:8000):
  - `POST /api/leads/enrich` — preview only (no CRM token needed).
  - `POST /api/leads/push?provider=...&token=...` — full flow + returns ids + `enriched_preview`.
  - `GET /api/health`, protected `/me` etc. (stubs evolving with T005/T010+).
- Docker Compose (T021): `db` (pgvector) + `backend`. Run web separately or extend compose. See `docker-compose.yml` + `.env.example`.

MCP server remains available for Claude/etc users (shared CrmClient + execute logic).

---

## Prerequisites (Legacy MCP + Full Stack)

**For AI BD web/extension (recommended for BD reps):**
- Docker + Docker Compose (for backend + Postgres/pgvector)
- Google account (for OAuth signup)
- Gemini API key (server-side; optional for mock mode) + optional Anthropic key
- Bitrix24 or HubSpot sandbox/developer account
- Node 20+ + npm (for web dev server)

**For legacy MCP server:**
- [Node.js](https://nodejs.org/) v18 or higher
- npm

---

## Setup & Running

### Full AI BD Assistant (web + backend) — Docker (recommended)

The backend + Postgres run in Docker; the web app runs via the Vite dev server (there's no
`web` service in `docker-compose.yml` yet). This is the fastest way to get a working e2e
setup for local testing.

1. **Clone & env**
   ```bash
   git clone <repo-url>
   cd bitrix24-bd-lead
   cp .env.example .env
   # Optional: set GEMINI_API_KEY/ANTHROPIC_API_KEY for real LLM calls (empty = mock mode),
   # BITRIX24_WEBHOOK_URL/HUBSPOT_ACCESS_TOKEN for a real CRM sandbox (empty = demo/mock push).
   ```

2. **Start db + backend**
   ```bash
   docker compose up -d --build
   docker compose ps                       # both services should show "healthy"
   curl http://localhost:8000/api/health   # {"status":"ok",...}
   ```
   Useful commands: `docker compose logs -f bdlead-backend` to tail logs, `docker compose down`
   to stop, `docker compose down -v` to also wipe the Postgres volume (fresh DB on next `up`).
   `DEBUG=true` is set in `docker-compose.yml`, so the backend accepts requests with no real
   login — it falls back to a stub demo user, matching what the web app/extension send today.

3. **Web app (separate terminal)**
   ```bash
   cd web
   npm install
   npm run dev   # http://localhost:5173
   ```

4. **Click through it**: open `http://localhost:5173` → "Sign in (stub)" → **Connections**
   (paste a Bitrix24 webhook or HubSpot token, Test Connection) → **New Lead** (fill the form,
   "Generate with AI", review the preview, Push) → **History** (confirm it landed, try "Use
   similar") → **Usage** (calls/tokens/cost should tick up) → **Memory** (set ICP/cadence/tone
   samples, generate again) → **Dashboard** (should reflect real connection/usage/history state,
   not just local session state).

5. **(Optional) Backend dev without Docker**
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head   # needs a reachable Postgres; see DATABASE_URL in .env
   uvicorn app.main:app --reload
   ```

See [specs/004-ai-bd-assistant/quickstart.md](./specs/004-ai-bd-assistant/quickstart.md) and `docker-compose.yml`.

### Testing the Browser Extension

The extension (`extension/`) is a plain MV3 Chrome extension — no build step, loaded unpacked.
It talks directly to the backend (`http://localhost:8000` by default), so start db + backend
first (step 2 above).

1. **Load it unpacked**
   - Open `chrome://extensions` (or `edge://extensions` for Edge).
   - Enable **Developer mode** (top-right toggle).
   - Click **Load unpacked** → select the `extension/` folder in this repo.
   - The "BD Lead AI" icon should appear in the toolbar/extensions menu.

2. **Configure the API/web base (if not using the defaults)**
   - Defaults are in `extension/config.js`: `API_BASE = http://localhost:8000/api`,
     `WEB_BASE = http://localhost:5173`. Edit that file (then click the reload icon on the
     extension card in `chrome://extensions`) if your backend/web run elsewhere.

3. **(Optional) Set a token**
   - Click the extension icon → **Options** (or right-click the icon → Options).
   - Paste a JWT/demo token and Save if you want authenticated requests. This is optional in
     `DEBUG` mode — with no token, requests go out with no `Authorization` header and the
     backend falls back to the same stub demo user the web app uses.

4. **Exercise the flows**
   - Click the extension icon → fill in the lead form → **Generate with AI** → confirm the
     preview renders (company snapshot, personalized opener, 3 follow-up tasks with rationale).
   - Click **Push to CRM** → confirm it returns contact/deal/task IDs (mock IDs if no real
     `BITRIX24_WEBHOOK_URL`/`HUBSPOT_ACCESS_TOKEN` is configured on the backend).
   - Open **Options** → confirm the links to the web dashboard/connections page work, and that
     Sign Out clears the stored token.

5. **Debugging**
   - Right-click the extension icon → **Inspect popup** (or open `chrome://extensions` → the
     extension's "service worker" link) to see console errors/network requests.
   - A "Not authenticated" or CORS error usually means the backend isn't running, or
     `API_BASE` in `config.js` doesn't match where `docker compose` published port 8000.

### Legacy MCP Server (still works)

(Keep your existing Bitrix24 webhook setup if using only the engine.)

1. Clone + `npm install`
2. `cp .env.example .env` and set `BITRIX24_WEBHOOK_URL=...` (or `HUBSPOT_ACCESS_TOKEN` + `CRM_PROVIDER=hubspot`)
3. `npm run build`
4. `npm start` (or via Claude MCP config below)

The MCP server uses stdio and is launched by MCP clients. It will error if no valid CRM config for the selected provider. Uses the same CrmClient + orchestration as the backend.

---

## Connecting to Claude (MCP — Legacy / Advanced)

Add the following to your MCP client config (e.g., `claude_desktop_config.json` or `.claude/settings.json`):

```json
{
  "mcpServers": {
    "bitrix24-bd-lead": {
      "command": "node",
      "args": ["/absolute/path/to/bitrix24-bd-lead/build/index.js"],
      "env": {
        "BITRIX24_WEBHOOK_URL": "https://yourcompany.bitrix24.com/rest/YOUR_USER_ID/YOUR_WEBHOOK_TOKEN/",
        "CRM_PROVIDER": "bitrix24"
      }
    }
  }
}
```

Restart Claude after saving the config. The tool `bitrix24_create_bd_lead` (and multi-provider) reuses the core flow.

---

## Development

**MCP / shared core (TS):**
```bash
npm run dev   # watch + rebuild src/
npm run build
```

**Web (React/Vite):**
```bash
cd web && npm run dev
```

**Backend (FastAPI):**
```bash
cd backend
# after venv + deps + alembic upgrade head
uvicorn app.main:app --reload
# or docker compose
```

Full stack dev uses docker-compose for db+backend + separate web dev server. See ARCHITECTURE.md and T021.

---

## Available scripts

**Root (MCP engine):**

| Script | Description |
|--------|-------------|
| `npm run build` | Compile TypeScript to `./build/` |
| `npm start` | Run the compiled server (MCP stdio) |
| `npm run dev` | Watch mode — recompile on changes |

**Web (`cd web`):**

| Script | Description |
|--------|-------------|
| `npm run dev` | Vite dev server (localhost:5173) |
| `npm run build` | Type-check + production build to dist/ |
| `npm run preview` | Preview production build |

**Backend (`cd backend`):** Use `python`, `alembic`, `uvicorn`, pytest (when added). Docker for full.

---

## Documentation

Product foundation (source of truth):
- [CONCEPT.md](./docs/CONCEPT.md) — Problem, market, solution & UVP, target users
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — Tech stack, DB schema, Google Auth, API integrations, deployment
- [FEATURES.md](./docs/FEATURES.md) — MVP must-haves, acceptance criteria, user stories, priorities
- [UI_UX.md](./docs/UI_UX.md) — Screens, navigation, journeys, components, accessibility (detailed user flows)

**Implementation specs (004-ai-bd-assistant)**: [specs/004-ai-bd-assistant/](./specs/004-ai-bd-assistant/)
- `plan.md` — phases, structure, contracts
- `spec.md` — user stories, FRs, success criteria
- `tasks.md` — full task list (T001+)
- `data-model.md`, `quickstart.md`, `research.md`, `contracts/`

**Security (T023)**: See [SECURITY.md](./SECURITY.md) — token handling (T006 vault envelope encrypted, server-only, never client), LLM keys (server config), budgets + logging (T007/T009), Google JWT (no passwords), logging details, data retention, code refs (token_vault.py, llm_service, main protected), basic threat model. "Security: tokens resolved server side only via vault; see backend/app/services/token_vault.py and llm budget checks. For T020 tests avoid logging real tokens."

Companion:
- `docs/development-options.md`
- `docs/market_research.md`

**Build status (2026-07-14)**: All tasks (T001-T027) complete and verified running end-to-end via Docker (backend + Postgres/pgvector) + the web dev server, including a genuine `docker compose up -d --build` migration/health smoke test. See [tasks.md](./specs/004-ai-bd-assistant/tasks.md) + [BUILD_COORDINATION.md](./BUILD_COORDINATION.md) for the full history.

## Tool reference (MCP engine — still supported)

**Tool name:** `bitrix24_create_bd_lead`

**Required inputs:**

| Field | Description |
|-------|-------------|
| `company_name` | Target company name |
| `deal_name` | Deal title (format: `[Company] — [Signal in 3 words]`) |
| `signal` | What triggered this lead (e.g., "Series B funding announced") |
| `signal_type` | One of: `new_leadership`, `funding`, `hiring_gap`, `outdated_site`, `new_launch`, `negative_reviews` |
| `contact_name` | Decision maker's full name |
| `contact_role` | Their job title |
| `pain_point` | The business problem to address |
| `email_subject` | Subject line for the outreach email |
| `notes` | Any additional context |

**What it creates (via shared CrmClient — Bitrix24 or HubSpot):**
- 1 Contact (the decision maker)
- 1 Deal (linked to the contact)
- 3 follow-up tasks: Check + Connect (day +4), Short Bump (day +9), Close the Loop (day +14)

(The MCP tool uses the identical core orchestration as web/extension push. Provider selected via env `CRM_PROVIDER` or config.)
