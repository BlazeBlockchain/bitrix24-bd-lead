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

T005: basic auth/JWT stub added. Protected dependency get_current_user.
 /push now requires/uses auth (Authorization: Bearer or debug fallback to settings).
CRM tokens (for create_crm_client) still via ?token query or settings for demo (separate concern).
"""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.config import settings
from app.database import init_db, close_db, get_db
from app.adapters.crm import create_crm_client, CrmClient  # type: ignore

logger = logging.getLogger(__name__)

# ─── T005: Basic auth/JWT stub (no full DB/users yet; prepare per data-model) ───
# Simple token validation + placeholder JWT decode using stdlib (or python-jose later).
# Mirrors vanguard lightly: protected dep returning user-like dict.
# In DEBUG: fallback stub user if no/invalid header (keeps current web stub flow working).
# Real: Google OAuth issue short JWT (HS256), validate + user lookup (T005/T009).
# Use current_user in future for per-user CRM token resolution (via CrmConnection).

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """Protected dependency stub (T005).

    Returns minimal user dict (id/email/display_name) per data-model User.
    No DB hit yet (stub); later query users table + validate against CrmConnections.
    Accepts Authorization: Bearer <token-or-jwt>.
    Falls back to settings-based demo user when DEBUG (keeps existing ?provider&token web calls working until web adds JWT header).
    Placeholder JWT: stdlib base64 decode attempt (python-jose + real verify + /auth/login later).
    """
    token = credentials.credentials if credentials else None

    if not token:
        if settings.DEBUG:
            logger.debug("get_current_user: no Authorization header, using DEBUG stub user (demo fallback)")
            return {
                "id": "stub-user-00000000-0000-0000-0000-000000000001",
                "email": "demo@local.test",
                "display_name": "Demo User (T005 stub)",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (Authorization: Bearer <token> required)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder user from token
    user: dict[str, Any] = {
        "id": "stub-from-token",
        "email": "user@stub.test",
        "display_name": "Authenticated Stub",
        "token_preview": (token[:12] + "...") if len(token) > 12 else token,
    }

    # Attempt placeholder JWT decode FIRST (stdlib, no sig verify - skeleton only)
    # This path is exercised for real-looking JWTs even in DEBUG.
    # For real JWT: from jose import jwt; jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1] + "=="
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8", errors="ignore"))
            if isinstance(payload, dict):
                user.update({
                    "id": payload.get("sub") or payload.get("user_id") or user["id"],
                    "email": payload.get("email") or user["email"],
                    "display_name": payload.get("name") or payload.get("display_name") or user["display_name"],
                })
                user["jwt_payload"] = payload
                user["note"] = "T005 placeholder JWT decoded via stdlib"
                return user
    except Exception as e:
        logger.debug(f"placeholder JWT decode failed (ok for demo tokens): {e}")

    if token == settings.DEMO_AUTH_TOKEN or (settings.DEBUG and len(token) > 0):
        # Accept DEMO or any non-empty token in debug (skeleton convenience, after JWT attempt)
        user["note"] = "T005 debug/demo auth accepted (Authorization or fallback)"
        return user

    if settings.DEBUG:
        user["note"] = "T005 fallback in DEBUG after placeholder attempt"
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid auth token (stub validation)",
        headers={"WWW-Authenticate": "Bearer"},
    )


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


# ─── Stub /push route that uses a CrmClient (now auth-protected T005) ──────────

@app.post("/api/leads/push")
async def push_lead(
    lead: LeadPushInput,
    provider: str = Query(default=settings.DEFAULT_CRM_PROVIDER, description="bitrix24 | hubspot"),
    token: str | None = Query(default=None, description="CRM webhook or access token (separate from user JWT; use ?token= or env for demo)"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Stub endpoint: takes lead input and exercises CrmClient (contact+deal+3tasks).

    T005 auth: now protected via get_current_user (Authorization: Bearer or DEBUG fallback).
    current_user available here (stub dict per data-model; will drive per-user CRM token lookup later).

    CRM token resolution unchanged: ?token query or settings (T006 vault will replace).
    Keep using create_crm_client(provider, token) as required.

    In prod: protected + full orchestration (T008) + memory/LLM.

    Returns the ids (like executeBdLead result shape).
    """
    logger.debug(f"push_lead invoked by current_user={current_user.get('email')} provider={provider}")

    # Resolve CRM token (unchanged logic; auth stub is orthogonal to CRM token)
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
            "authenticated_as": current_user.get("email") or current_user.get("id"),
            "note": "STUB route (T005): protected by get_current_user; full orchestration + LLM enrich in T008+. CrmClient exercised. Auth is stub (DEBUG fallback or Bearer).",
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
