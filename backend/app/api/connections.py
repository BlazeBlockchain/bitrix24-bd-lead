"""
Connections API routes (T012).

Manage CRM connections for current user: store/validate tokens, test connections.
Routes:
- POST /api/connections/bitrix24 (body: webhook_url) — validate + store encrypted
- POST /api/connections/bitrix24/test (body: webhook_url or uses stored) — test connectivity
- POST /api/connections/hubspot (body: access_token) — store private app token
- GET /api/connections — list user's connections

All auth-protected via get_current_user; uses token_vault encrypt/decrypt, CrmConnection model.
"""

import logging
import re
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.auth import get_current_user_api
from app.config import settings
from app.database import get_db
from app.models import CrmConnection
from app.services.token_vault import encrypt_credentials, decrypt_credentials, derive_user_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connections", tags=["connections"])

__all__ = ["router"]


# Auth dependency imported from app.api.auth (shared, single canonical implementation)

# ─── Input models ───

class Bitrix24ConnectInput(BaseModel):
    webhook_url: str = Field(..., min_length=10)


class Bitrix24TestInput(BaseModel):
    webhook_url: str | None = Field(default=None, description="Optional; if not provided, uses stored connection")


class HubSpotConnectInput(BaseModel):
    access_token: str = Field(..., min_length=1, description="HubSpot private app access token (e.g., pat-na1-...)")


class ConnectionResponse(BaseModel):
    id: str
    provider: str
    connected: bool
    auth_type: str
    created_at: str | None = None
    last_validated_at: str | None = None
    # Masked token for display (never full token)
    masked_credential: str | None = None


class ConnectionListResponse(BaseModel):
    connections: list[ConnectionResponse]


# ─── Helpers ───

def _mask_credential(credential: str, provider: str) -> str:
    """Mask credential for safe display. E.g., show last 4 chars."""
    if not credential:
        return "(not set)"
    if provider == "bitrix24":
        # webhook URL: show domain + last 4
        if "https://" in credential:
            # Extract domain and last 4 of token
            parts = credential.split("/rest/")
            if len(parts) > 1:
                domain = parts[0]
                rest = parts[1]
                last_4 = rest[-4:] if len(rest) >= 4 else "****"
                return f"{domain}/rest/.../{last_4}"
        return f"...{credential[-4:]}" if len(credential) > 4 else "****"
    elif provider in ("hubspot", "hs"):
        # token: show prefix + last 4
        if credential.startswith("pat-"):
            last_4 = credential[-4:] if len(credential) > 4 else "****"
            return f"pat-...{last_4}"
        return f"...{credential[-4:]}" if len(credential) > 4 else "****"
    return "***"


async def _test_bitrix24_webhook(webhook_url: str) -> tuple[bool, str]:
    """Lightweight test: call CRM.contact.list as a basic connectivity check.

    Returns (success, reason_or_empty_string).
    """
    try:
        # Extract base URL and validate format
        if not re.search(r"https?://.*\.bitrix24\.(com|de|fr|ru)", webhook_url):
            return False, "URL does not look like a Bitrix24 webhook"

        url = f"{webhook_url.rstrip('/')}/crm.contact.list.json?limit=1"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={})
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

            # Bitrix24 returns status_code 200 even for invalid tokens; check response body
            if response.status_code >= 400:
                error = body.get("error") or response.reason_phrase or "HTTP error"
                return False, f"HTTP {response.status_code}: {error}"

            # Check for Bitrix24 error response (they use status_code 200 with error in body)
            if "error" in body or "error_description" in body:
                error = body.get("error_description") or body.get("error") or "Unknown error"
                return False, f"Bitrix24 error: {error}"

            # If we got a successful response with result, connection works
            if "result" in body:
                return True, ""

            # Ambiguous response but no error
            return True, ""

    except httpx.TimeoutException:
        return False, "Connection timed out (webhook URL may be invalid or server down)"
    except Exception as e:
        logger.debug(f"Bitrix24 test error: {e}")
        return False, f"Connection failed: {str(e)}"


async def _test_hubspot_token(access_token: str) -> tuple[bool, str]:
    """Lightweight test: call GET /crm/v3/objects/contacts?limit=1 to validate token.

    Returns (success, reason_or_empty_string).
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/contacts?limit=1"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

            if response.status_code == 401:
                return False, "Unauthorized (invalid or expired token)"
            elif response.status_code >= 400:
                error = body.get("message") or response.reason_phrase or "HTTP error"
                return False, f"HTTP {response.status_code}: {error}"

            # HubSpot returns 200 with contacts list for valid token
            if "results" in body or "objects" in body:
                return True, ""

            return True, ""

    except httpx.TimeoutException:
        return False, "Connection timed out (HubSpot API may be down)"
    except Exception as e:
        logger.debug(f"HubSpot test error: {e}")
        return False, f"Connection failed: {str(e)}"


# ─── POST /api/connections/bitrix24 ───

@router.post("/bitrix24")
async def connect_bitrix24(
    body: Bitrix24ConnectInput,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> ConnectionResponse:
    """
    Connect Bitrix24 webhook URL for current user (T012).

    Validates webhook format, encrypts + stores in CrmConnection, returns connection info.
    If connection already exists for this user+provider, updates it.
    """
    logger.debug(f"connect_bitrix24 invoked by user={current_user.get('email')}")

    webhook_url = body.webhook_url.strip()

    # Validate webhook format
    if not re.search(r"https?://.*\.bitrix24\.(com|de|fr|ru)", webhook_url):
        raise HTTPException(status_code=400, detail="Invalid Bitrix24 webhook URL format")

    # Encrypt credential
    encrypted = encrypt_credentials(webhook_url)

    # Upsert into CrmConnection
    try:
        user_uuid = derive_user_uuid(current_user.get("id"))

        # Check if connection already exists
        stmt = select(CrmConnection).where(
            (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "bitrix24")
        )
        result = await db.execute(stmt)
        conn = result.scalar_one_or_none()

        if conn:
            # Update existing
            conn.encrypted_credentials = encrypted
            conn.last_validated_at = None  # will be set by test
            logger.debug(f"Updated Bitrix24 connection for user {user_uuid}")
        else:
            # Create new
            conn = CrmConnection(
                id=uuid.uuid4(),
                user_id=user_uuid,
                provider="bitrix24",
                auth_type="webhook",
                encrypted_credentials=encrypted,
                created_at=datetime.utcnow(),
            )
            db.add(conn)
            logger.debug(f"Created Bitrix24 connection for user {user_uuid}")

        await db.commit()

        return ConnectionResponse(
            id=str(conn.id),
            provider="bitrix24",
            connected=True,  # We don't know if it actually works until test
            auth_type="webhook",
            created_at=conn.created_at.isoformat() if conn.created_at else None,
            last_validated_at=conn.last_validated_at.isoformat() if conn.last_validated_at else None,
            masked_credential=_mask_credential(webhook_url, "bitrix24"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to store Bitrix24 connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store connection: {str(e)}")


# ─── POST /api/connections/bitrix24/test ───

@router.post("/bitrix24/test")
async def test_bitrix24_connection(
    body: Bitrix24TestInput,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Test Bitrix24 connection (T012).

    If webhook_url provided in body, tests that URL.
    Otherwise, retrieves stored connection and tests it.
    """
    logger.debug(f"test_bitrix24_connection invoked by user={current_user.get('email')}")

    webhook_url = body.webhook_url

    if not webhook_url:
        # Try to get stored connection
        try:
            user_uuid = derive_user_uuid(current_user.get("id"))

            stmt = select(CrmConnection).where(
                (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "bitrix24")
            )
            result = await db.execute(stmt)
            conn = result.scalar_one_or_none()

            if not conn or not conn.encrypted_credentials:
                raise HTTPException(status_code=400, detail="No stored Bitrix24 connection. Provide webhook_url or connect first.")

            webhook_url = decrypt_credentials(conn.encrypted_credentials)

        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Failed to retrieve stored connection: {e}")
            raise HTTPException(status_code=400, detail="No stored connection and no webhook_url provided")

    # Test connectivity
    success, reason = await _test_bitrix24_webhook(webhook_url)

    # If test succeeds and we have a stored connection, update last_validated_at
    if success and not body.webhook_url:
        try:
            user_uuid = derive_user_uuid(current_user.get("id"))

            stmt = select(CrmConnection).where(
                (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "bitrix24")
            )
            result = await db.execute(stmt)
            conn = result.scalar_one_or_none()
            if conn:
                conn.last_validated_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.debug(f"Failed to update last_validated_at: {e}")

    return {
        "provider": "bitrix24",
        "connected": success,
        "reason": reason if not success else "",
    }


# ─── POST /api/connections/hubspot ───

@router.post("/hubspot")
async def connect_hubspot(
    body: HubSpotConnectInput,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> ConnectionResponse:
    """
    Connect HubSpot private app token for current user (T012).

    Stores access token encrypted in CrmConnection, returns connection info.
    If connection already exists, updates it.
    """
    logger.debug(f"connect_hubspot invoked by user={current_user.get('email')}")

    access_token = body.access_token.strip()

    if not access_token:
        raise HTTPException(status_code=400, detail="HubSpot access token is required")

    # Encrypt credential
    encrypted = encrypt_credentials(access_token)

    # Upsert into CrmConnection
    try:
        user_uuid = derive_user_uuid(current_user.get("id"))

        # Check if connection already exists
        stmt = select(CrmConnection).where(
            (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "hubspot")
        )
        result = await db.execute(stmt)
        conn = result.scalar_one_or_none()

        if conn:
            # Update existing
            conn.encrypted_credentials = encrypted
            conn.last_validated_at = None  # will be set by test
            logger.debug(f"Updated HubSpot connection for user {user_uuid}")
        else:
            # Create new
            conn = CrmConnection(
                id=uuid.uuid4(),
                user_id=user_uuid,
                provider="hubspot",
                auth_type="oauth",  # Note: private app, but stored as oauth type per model
                encrypted_credentials=encrypted,
                created_at=datetime.utcnow(),
            )
            db.add(conn)
            logger.debug(f"Created HubSpot connection for user {user_uuid}")

        await db.commit()

        return ConnectionResponse(
            id=str(conn.id),
            provider="hubspot",
            connected=True,  # We don't know if it actually works until test
            auth_type="oauth",
            created_at=conn.created_at.isoformat() if conn.created_at else None,
            last_validated_at=conn.last_validated_at.isoformat() if conn.last_validated_at else None,
            masked_credential=_mask_credential(access_token, "hubspot"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to store HubSpot connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store connection: {str(e)}")


# ─── POST /api/connections/hubspot/test ───

@router.post("/hubspot/test")
async def test_hubspot_connection(
    body: BaseModel | dict = None,
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Test HubSpot connection (T012).

    If access_token provided in body, tests that token.
    Otherwise, retrieves stored connection and tests it.
    """
    logger.debug(f"test_hubspot_connection invoked by user={current_user.get('email')}")

    access_token = None

    # Try to extract token from body if provided
    if body:
        if isinstance(body, dict):
            access_token = body.get("access_token")
        else:
            # Try as Pydantic model
            try:
                access_token = getattr(body, "access_token", None)
            except Exception:
                pass

    if not access_token:
        # Try to get stored connection
        try:
            user_uuid = derive_user_uuid(current_user.get("id"))

            stmt = select(CrmConnection).where(
                (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "hubspot")
            )
            result = await db.execute(stmt)
            conn = result.scalar_one_or_none()

            if not conn or not conn.encrypted_credentials:
                raise HTTPException(status_code=400, detail="No stored HubSpot connection. Provide access_token or connect first.")

            access_token = decrypt_credentials(conn.encrypted_credentials)

        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Failed to retrieve stored connection: {e}")
            raise HTTPException(status_code=400, detail="No stored connection and no access_token provided")

    # Test connectivity
    success, reason = await _test_hubspot_token(access_token)

    # If test succeeds and we have a stored connection, update last_validated_at
    if success and not body:
        try:
            user_uuid = derive_user_uuid(current_user.get("id"))

            stmt = select(CrmConnection).where(
                (CrmConnection.user_id == user_uuid) & (CrmConnection.provider == "hubspot")
            )
            result = await db.execute(stmt)
            conn = result.scalar_one_or_none()
            if conn:
                conn.last_validated_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.debug(f"Failed to update last_validated_at: {e}")

    return {
        "provider": "hubspot",
        "connected": success,
        "reason": reason if not success else "",
    }


# ─── GET /api/connections ───

@router.get("")
async def list_connections(
    current_user: dict = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
) -> ConnectionListResponse:
    """
    List current user's connections (T012).

    Returns all stored CRM connections for this user with masked credentials.
    """
    logger.debug(f"list_connections for user={current_user.get('email')}")

    try:
        user_uuid = derive_user_uuid(current_user.get("id"))

        stmt = select(CrmConnection).where(CrmConnection.user_id == user_uuid)
        result = await db.execute(stmt)
        conns = result.scalars().all()

        items: list[ConnectionResponse] = []
        for conn in conns:
            try:
                decrypted = decrypt_credentials(conn.encrypted_credentials) if conn.encrypted_credentials else ""
                masked = _mask_credential(decrypted, conn.provider)
            except Exception as e:
                logger.debug(f"Failed to decrypt connection {conn.id}: {e}")
                masked = "(error decrypting)"

            items.append(
                ConnectionResponse(
                    id=str(conn.id),
                    provider=conn.provider,
                    connected=conn.last_validated_at is not None,
                    auth_type=conn.auth_type or "webhook",
                    created_at=conn.created_at.isoformat() if conn.created_at else None,
                    last_validated_at=conn.last_validated_at.isoformat() if conn.last_validated_at else None,
                    masked_credential=masked,
                )
            )

        return ConnectionListResponse(connections=items)

    except Exception as e:
        logger.exception(f"list_connections failed: {e}")
        # Graceful: return empty list
        return ConnectionListResponse(connections=[])
