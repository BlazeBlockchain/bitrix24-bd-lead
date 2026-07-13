"""
Parallel Python interface definition for CrmClient.

This is the canonical contract for the future FastAPI backend (T004/T008+),
so that adapters (bitrix24.py, hubspot.py) and orchestration exactly match
the TypeScript version in src/crm/types.ts and contracts/crm-client.md.

Source of truth: specs/004-ai-bd-assistant/contracts/crm-client.md
Backend location target (per plan.md): backend/app/adapters/crm/ or similar.

Usage in backend:
- Implement as classes satisfying this Protocol.
- Convert to/from Pydantic models at API boundaries if desired.
- Keep field names and semantics identical.

No runtime dependencies for this definition file.
"""

from dataclasses import dataclass
from typing import Optional, Protocol, TypedDict


# ─── Data types (mirror TS interfaces exactly) ─────────────────────────────────

@dataclass
class CrmContact:
    name: str
    role: Optional[str] = None
    company: str
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


# TypedDict variants for cases where dicts are preferred over dataclasses
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


# ─── Client interface (Protocol for structural typing) ─────────────────────────

class CrmClient(Protocol):
    """CRM abstraction. Implement for Bitrix24, HubSpot, etc.

    Method names kept in camelCase to exactly mirror the TS contract
    (future Python code may alias to snake_case internally).
    Return dicts use {'id': str} to match TS { id: string }.
    """

    def createContact(self, contact: CrmContact | CrmContactDict) -> dict[str, str]:
        """Create contact. Must return {'id': '123'} (string ID)."""
        ...

    def createDeal(self, deal: CrmDeal | CrmDealDict) -> dict[str, str]:
        """Create deal associated to contact. Return {'id': '123'}."""
        ...

    def createTask(self, task: CrmTask | CrmTaskDict) -> dict[str, str]:
        """Create task linked to deal. Return {'id': '123'}."""
        ...


# ─── Bitrix24 Adapter Notes (for implementers, copied from contract) ───────────
#
# - Uses existing logic from (refactored) TS Bitrix24Client.
# - Field mappings to preserve:
#   - Contact: NAME / LAST_NAME (split from .name), POST=role, COMPANY_TITLE=company
#   - Deal: TITLE, CONTACT_ID (numeric coercion ok), COMMENTS
#   - Task: TITLE, DESCRIPTION, DEADLINE=`${dueDate}T09:00:00+00:00`,
#           RESPONSIBLE_ID (from webhook), UF_CRM_TASK=[f"D_{dealId}"]
# - Error handling + HTTP shape must match the TS call() implementation.
# - IDs returned as strings.
#
# ─── HubSpot Adapter Notes ─────────────────────────────────────────────────────
#
# - v3 objects: contacts, deals, tasks
# - Use associations for linking contact<->deal, deal<->task
# - hs_timestamp = due date in ms epoch UTC for tasks
# - See contracts/crm-client.md for details.


# Convenience type for results (optional)
CrmId = dict[str, str]  # {'id': '...' }
