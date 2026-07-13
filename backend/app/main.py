"""
FastAPI app skeleton for AI BD Lead Assistant (T004+).

Mirrors vanguard-game/backend/app/main.py patterns:
- startup/shutdown for db
- CORS
- health
- include routers (stubs)

Provides:
- GET /api/health
- POST /api/leads/push  (auth protected; delegates to T008 lead_service for exact CrmClient flow)

T005: basic auth/JWT stub + protected dep.
T008: orchestration extracted to services/lead_service.py (create_lead_with_followups).
T006: CRM token via vault.resolve using current_user + provider (envelope decrypt from CrmConnection stub);
      ?token= remains as override for demo. create_crm_client receives resolved plaintext token.
"""

import base64
import json
import logging
from typing import Any

from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.config import settings
from app.database import init_db, close_db, get_db
from app.services.lead_service import create_lead_with_followups
from app.services.token_vault import resolve_token  # T006: per-user CRM token vault resolve (envelope)

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

    T006 note: current_user["id"] is used by token_vault.resolve_token() + CrmConnection lookup for per-user CRM tokens.
    User auth (JWT) is separate from CRM token vault.
    """

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


# ─── Stub lead input (subset of BdLeadSchema from src/tool.ts; orchestration in T008; full models T009) ────

class LeadPushInput(BaseModel):
    """Minimal lead input for stub /push. Matches core fields from contracts + tool.ts.
    Passed to create_lead_with_followups (T008 service).
    """
    company_name: str = Field(..., min_length=1)
    deal_name: str = Field(..., min_length=1)
    contact_name: str = Field(..., min_length=1)
    contact_role: str = Field(..., min_length=1)
    signal: str = Field(default="stub signal")
    signal_type: str = Field(default="new_launch")
    pain_point: str = Field(default="stub pain")
    email_subject: str = Field(default="Intro")
    notes: str = Field(default="stub notes")


# Date helpers moved to services/lead_service.py (T008 orchestration centralization).
# Stub duplication of tool.ts logic eliminated.


# ─── Stub /push route (auth-protected T005; delegates to T008 orchestration) ──

@app.post("/api/leads/push")
async def push_lead(
    lead: LeadPushInput,
    provider: str = Query(default=settings.DEFAULT_CRM_PROVIDER, description="bitrix24 | hubspot"),
    token: str | None = Query(default=None, description="CRM webhook or access token (separate from user JWT; use ?token= or env for demo). T006: override bypasses vault."),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Stub endpoint: takes lead input and exercises full CrmClient flow via orchestration service.

    T005 auth: protected via get_current_user.
    T006: CRM token resolved via vault using current_user + provider (CrmConnection lookup + envelope decrypt).
          ?token= acts as override (for demo continuity / before stored connections in T009+).

    Delegates to create_lead_with_followups (T008) which does:
      createContact -> createDeal(with contactId) -> 3x createTask(due +4/9/14, dealId)
    using create_crm_client(provider, resolved_token, current_user=...) exactly.

    Token injection (clarification addressed): user JWT != CRM token.
    Vault (token_vault.resolve_token) does the (current_user, provider) -> CrmConnection -> decrypt lookup.
    Plaintext token only ever passed server-side into CrmClient adapters.
    Keeps CrmClient abstraction intact.

    Stub notes/LLM comments retained for later enrichment (T007/T009).

    Returns ids shape (like executeBdLead + extras).
    """
    logger.debug(f"push_lead invoked by current_user={current_user.get('email')} provider={provider}")

    # T006: resolve token from vault (keyed on current_user + provider). ?token= is override.
    # Vault handles DEBUG fallback to settings + future real CrmConnection decrypt.
    # This replaces the prior inline settings lookup. (resolve is sync in T006 stub)
    try:
        effective_token = resolve_token(current_user, provider, override=token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not effective_token:
        raise HTTPException(
            status_code=400,
            detail=f"No token configured for provider '{provider}'. Store via connect (T006/T012) or pass ?token=... or set in .env (stub).",
        )

    try:
        # Delegate exact orchestration to T008 service (contact->deal->3x task with +4/9/14 dates).
        # Keeps CrmClient usage exact inside service (factory may also use vault if needed).
        # effective_token is plaintext (decrypted by vault).
        core_result = await create_lead_with_followups(lead, provider, effective_token, current_user)
    except Exception as e:
        logger.exception("CrmClient call failed in stub push (via lead_service)")
        # Creation errors (e.g. bad token to factory) and op errors -> 502 for simplicity in stub
        # (prior separate 400 for create is now subsumed; callers see descriptive detail)
        raise HTTPException(status_code=502, detail=f"CRM operation failed: {str(e)}")

    return {
        **core_result,
        "provider": provider,
        "authenticated_as": current_user.get("email") or current_user.get("id"),
        "note": "STUB route (T008+T006): protected by get_current_user; token resolved via vault (current_user + CrmConnection); delegates to create_lead_with_followups (exact flow). Full orchestration + LLM enrich + real models/DB in T009+. CrmClient exercised via service.",
    }


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
