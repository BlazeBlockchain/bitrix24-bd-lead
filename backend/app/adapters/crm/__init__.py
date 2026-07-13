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


def create_crm_client(provider: CrmProvider = "bitrix24", config: str = "") -> CrmClient:
    """Minimal factory (auth stub: config is webhook or token).

    Defaults to bitrix24 for back-compat with existing MCP.
    Later: select from per-user CrmConnection (encrypted).
    """
    if not config:
        # Lazy to avoid circulars during module load; auth stub for T004
        from app.config import settings
        if provider == "hubspot":
            config = settings.HUBSPOT_ACCESS_TOKEN
        else:
            config = settings.BITRIX24_WEBHOOK_URL
    if provider == "hubspot":
        return HubspotClient(config)
    return Bitrix24Client(config)
