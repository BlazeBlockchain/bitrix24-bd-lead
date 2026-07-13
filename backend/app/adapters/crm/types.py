"""
Python CrmClient types and Protocol for backend.

Mirrors exactly:
- specs/004-ai-bd-assistant/contracts/crm_client.py
- specs/004-ai-bd-assistant/contracts/crm-client.md
- src/crm/types.ts

Used by adapters and stub routes. Keep field names/semantics 1:1 with TS.
"""

from dataclasses import dataclass
from typing import Optional, Protocol, TypedDict, Union


# ─── Data types (mirror TS interfaces exactly) ─────────────────────────────────

@dataclass
class CrmContact:
    # Required fields first (dataclass rule: no non-default after default)
    name: str
    company: str
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None


@dataclass
class CrmDeal:
    title: str
    contactId: str
    comments: str


@dataclass
class CrmTask:
    title: str
    description: str
    dueDate: str  # YYYY-MM-DD or ISO
    dealId: str


# TypedDict for dict usage (flexible for API input)
class CrmContactDict(TypedDict, total=False):
    name: str
    role: Optional[str]
    company: str
    email: Optional[str]
    linkedin: Optional[str]


class CrmDealDict(TypedDict):
    title: str
    contactId: str
    comments: str


class CrmTaskDict(TypedDict):
    title: str
    description: str
    dueDate: str
    dealId: str


CrmContactInput = Union[CrmContact, CrmContactDict]
CrmDealInput = Union[CrmDeal, CrmDealDict]
CrmTaskInput = Union[CrmTask, CrmTaskDict]


# ─── Client interface (Protocol) ───────────────────────────────────────────────

class CrmClient(Protocol):
    """CRM abstraction. Implement for Bitrix24, HubSpot, etc.

    Method names kept in camelCase to exactly mirror the TS contract.
    Return dicts use {'id': str} to match TS { id: string }.
    """

    async def createContact(self, contact: CrmContactInput) -> dict[str, str]:
        """Create contact. Must return {'id': '123'} (string ID)."""
        ...

    async def createDeal(self, deal: CrmDealInput) -> dict[str, str]:
        """Create deal associated to contact. Return {'id': '123'}."""
        ...

    async def createTask(self, task: CrmTaskInput) -> dict[str, str]:
        """Create task linked to deal. Return {'id': '123'}."""
        ...


# Convenience
CrmId = dict[str, str]  # {'id': '...' }
