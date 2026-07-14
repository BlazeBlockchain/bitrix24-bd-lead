"""
CRM adapters package.

Exports Python implementations of CrmClient (Protocol) for Bitrix24 and HubSpot.
Factory mirrors src/crm/index.ts (T003 readiness).

Usage:
    from app.adapters.crm import create_crm_client
    client = create_crm_client("bitrix24", webhook_url)
    result = await client.createContact({...})
"""

from .types import (
    CrmClient,
    CrmContact,
    CrmDeal,
    CrmTask,
    CrmContactInput,
    CrmDealInput,
    CrmTaskInput,
    CrmId,
)
from .bitrix24 import Bitrix24Client
from .hubspot import HubspotClient

__all__ = [
    "CrmClient",
    "CrmContact",
    "CrmDeal",
    "CrmTask",
    "CrmContactInput",
    "CrmDealInput",
    "CrmTaskInput",
    "CrmId",
    "Bitrix24Client",
    "HubspotClient",
    "create_crm_client",
]

type CrmProvider = str  # 'bitrix24' | 'hubspot'


def create_crm_client(provider: CrmProvider = "bitrix24", config: str = "", current_user: dict | None = None) -> CrmClient:
    """Factory for CrmClient (Bitrix24/HubSpot).

    config: plaintext webhook URL or access token (after vault resolution).
    current_user: optional (T006) — if provided and no config, resolves via token vault
                  using current_user + provider (per CrmConnection).

    Defaults to bitrix24 for back-compat with existing MCP.
    Token resolution: prefer explicit config (from ?token or vault.resolve in caller);
    falls back to per-user vault lookup when current_user passed (see token_vault.py).
    """
    if not config and current_user:
        # T006: resolve from vault (envelope decrypt per current_user + provider)
        # Lazy import to avoid cycles (vault may be used by main/service too).
        # Removed settings-fallback bypass per review finding A2 — vault must be fail-closed.
        from app.services.token_vault import resolve_token
        config = resolve_token(current_user, provider)

    if not config:
        # Original T004 stub fallback (settings)
        from app.config import settings
        if provider == "hubspot":
            config = settings.HUBSPOT_ACCESS_TOKEN
        else:
            config = settings.BITRIX24_WEBHOOK_URL

    if provider == "hubspot":
        return HubspotClient(config)
    return Bitrix24Client(config)
