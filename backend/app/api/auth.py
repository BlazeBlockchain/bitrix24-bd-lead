"""
Auth API routes (T005+ full implementation per review finding).

Endpoints:
- POST /api/auth/google — exchange Google ID token for a signed JWT
- GET /api/auth/me — return current user info (requires JWT)

Shared dependencies:
- get_current_user_api — used by all protected routers (replaces 4x duplication)
- create_access_token — issues signed JWTs
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

security = HTTPBearer(auto_error=False)

__all__ = ["router", "get_current_user_api", "create_access_token", "is_email_allowed"]


def is_email_allowed(email: str) -> bool:
    """Whether `email` may sign in, per settings.AUTH_EMAIL_ALLOWLIST.

    An empty allowlist admits everyone — see the setting's docstring for why that
    default is only safe locally. Entries are either full addresses or "@domain"
    suffixes; matching is case-insensitive on both sides.
    """
    raw = settings.AUTH_EMAIL_ALLOWLIST.strip()
    if not raw:
        return True

    if not email:
        return False

    candidate = email.strip().lower()
    for entry in raw.split(","):
        rule = entry.strip().lower()
        if not rule:
            continue
        if rule.startswith("@"):
            if candidate.endswith(rule):
                return True
        elif candidate == rule:
            return True
    return False


def create_access_token(user_id: str, email: str, display_name: str) -> str:
    """Issue a signed JWT for the given user.

    Uses HS256 with settings.JWT_SECRET. Short-lived per settings.JWT_EXPIRE_MINUTES.
    """
    from jose import jwt

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "name": display_name,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user_api(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    """Protected dependency — verifies JWT from Authorization header.

    Returns a user dict with id, email, display_name matching the JWT payload.
    Raises 401 if token is missing, expired, or invalid.

    This is the single canonical auth dependency used by all API routers.
    Debug fallback removed per review (no silent stub users in production).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (Authorization: Bearer <token> required)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (empty token)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        display_name: str | None = payload.get("name")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing sub",
            )

        return {
            "id": user_id,
            "email": email or "unknown@unknown.test",
            "display_name": display_name or "Unknown",
        }
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Request / Response models ────────────────────────────────────────────────


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="Google ID token from Google Identity Services")


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, Any]


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    created_at: str | None = None


# ─── POST /api/auth/google ────────────────────────────────────────────────────


@router.post("/google", response_model=AuthTokenResponse)
async def google_auth(
    body: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Exchange Google ID token for a signed JWT.

    Verifies the Google ID token using google-auth library,
    looks up or creates the user in the database,
    and returns a signed JWT for subsequent API calls.

    Requires GOOGLE_CLIENT_ID to be set in environment.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured (GOOGLE_CLIENT_ID not set)",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        id_info = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        google_sub: str = id_info.get("sub", "")
        email: str = id_info.get("email", "")
        display_name: str = id_info.get("name", email.split("@")[0] if email else "User")

        if not google_sub:
            raise HTTPException(status_code=400, detail="Invalid Google ID token: missing sub")

    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")

    # Allowlist gate. Deliberately before any DB write: a rejected address must not
    # create a user row. Only consulted when an allowlist is configured, so local dev
    # and the existing tests are unaffected.
    if settings.AUTH_EMAIL_ALLOWLIST.strip():
        # A domain rule is only as trustworthy as the claim it matches on, so an
        # unverified address cannot satisfy the allowlist even if it spells the
        # domain correctly.
        if not id_info.get("email_verified", False):
            logger.warning("Sign-in refused: Google reports the address as unverified")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This Google account's email address is not verified.",
            )
        if not is_email_allowed(email):
            logger.warning(f"Sign-in refused for {email!r}: not on the allowlist")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is not authorised for this deployment.",
            )

    # Look up existing user by google_sub, fall back to email
    try:
        stmt = select(User).where(
            (User.google_sub == google_sub) | (User.email == email)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update google_sub if previously linked by email only
            if not user.google_sub:
                user.google_sub = google_sub
                await db.commit()
            user_id = str(user.id)
        else:
            # Create new user
            user_id_uuid = uuid.uuid4()
            new_user = User(
                id=user_id_uuid,
                email=email,
                google_sub=google_sub,
                display_name=display_name,
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            user_id = str(new_user.id)

        access_token = create_access_token(user_id, email, display_name)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_id,
                "email": email,
                "display_name": display_name,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"User lookup/creation failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# ─── GET /api/auth/me ─────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: dict[str, Any] = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the currently authenticated user's info.

    Protected by JWT (requires Authorization: Bearer <token>).
    Also queries DB for created_at timestamp.
    """
    user_id = current_user.get("id", "")
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) and "-" in user_id else None
        if user_uuid:
            stmt = select(User).where(User.id == user_uuid)
            result = await db.execute(stmt)
            db_user = result.scalar_one_or_none()
            if db_user:
                return {
                    "id": str(db_user.id),
                    "email": db_user.email,
                    "display_name": db_user.display_name,
                    "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
                }
    except Exception as e:
        logger.debug(f"DB lookup for /me failed (returning JWT data): {e}")

    return {
        "id": user_id,
        "email": current_user.get("email", ""),
        "display_name": current_user.get("display_name", ""),
        "created_at": None,
    }
