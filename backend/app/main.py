"""
FastAPI app skeleton for AI BD Lead Assistant (T004+).

Mirrors vanguard-game/backend/app/main.py patterns:
- startup/shutdown for db
- CORS
- health
- include routers (stubs)

Provides:
- GET /api/health
- POST /api/leads/push  (stub that accepts lead input + exercises CrmClient)

Auth is stubbed (no JWT dep yet; T005). CRM tokens from settings (env) or query for demo.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.database import init_db, close_db, get_db
from app.adapters.crm import create_crm_client, CrmClient  # type: ignore

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS (open for skeleton; tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting up BD Lead Assistant API...")
    await init_db()
    logger.info("Database initialized (stub models)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    logger.info("Shutting down BD Lead Assistant API...")
    await close_db()
    logger.info("Database connections closed")


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Basic health endpoint."""
    return {"status": "ok", "version": settings.APP_VERSION, "provider_default": settings.DEFAULT_CRM_PROVIDER}


# ─── Stub lead input (subset of BdLeadSchema from src/tool.ts; full in T008) ────

class LeadPushInput(BaseModel):
    """Minimal lead input for stub /push. Matches core fields from contracts + tool.ts."""
    company_name: str = Field(..., min_length=1)
    deal_name: str = Field(..., min_length=1)
    contact_name: str = Field(..., min_length=1)
    contact_role: str = Field(..., min_length=1)
    signal: str = Field(default="stub signal")
    signal_type: str = Field(default="new_launch")
    pain_point: str = Field(default="stub pain")
    email_subject: str = Field(default="Intro")
    notes: str = Field(default="stub notes")


# Date helpers (stub duplication of tool.ts; centralize in T008 orchestration)
def _add_days(n: int) -> str:
    d = datetime.utcnow() + timedelta(days=n)
    return d.strftime("%Y-%m-%d")


# ─── Stub /push route that uses a CrmClient ────────────────────────────────────

@app.post("/api/leads/push")
async def push_lead(
    lead: LeadPushInput,
    provider: str = Query(default=settings.DEFAULT_CRM_PROVIDER, description="bitrix24 | hubspot"),
    token: str | None = Query(default=None, description="CRM webhook or access token (auth stub; prefer env)"),
) -> dict[str, Any]:
    """
    Stub endpoint: takes lead input and exercises CrmClient (contact+deal+3tasks).

    Auth/selection stub: token from query or settings (T006 will use encrypted per-user).
    In production this will be protected + use full orchestration from T008 + memory/LLM.

    Returns the ids (like executeBdLead result shape).
    """
    # Resolve token (auth stub decision: top level config for skeleton/demo)
    if not token:
        if provider == "hubspot":
            token = settings.HUBSPOT_ACCESS_TOKEN
        else:
            token = settings.BITRIX24_WEBHOOK_URL

    if not token:
        raise HTTPException(
            status_code=400,
            detail=f"No token configured for provider '{provider}'. Pass ?token=... or set in .env (stub mode).",
        )

    try:
        client: CrmClient = create_crm_client(provider, token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create CRM client: {e}")

    # Map to Crm* (minimal; full comments construction in orchestration)
    try:
        contact = await client.createContact({
            "name": lead.contact_name,
            "role": lead.contact_role,
            "company": lead.company_name,
        })

        deal_comments = (
            f"Signal: {lead.signal}\n\n"
            f"Pain Point: {lead.pain_point}\n\n"
            f"Email Subject: {lead.email_subject}\n\n"
            f"Notes:\n{lead.notes}"
        )
        deal = await client.createDeal({
            "title": lead.deal_name,
            "contactId": contact["id"],
            "comments": deal_comments,
        })

        # 3 tasks (same cadence as TS tool.ts)
        date1 = _add_days(4)
        date2 = _add_days(9)
        date3 = _add_days(14)

        task1 = await client.createTask({
            "title": "Follow-up 1 — Check + Connect",
            "description": f"Stub: check email + connect on LinkedIn for {lead.contact_name} at {lead.company_name}.",
            "dueDate": date1,
            "dealId": deal["id"],
        })
        task2 = await client.createTask({
            "title": "Follow-up 2 — Short Bump",
            "description": f"Stub bump for {lead.signal_type}.",
            "dueDate": date2,
            "dealId": deal["id"],
        })
        task3 = await client.createTask({
            "title": "Follow-up 3 — Close the Loop",
            "description": f"Stub close on: {lead.pain_point}",
            "dueDate": date3,
            "dealId": deal["id"],
        })

        return {
            "contact_id": contact["id"],
            "deal_id": deal["id"],
            "task1": {"id": task1["id"], "date": date1},
            "task2": {"id": task2["id"], "date": date2},
            "task3": {"id": task3["id"], "date": date3},
            "provider": provider,
            "note": "STUB route: full orchestration + auth + LLM enrich in later tasks (T005-T010). CrmClient exercised.",
        }
    except Exception as e:
        logger.exception("CrmClient call failed in stub push")
        raise HTTPException(status_code=502, detail=f"CRM operation failed: {str(e)}")


# Router placeholders (mirrors vanguard; expand in T005+)
# from app.api import leads  # etc
# app.include_router(...)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
