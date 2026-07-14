"""
Usage Ledger API routes (T025).

Endpoints:
- GET /api/usage/summary — returns current user's usage stats (total calls, tokens, cost, today's spend, remaining budget)
- GET /api/usage/history?limit=50 — returns paginated list of recent UsageLedger rows for the user

Uses UsageLedger model (T009) + derive_user_uuid() for consistent user_id handling (T012 pattern).
Reads from usage_ledger table that's populated by llm_service._record_usage (T010).
All read-only, no modifications to usage recording.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_api
from app.config import settings
from app.database import get_db
from app.models import UsageLedger
from app.services.token_vault import derive_user_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage", tags=["usage"])

__all__ = ["router", "UsageSummaryResponse", "UsageHistoryItemResponse", "UsageHistoryResponse"]


# ─── Pydantic models ──────────────────────────────────────────────────────────

class UsageSummaryResponse(BaseModel):
    """Summary of current user's usage stats."""
    total_calls: int = Field(..., description="Total enrich/push calls this user has made")
    total_input_tokens: int = Field(..., description="Total input tokens used")
    total_output_tokens: int = Field(..., description="Total output tokens used")
    total_estimated_cost_cents: int = Field(..., description="Total estimated cost in cents")
    today_cost_cents: int = Field(..., description="Today's estimated cost in cents")
    remaining_budget_cents: int = Field(..., description="Remaining budget for today (LLM_DAILY_BUDGET_CENTS - today_cost)")
    daily_budget_cents: int = Field(..., description="Daily budget limit from settings")


class UsageHistoryItemResponse(BaseModel):
    """Single usage ledger entry."""
    id: str = Field(..., description="Usage ledger entry UUID")
    model: str = Field(..., description="Model name (e.g. 'gemini-2.5-flash')")
    input_tokens: int = Field(..., description="Input tokens for this call")
    output_tokens: int = Field(..., description="Output tokens for this call")
    estimated_cost_cents: int = Field(..., description="Estimated cost in cents")
    created_at: str = Field(..., description="ISO timestamp of when this usage was recorded")
    lead_id: Optional[str] = Field(default=None, description="Optional: UUID of associated lead")


class UsageHistoryResponse(BaseModel):
    """Paginated history response."""
    items: list[UsageHistoryItemResponse] = Field(..., description="List of recent usage entries")
    total_count: int = Field(..., description="Total number of entries for this user")
    limit: int = Field(..., description="Requested limit")


# Auth dependency imported from app.api.auth (shared, single canonical implementation)

# ─── GET /api/usage/summary (T025: fetch user's usage summary) ──

@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    T025 GET endpoint: fetch current user's usage summary.

    Returns:
    - total_calls: total number of LLM calls for this user
    - total_input_tokens, total_output_tokens: cumulative token counts
    - total_estimated_cost_cents: cumulative cost in cents
    - today_cost_cents: cost incurred today (for budget comparison)
    - remaining_budget_cents: today's remaining budget (LLM_DAILY_BUDGET_CENTS - today_cost)
    - daily_budget_cents: the configured daily budget from settings

    Protected via get_current_user_api.
    Graceful handling: no usage records yet returns zero values.
    """
    logger.debug(f"get_usage_summary invoked by current_user={current_user.get('email')}")

    try:
        # Derive UUID from user_id (same as T012/T024 pattern)
        user_id = current_user.get("id") or "00000000-0000-0000-0000-000000000001"
        user_uuid = derive_user_uuid(user_id)

        # Query all usage for this user (total stats)
        stmt_total = select(
            func.count(UsageLedger.id).label("call_count"),
            func.sum(UsageLedger.input_tokens).label("total_input"),
            func.sum(UsageLedger.output_tokens).label("total_output"),
            func.sum(UsageLedger.estimated_cost_cents).label("total_cost"),
        ).where(UsageLedger.user_id == user_uuid)

        result_total = await db.execute(stmt_total)
        row_total = result_total.one()

        total_calls = row_total.call_count or 0
        total_input_tokens = row_total.total_input or 0
        total_output_tokens = row_total.total_output or 0
        total_cost_cents = row_total.total_cost or 0

        # Query today's usage (for budget check)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt_today = select(
            func.sum(UsageLedger.estimated_cost_cents).label("today_cost"),
        ).where(
            (UsageLedger.user_id == user_uuid) & (UsageLedger.created_at >= today_start)
        )

        result_today = await db.execute(stmt_today)
        row_today = result_today.one()
        today_cost_cents = row_today.today_cost or 0

        remaining_budget = max(0, settings.LLM_DAILY_BUDGET_CENTS - today_cost_cents)

        return {
            "total_calls": total_calls,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_estimated_cost_cents": total_cost_cents,
            "today_cost_cents": today_cost_cents,
            "remaining_budget_cents": remaining_budget,
            "daily_budget_cents": settings.LLM_DAILY_BUDGET_CENTS,
        }

    except Exception as e:
        logger.exception("get_usage_summary failed")
        # Graceful degradation in demo (return zeros instead of error)
        if settings.DEBUG:
            logger.warning(f"Returning zero usage due to error in demo: {e}")
            return {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_estimated_cost_cents": 0,
                "today_cost_cents": 0,
                "remaining_budget_cents": settings.LLM_DAILY_BUDGET_CENTS,
                "daily_budget_cents": settings.LLM_DAILY_BUDGET_CENTS,
            }
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage summary: {str(e)}")


# ─── GET /api/usage/history (T025: fetch paginated usage history) ──

@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    T025 GET endpoint: fetch current user's recent usage history (paginated).

    Query params:
    - limit: max number of entries to return (default 50, cap at 200 for safety)

    Returns:
    - items: list of UsageHistoryItemResponse (model, tokens, cost, created_at, lead_id)
    - total_count: total number of entries for this user (for pagination awareness)
    - limit: the limit that was used

    Protected via get_current_user_api.
    Entries ordered by created_at DESC (most recent first).
    Graceful handling: no usage records yet returns empty list.
    """
    logger.debug(f"get_usage_history invoked by current_user={current_user.get('email')} limit={limit}")

    # Safety: cap limit
    limit = min(limit, 200)

    try:
        # Derive UUID from user_id
        user_id = current_user.get("id") or "00000000-0000-0000-0000-000000000001"
        user_uuid = derive_user_uuid(user_id)

        # Get total count for this user
        stmt_count = select(func.count(UsageLedger.id)).where(UsageLedger.user_id == user_uuid)
        result_count = await db.execute(stmt_count)
        total_count = result_count.scalar() or 0

        # Get recent entries (ordered by created_at DESC, limit applied)
        stmt = (
            select(UsageLedger)
            .where(UsageLedger.user_id == user_uuid)
            .order_by(desc(UsageLedger.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)
        entries = result.scalars().all()

        items = [
            {
                "id": str(entry.id),
                "model": entry.model,
                "input_tokens": entry.input_tokens,
                "output_tokens": entry.output_tokens,
                "estimated_cost_cents": entry.estimated_cost_cents,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "lead_id": str(entry.lead_id) if entry.lead_id else None,
            }
            for entry in entries
        ]

        return {
            "items": items,
            "total_count": total_count,
            "limit": limit,
        }

    except Exception as e:
        logger.exception("get_usage_history failed")
        # Graceful degradation in demo
        if settings.DEBUG:
            logger.warning(f"Returning empty usage history due to error in demo: {e}")
            return {
                "items": [],
                "total_count": 0,
                "limit": limit,
            }
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage history: {str(e)}")
