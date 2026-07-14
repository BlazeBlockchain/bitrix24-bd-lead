"""
Leads API routes (T010).

Extracted from main.py to follow plan structure (backend/app/api/leads.py).
Routes:
- POST /api/leads/enrich (T007: LLM enrichment, protected)
- POST /api/leads/push (T008: full lead creation, protected)
- GET /api/leads/history (T014: user's past leads, protected)
- GET /api/leads/{lead_id} (T010: full lead detail, protected, ownership check)

All auth-protected via get_current_user; shapes preserved exactly.
Persistence: uses Lead model (T009) + UsageLedger (T010).
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.config import settings
from app.database import get_db
from app.models import Lead, UsageLedger
from app.services.lead_service import create_lead_with_followups
from app.services.llm_service import generate_enrichment
from app.services.token_vault import resolve_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])

__all__ = ["router", "LeadPushInput"]


# ─── Lead input (subset of BdLeadSchema from src/tool.ts; orchestration T008 + LLM T007) ────

class LeadPushInput(BaseModel):
    """Minimal lead input for /push and /enrich. Matches core fields from contracts + tool.ts.
    T007: also used for generate_enrichment (preview).
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


# ─── Auth dependency (replicated from main.py to avoid circular imports) ───
security = HTTPBearer(auto_error=False)


async def get_current_user_api(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """Protected dependency stub (T005).

    Returns minimal user dict (id/email/display_name) per data-model User.
    Replicated from main.py to avoid circular imports.
    Accepts Authorization: Bearer <token-or-jwt>.
    Falls back to settings-based demo user when DEBUG.
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
    try:
        import base64
        import json
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


# ─── POST /api/leads/enrich (T007: LLM preview, protected) ──

@router.post("/enrich")
async def enrich_lead(
    lead: LeadPushInput,
    current_user: dict = Depends(get_current_user_api),
) -> dict[str, Any]:
    """
    T007 LLM enrichment for preview (Composer "Generate with AI").

    Calls generate_enrichment (Gemini primary + Haiku fallback; memory context injected via current_user).
    Structured output: snapshot + opener + 3 follow-ups + rationale.
    No CrmClient / token involved. Budget + logging applied inside service.

    Prepares web T013; safe additive (no impact to /push or CrmClient).
    """
    logger.debug(f"enrich_lead invoked by current_user={current_user.get('email')}")
    try:
        result = await generate_enrichment(lead.model_dump(), current_user=current_user)
        return {
            **result,
            "authenticated_as": current_user.get("email") or current_user.get("id"),
            "provider_default": settings.DEFAULT_CRM_PROVIDER,
        }
    except Exception as e:
        logger.exception("LLM enrichment failed")
        raise HTTPException(status_code=502, detail=f"LLM enrichment failed: {str(e)}")


# ─── POST /api/leads/push (T008: full lead creation, protected) ──

async def _persist_lead(lead_input: LeadPushInput, core_result: dict, provider: str, current_user: dict, db: AsyncSession) -> None:
    """T010/T014: persist helper using T009 Lead model. Non-fatal on error (demo resilience)."""
    try:
        uid_str = current_user.get("id", "00000000-0000-0000-0000-000000000001")
        try:
            user_uuid = uuid.UUID(uid_str) if "-" in str(uid_str) else uuid.UUID("00000000-0000-0000-0000-000000000001")
        except Exception:
            user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        lead_uuid = uuid.uuid4()
        db_lead = Lead(
            id=lead_uuid,
            user_id=user_uuid,
            company_name=lead_input.company_name,
            contact_name=lead_input.contact_name,
            contact_role=lead_input.contact_role,
            signal=lead_input.signal,
            signal_type=lead_input.signal_type,
            pain_point=lead_input.pain_point,
            notes=lead_input.notes,
            email=None,
            linkedin_url=None,
            enriched=core_result.get("enriched_preview"),
            crm_provider=provider,
            crm_contact_id=core_result.get("contact_id"),
            crm_deal_id=core_result.get("deal_id"),
            created_at=datetime.utcnow(),
        )
        db.add(db_lead)
        await db.commit()
        logger.debug(f"Persisted lead {lead_uuid} for user {user_uuid}")
    except Exception as e:
        logger.warning(f"Non-fatal: failed to persist lead (T014 history prep): {e}")
        # do not rollback hard; keep push success for CRM side
        try:
            await db.rollback()
        except Exception:
            pass


@router.post("/push")
async def push_lead(
    lead: LeadPushInput,
    provider: str = Query(default=settings.DEFAULT_CRM_PROVIDER, description="bitrix24 | hubspot"),
    token: str | None = Query(default=None, description="CRM webhook or access token (separate from user JWT; use ?token= or env for demo)"),
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Endpoint: takes lead input and exercises full CrmClient flow via orchestration service (T008).

    T005 auth: protected via get_current_user.
    current_user available (will drive per-user CRM token lookup in T006+).

    Delegates to create_lead_with_followups (T008 + T007) which does:
      generate_enrichment (LLM memory-injected) -> createContact -> createDeal(with contactId) -> 3x createTask(due +4/9/14, dealId)
    using create_crm_client(provider, token) exactly. Crm flow intact.

    CRM token resolution: ?token or settings (T006 vault later).
    LLM enrichment now populates dynamic text.

    Returns ids shape (like executeBdLead) + enriched_preview (T007).
    T010/T014: after success, persist to Lead model for /history (non-fatal).
    """
    logger.debug(f"push_lead invoked by current_user={current_user.get('email')} provider={provider}")

    # T006: resolve token from vault (keyed on current_user + provider). ?token= is override.
    # Vault handles DEBUG fallback to settings + future real CrmConnection decrypt.
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
        # Delegate exact orchestration to T008 service (T007 LLM first, then contact->deal->3x task +4/9/14).
        # T010: pass db for usage ledger persistence
        core_result = await create_lead_with_followups(lead, provider, effective_token, current_user, db=db)
    except Exception as e:
        logger.exception("CrmClient call failed in push")
        raise HTTPException(status_code=502, detail=f"CRM operation failed: {str(e)}")

    # T014/T010: persist for history (uses T009 model; shape of return unchanged)
    await _persist_lead(lead, core_result, provider, current_user, db)

    return {
        **core_result,
        "provider": provider,
        "authenticated_as": current_user.get("email") or current_user.get("id"),
        "note": "T008+T007: protected; delegates to create_lead_with_followups (LLM enrich + exact CrmClient flow for both providers). enriched_preview included.",
    }


# ─── GET /api/leads/history (T014: user's past leads, protected) ──

@router.get("/history")
async def get_lead_history(
    limit: int = Query(20, le=100, description="Max items (MVP simple limit; no cursor/pagination yet)"),
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    T014 History list: returns user's past pushed leads (persisted on successful /push).
    Shows: company, contact, date, crm ids, brief signal + enriched snapshot for detail.
    Protected. Uses heavy index (user_id, created_at) from T009.
    Decision: simple limit (20 default) for MVP; shared for dashboard T015 + future filters.
    Shape: list of {id, company_name, contact_name, created_at, crm_*, signal, enriched (full snapshot/opener/tasks for detail/use-similar)}
    CRM outcome: currently the crm ids + enriched (later outreach_history for won/lost).
    No breakage to /push or /enrich shapes/flows.
    """
    logger.debug(f"get_lead_history for {current_user.get('email')} limit={limit}")
    try:
        uid_str = current_user.get("id", "00000000-0000-0000-0000-000000000001")
        try:
            user_uuid = uuid.UUID(uid_str) if "-" in str(uid_str) else uuid.UUID("00000000-0000-0000-0000-000000000001")
        except Exception:
            user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

        stmt = (
            select(Lead)
            .where(Lead.user_id == user_uuid)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()

        items: list[dict[str, Any]] = []
        for l in leads:
            items.append({
                "id": str(l.id),
                "company_name": l.company_name,
                "contact_name": l.contact_name,
                "contact_role": l.contact_role,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "crm_provider": l.crm_provider,
                "crm_contact_id": l.crm_contact_id,
                "crm_deal_id": l.crm_deal_id,
                "signal": l.signal,
                "signal_type": l.signal_type,
                "enriched": l.enriched,  # full for detail (snapshot, opener, follow_ups) + CRM outcome via ids
            })
        return items
    except Exception as e:
        logger.exception("history query failed (T014)")
        # graceful: empty list (demo without DB rows ok)
        return []


# ─── GET /api/leads/{lead_id} (T010: full lead detail, protected, ownership check) ──

@router.get("/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    T010 Full lead detail endpoint.

    Returns: complete lead record including enriched fields, CRM ids, all signal/notes.
    Protected: get_current_user ensures auth.
    Ownership check: verify lead.user_id matches current_user["id"], return 404 if not found or not owned.

    Shape: {id, company_name, contact_name, contact_role, signal, signal_type, pain_point, notes,
             email, linkedin_url, enriched (full snapshot/opener/follow_ups), crm_provider, crm_contact_id,
             crm_deal_id, created_at, authenticated_as}
    """
    logger.debug(f"get_lead_detail: lead_id={lead_id}, user={current_user.get('email')}")

    try:
        # Parse lead_id as UUID
        try:
            lead_uuid = uuid.UUID(lead_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid lead_id format (must be UUID)")

        # Get current user's UUID
        uid_str = current_user.get("id", "00000000-0000-0000-0000-000000000001")
        try:
            user_uuid = uuid.UUID(uid_str) if "-" in str(uid_str) else uuid.UUID("00000000-0000-0000-0000-000000000001")
        except Exception:
            user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

        # Query for lead with ownership check
        stmt = select(Lead).where((Lead.id == lead_uuid) & (Lead.user_id == user_uuid))
        result = await db.execute(stmt)
        lead = result.scalars().first()

        if not lead:
            logger.debug(f"Lead {lead_id} not found or not owned by user {user_uuid}")
            raise HTTPException(status_code=404, detail="Lead not found or access denied")

        # Return full detail
        return {
            "id": str(lead.id),
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "contact_role": lead.contact_role,
            "signal": lead.signal,
            "signal_type": lead.signal_type,
            "pain_point": lead.pain_point,
            "notes": lead.notes,
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "enriched": lead.enriched,  # full: snapshot, opener, follow_ups with rationale
            "crm_provider": lead.crm_provider,
            "crm_contact_id": lead.crm_contact_id,
            "crm_deal_id": lead.crm_deal_id,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "authenticated_as": current_user.get("email") or current_user.get("id"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"get_lead_detail failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead detail")
