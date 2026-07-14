"""
CRM Token Vault (T006).

Per-user envelope encryption / resolution for CRM credentials (webhook URLs or access tokens).

- Stores/encrypts under CrmConnection (user_id + provider unique).
- Resolves using current_user (from get_current_user) + provider.
- Simple envelope encryption stub: master KEK from settings (Fernet); real envelope will use
  per-connection DEK wrapped by KEK (or KMS) + store {wrapped_dek, ciphertext} in encrypted_credentials.
- Prepares for T009 (real DB queries via CrmConnection model + AsyncSession).
- Keeps CrmClient usage unchanged: callers always pass a plaintext token str (after resolve/decrypt).

Current behavior (post T005/T008):
- /push still accepts ?token= override (for demo / web stub continuity).
- Vault resolve falls back to settings in DEBUG when no stored conn (keeps existing flows).
- Later: connect endpoints (T006/T012) will call store; /push and service will not need ?token once conn saved.

Token injection clarification (addressed):
  User JWT (auth via get_current_user) is orthogonal to CRM tokens.
  Vault does lookup: CrmConnection by (current_user["id"], provider) -> decrypt -> token.
  The resolved token is injected only into CrmClient ctor (server-side, never to client/web).
  ?token override is dev-only convenience (still separated from JWT).
"""

import base64
import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


def derive_user_uuid(user_id: Any) -> "uuid.UUID":
    """Map a current_user['id'] to a stable UUID for CrmConnection.user_id lookups.

    current_user['id'] is a real UUID once real auth (T005 full) is wired, but the
    T005 stub can hand back non-UUID ids (e.g. "stub-user-00000000-...",
    "stub-from-token", or arbitrary JWT `sub` claims). Those must NOT all collapse
    onto one fixed placeholder UUID — that would let unrelated stub identities read
    (and overwrite, via the connect endpoints' upsert) each other's stored CRM
    credentials. Instead, deterministically derive a UUID per distinct id string via
    uuid5, so the mapping is stable (same input -> same output, needed so store and
    lookup agree) while still keeping distinct users' rows distinct.
    """
    import uuid as _uuid

    s = str(user_id) if user_id is not None else ""
    try:
        return _uuid.UUID(s)
    except (ValueError, AttributeError, TypeError):
        return _uuid.uuid5(_uuid.NAMESPACE_OID, s or "anonymous-stub-user")


def _get_fernet() -> Fernet:
    """Build Fernet from settings.ENCRYPTION_KEK.

    Accepts raw string or base64url (32-byte). For dev convenience, derives if short.
    This is the "envelope" master key stub.
    """
    raw = settings.ENCRYPTION_KEK or "dev-encryption-kek-change-me-32bytes-min-for-t006-vault!!"
    # Normalize to 32-byte key material for Fernet (must be urlsafe b64 of 32 bytes)
    if len(raw) >= 44 and "=" in raw[-2:]:  # looks like b64 Fernet key
        key = raw.encode()
    else:
        # Derive: repeat/pad/truncate to 32 bytes then b64url encode
        key_bytes = (raw.encode("utf-8") * 2)[:32]
        key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key)


def encrypt_credentials(plaintext: str) -> str:
    """Encrypt raw CRM token/URL for storage in CrmConnection.encrypted_credentials.

    Returns base64 string safe for Text/JSON column (stub).
    """
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_credentials(ciphertext: str) -> str:
    """Decrypt from stored encrypted_credentials. Raises on tamper/bad key."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.warning(f"token_vault decrypt failed (bad key/tamper?): {e}")
        # In prod: do not fallback; raise to surface misconfig
        if settings.DEBUG:
            return ciphertext  # dev convenience only
        raise


def resolve_token(
    current_user: dict[str, Any],
    provider: str,
    db: Any = None,
    override: str | None = None,
) -> str:
    """Resolve plaintext CRM token for this user+provider using the vault (T006).

    Sync for T006 (stub + settings/DB not wired). When T009 adds real queries, this will become async
    (or callers will do lookup + decrypt separately) and factory/lead_service will await accordingly.

    Priority:
      1. explicit override (from ?token= in /push for demo/dev)
      2. lookup CrmConnection by current_user["id"] + provider -> decrypt
      3. DEBUG fallback to settings (preserves T004/T005 stub flows until real connect + T009)
      4. error

    db param: AsyncSession from Depends(get_db) — unused in T006 stub (T009 will query).
    current_user: from get_current_user dep (contains "id" etc.)

    Returns the token str suitable for create_crm_client(..., config=token).
    """
    if override:
        logger.debug("token_vault: using override token (demo ?token= path)")
        return override

    user_id = current_user.get("id") or current_user.get("user_id") or "stub-user"
    prov = (provider or settings.DEFAULT_CRM_PROVIDER).lower()

    # --- T009 prep: real lookup (commented; no DB dependency yet to keep T006 isolated) ---
    # if db is not None:
    #     from sqlalchemy import select
    #     from uuid import UUID
    #     from app.models import CrmConnection
    #     try:
    #         uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    #         stmt = select(CrmConnection).where(
    #             CrmConnection.user_id == uid,
    #             CrmConnection.provider == prov,
    #         )
    #         result = await db.execute(stmt)  # becomes real when async
    #         conn: CrmConnection | None = result.scalar_one_or_none()
    #         if conn and conn.encrypted_credentials:
    #             token = decrypt_credentials(conn.encrypted_credentials)
    #             if token:
    #                 logger.debug(f"token_vault: resolved from CrmConnection for user={user_id} provider={prov}")
    #                 return token
    #     except Exception as e:
    #         logger.debug(f"token_vault DB lookup skipped/failed (ok pre-T009): {e}")

    # Stub / demo path (no real store/lookup yet)
    if settings.DEBUG:
        if prov in ("hubspot", "hs"):
            tok = settings.HUBSPOT_ACCESS_TOKEN
            if tok:
                logger.debug("token_vault: DEBUG fallback to HUBSPOT_ACCESS_TOKEN")
                return tok
            # allow tests/mocks to proceed with recognizable stub
            return "demo-hubspot-token-stub-from-vault"
        # bitrix24 default
        tok = settings.BITRIX24_WEBHOOK_URL
        if tok:
            logger.debug("token_vault: DEBUG fallback to BITRIX24_WEBHOOK_URL")
            return tok
        return "https://demo.bitrix24.com/rest/1/demo-token-from-vault/"

    # Production-like without stored connection: force explicit connect first
    raise ValueError(
        f"No CRM token stored for user_id={user_id} provider={prov} "
        "(T006 vault). Use connect flow or pass ?token= override in dev."
    )


async def resolve_stored_token(
    current_user: dict[str, Any],
    provider: str,
    db: Any,
) -> str | None:
    """Look up a real stored CrmConnection (T012 connect flow) and decrypt it.

    Returns the plaintext token/webhook_url if a connection exists for this
    user+provider, else None (caller should fall back to resolve_token's
    override/DEBUG/raise behavior).

    This closes the T006->T012 gap: connect endpoints (app/api/connections.py)
    store via encrypt_credentials(); this reads back via decrypt_credentials()
    using the SAME CrmConnection row (user_id, provider), so the format always
    matches what was stored.
    """
    if db is None:
        return None

    from sqlalchemy import select
    from app.models import CrmConnection

    user_id = current_user.get("id") or current_user.get("user_id")
    prov = (provider or settings.DEFAULT_CRM_PROVIDER).lower()
    if not user_id:
        return None

    # Same derivation as app/api/connections.py uses on store, so lookup agrees
    # with whatever row the connect endpoints created/updated for this user.
    uid = derive_user_uuid(user_id)

    try:
        stmt = select(CrmConnection).where(
            CrmConnection.user_id == uid,
            CrmConnection.provider == prov,
        )
        result = await db.execute(stmt)
        conn = result.scalar_one_or_none()
        if conn and conn.encrypted_credentials:
            token = decrypt_credentials(conn.encrypted_credentials)
            if token:
                logger.debug(f"token_vault: resolved stored CrmConnection for user={user_id} provider={prov}")
                return token
    except Exception as e:
        logger.debug(f"token_vault: resolve_stored_token lookup failed (falling back): {e}")

    return None


# Convenience alias (some call sites may use this name)
resolve_crm_token = resolve_token


def mock_store_token(user_id: str, provider: str, plaintext_token: str) -> str:
    """Test/dev helper: returns what would be stored in CrmConnection.encrypted_credentials.

    Does NOT touch DB (T009). Used for mock vault resolve verification.
    """
    return encrypt_credentials(plaintext_token)
