"""
Bitrix24 API client implementing CrmClient (Python).

Uses httpx async (no new heavy deps beyond requirements).

Mirrors src/crm/bitrix24.ts exactly for field mappings, error handling, dates, linking.
See contracts/crm_client.py notes for Bitrix specifics.

Constructor takes webhook URL (like TS).
"""

import re
from typing import Any

import httpx

from .types import CrmClient, CrmContactInput, CrmDealInput, CrmTaskInput, CrmId


class Bitrix24Client:
    """Implements CrmClient Protocol for Bitrix24."""

    def __init__(self, webhook_url: str):
        # Normalise — remove trailing slash
        self.base_url = webhook_url.rstrip("/")
        # Extract user ID from webhook URL: https://domain/rest/{userId}/{token}/
        match = re.search(r"/rest/(\d+)/", webhook_url)
        self.user_id: int = int(match.group(1)) if match else 1

    # ─── Core HTTP ───────────────────────────────────────────────────────────────

    async def _call(self, method: str, params: dict[str, Any]) -> Any:
        url = f"{self.base_url}/{method}.json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=params)
            except Exception as err:
                raise RuntimeError(f"Network error calling Bitrix24 ({method}): {err}") from err

            try:
                body = response.json()
            except Exception:
                body = {}

            if response.status_code >= 400:
                error = body.get("error") or response.reason_phrase
                desc = body.get("error_description", "")
                raise RuntimeError(
                    f"Bitrix24 HTTP {response.status_code} on {method}: {error} — {desc}"
                )

            if body.get("error"):
                desc = body.get("error_description", "")
                raise RuntimeError(
                    f"Bitrix24 API error on {method}: {body['error']} — {desc}"
                )

            if body.get("result") is None:
                raise RuntimeError(f"Bitrix24 returned no result for {method}")

            return body["result"]

    # ─── Helpers ─────────────────────────────────────────────────────────────────

    def _normalize_date(self, d: str) -> str:
        """Accept YYYY-MM-DD or full ISO; return base date (defensive, matches TS)."""
        return d.split("T")[0] if "T" in d else d

    def _split_name(self, full: str) -> tuple[str, str]:
        parts = full.strip().split()
        first = parts[0] if parts else full
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
        return first, last

    # ─── Contact ─────────────────────────────────────────────────────────────────

    async def createContact(self, contact: CrmContactInput) -> CrmId:
        # Support dataclass or dict
        if isinstance(contact, dict):
            name = contact.get("name", "")
            role = contact.get("role")
            company = contact.get("company", "")
        else:
            name = contact.name
            role = contact.role
            company = contact.company

        first_name, last_name = self._split_name(name)

        result_id = await self._call(
            "crm.contact.add",
            {
                "fields": {
                    "NAME": first_name,
                    "LAST_NAME": last_name,
                    "POST": role,
                    "COMPANY_TITLE": company,
                }
            },
        )

        return {"id": str(result_id)}

    # ─── Deal ─────────────────────────────────────────────────────────────────────

    async def createDeal(self, deal: CrmDealInput) -> CrmId:
        if isinstance(deal, dict):
            title = deal["title"]
            contact_id = deal["contactId"]
            comments = deal["comments"]
        else:
            title = deal.title
            contact_id = deal.contactId
            comments = deal.comments

        result_id = await self._call(
            "crm.deal.add",
            {
                "fields": {
                    "TITLE": title,
                    # Preserve numeric coercion shape
                    "CONTACT_ID": int(contact_id) if contact_id.isdigit() else contact_id,
                    "COMMENTS": comments,
                }
            },
        )

        return {"id": str(result_id)}

    # ─── Task ─────────────────────────────────────────────────────────────────────

    async def createTask(self, task: CrmTaskInput) -> CrmId:
        if isinstance(task, dict):
            title = task["title"]
            description = task["description"]
            due_date = task["dueDate"]
            deal_id = task["dealId"]
        else:
            title = task.title
            description = task.description
            due_date = task.dueDate
            deal_id = task.dealId

        deadline = f"{self._normalize_date(due_date)}T09:00:00+00:00"

        # tasks.task.add returns { task: { id: "123", ... } }
        result = await self._call(
            "tasks.task.add",
            {
                "fields": {
                    "TITLE": title,
                    "DESCRIPTION": description,
                    "DEADLINE": deadline,
                    "RESPONSIBLE_ID": self.user_id,
                    "UF_CRM_TASK": [f"D_{deal_id}"],
                }
            },
        )

        raw_id = result.get("task", {}).get("id", "0")
        return {"id": str(int(raw_id))}
