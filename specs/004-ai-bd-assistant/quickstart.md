# Quickstart: AI-Native BD Lead Assistant (004-ai-bd-assistant)

## Prerequisites
- Docker + Docker Compose
- Google OAuth credentials (Client ID + Secret) for development
- Gemini API key (primary) + optional Anthropic key (fallback)
- Bitrix24 sandbox account (webhook) or HubSpot developer account (private app)

## Local Setup

```bash
# 1. Clone and enter the feature branch (already on 004-ai-bd-assistant)
git checkout 004-ai-bd-assistant

# 2. Copy env
cp .env.example .env
# Edit: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GEMINI_API_KEY, DATABASE_URL, etc.

# 3. Start infra
docker compose up -d db redis

# 4. Backend (Python)
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload   # or use compose service

# 5. Web (in another terminal)
cd web   # or frontend/
npm install
npm run dev

# 6. (Optional) Extension dev
cd extension
npm run build   # or use Vite watch + load unpacked in chrome://extensions
```

## First Run (Non-technical flow)
1. Open web app → Sign in with Google.
2. Go to Connections → paste Bitrix24 webhook or connect HubSpot.
3. New Lead → fill form → Generate with AI.
4. Review preview → Push.
5. Verify in CRM sandbox.
6. Create second lead → observe memory personalization.

## MCP (still supported)
The refactored core is used by the existing MCP server on the same branch.

## Troubleshooting
- Token encryption errors → ensure ENCRYPTION_KEK is set.
- LLM fallback → check keys and logs.
- CORS / auth → verify frontend API client base URL and JWT interceptor.

See ARCHITECTURE.md and docker-compose.yml for full details.
