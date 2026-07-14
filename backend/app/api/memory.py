"""
Memory Profile API routes (T024).

Endpoints:
- GET /api/memory-profile — fetch user's saved profile (tone_samples, icp_industries, typical_cadence)
- PUT /api/memory-profile — create/update user's profile (upsert)

Uses UserMemoryProfile model (T009) + derive_user_uuid() for consistent user_id handling (T012 pattern).
Integrates with llm_service._build_memory_context for real memory injection into /enrich flow.
"""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.auth import get_current_user_api
from app.config import settings
from app.database import get_db
from app.models import UserMemoryProfile
from app.services.token_vault import derive_user_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])

__all__ = ["router", "MemoryProfileRequest", "MemoryProfileResponse"]


# ─── Pydantic models ──────────────────────────────────────────────────────────

class ToneSampleRequest(BaseModel):
    """Single tone sample (past opener + optional outcome)."""
    opener: str = Field(..., min_length=1, description="Example opening email/message")
    outcome: Optional[str] = Field(default=None, description="Optional: whether it was accepted/rejected")


class MemoryProfileRequest(BaseModel):
    """Memory profile update request (all fields optional for partial updates)."""
    icp_industries: Optional[list[str]] = Field(default=None, description="Industries user targets (e.g., ['SaaS', 'FinTech'])")
    typical_cadence: Optional[list[int]] = Field(default=None, description="Follow-up cadence in days (e.g., [4, 9, 14])")
    tone_samples: Optional[list[ToneSampleRequest]] = Field(default=None, description="Past accepted openers with outcomes")


class MemoryProfileResponse(BaseModel):
    """Memory profile response (fully populated)."""
    id: str
    user_id: str
    icp_industries: Optional[list[str]] = None
    typical_cadence: Optional[list[int]] = None
    tone_samples: Optional[list[dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Auth dependency imported from app.api.auth (shared, single canonical implementation)

# ─── GET /api/memory-profile (T024: fetch user's memory profile) ──

@router.get("/profile", response_model=MemoryProfileResponse)
async def get_memory_profile(
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    T024 GET endpoint: fetch current user's memory profile.

    Returns:
    - tone_samples: list of {opener, outcome, accepted_at}
    - icp_industries: list of industry strings
    - typical_cadence: list of follow-up day intervals
    - profile_embedding: (ignored for now; future semantic recall)

    If no profile exists yet, returns empty/sensible defaults (no error).
    Protected via get_current_user_api.
    """
    logger.debug(f"get_memory_profile invoked by current_user={current_user.get('email')}")

    try:
        # Derive UUID from user_id (same as T012 vault pattern)
        user_id = current_user.get("id") or "00000000-0000-0000-0000-000000000001"
        user_uuid = derive_user_uuid(user_id)

        # Query for existing profile
        stmt = select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_uuid)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile:
            return {
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "icp_industries": profile.icp_industries or [],
                "typical_cadence": profile.typical_cadence or [4, 9, 14],  # sensible default
                "tone_samples": profile.tone_samples or [],
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
        else:
            # Return empty profile (no error; client can pre-fill form)
            return {
                "id": str(uuid.uuid4()),
                "user_id": str(user_uuid),
                "icp_industries": [],
                "typical_cadence": [4, 9, 14],  # default
                "tone_samples": [],
                "created_at": None,
                "updated_at": None,
            }

    except Exception as e:
        logger.exception("get_memory_profile failed")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory profile: {str(e)}")


# ─── PUT /api/memory-profile (T024: upsert user's memory profile) ──

@router.put("/profile", response_model=MemoryProfileResponse)
async def upsert_memory_profile(
    req: MemoryProfileRequest,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    T024 PUT endpoint: create or update user's memory profile.

    Body: { icp_industries?: [...], typical_cadence?: [...], tone_samples?: [...] }
    - All fields optional (partial updates supported).
    - icp_industries: list of industry names the user targets.
    - typical_cadence: list of follow-up intervals in days (e.g., [4, 9, 14]).
    - tone_samples: list of past accepted openers {opener, outcome?, accepted_at?}.

    Upserts using derive_user_uuid() (same T012 pattern).
    Returns full updated profile.
    Non-fatal DB errors (graceful degradation for demo).
    Protected via get_current_user_api.
    """
    logger.debug(f"upsert_memory_profile invoked by current_user={current_user.get('email')}")

    try:
        # Derive UUID (same as vault + connect endpoints)
        user_id = current_user.get("id") or "00000000-0000-0000-0000-000000000001"
        user_uuid = derive_user_uuid(user_id)

        # Check if profile exists
        stmt = select(UserMemoryProfile).where(UserMemoryProfile.user_id == user_uuid)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile:
            # Update existing
            if req.icp_industries is not None:
                profile.icp_industries = req.icp_industries
            if req.typical_cadence is not None:
                profile.typical_cadence = req.typical_cadence
            if req.tone_samples is not None:
                # Convert ToneSampleRequest to dict format for JSON storage
                profile.tone_samples = [
                    {
                        "opener": ts.opener,
                        "outcome": ts.outcome,
                        "accepted_at": datetime.utcnow().isoformat(),
                    }
                    for ts in req.tone_samples
                ]
            profile.updated_at = datetime.utcnow()
            db.add(profile)
        else:
            # Create new
            profile = UserMemoryProfile(
                id=uuid.uuid4(),
                user_id=user_uuid,
                icp_industries=req.icp_industries or [],
                typical_cadence=req.typical_cadence or [4, 9, 14],
                tone_samples=[
                    {
                        "opener": ts.opener,
                        "outcome": ts.outcome,
                        "accepted_at": datetime.utcnow().isoformat(),
                    }
                    for ts in (req.tone_samples or [])
                ],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(profile)

        await db.commit()
        logger.debug(f"Persisted memory profile for user {user_uuid}")

        return {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "icp_industries": profile.icp_industries or [],
            "typical_cadence": profile.typical_cadence or [4, 9, 14],
            "tone_samples": profile.tone_samples or [],
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }

    except Exception as e:
        logger.warning(f"Non-fatal: failed to upsert memory profile: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        # Return partial response (demo resilience; in prod would raise)
        if settings.DEBUG:
            return {
                "id": str(uuid.uuid4()),
                "user_id": str(user_uuid),
                "icp_industries": req.icp_industries or [],
                "typical_cadence": req.typical_cadence or [4, 9, 14],
                "tone_samples": req.tone_samples or [],
                "created_at": None,
                "updated_at": None,
            }
        raise HTTPException(status_code=500, detail=f"Failed to save memory profile: {str(e)}")
