"""
HubSpot API client implementing CrmClient (Python).

Uses httpx async.

Mirrors src/crm/hubspot.ts EXACTLY:
- v3 objects POST /crm/v3/objects/{contacts,deals,tasks}
- associations arrays (HUBSPOT_DEFINED + typeId 3 for deal-contact, 216 for task-deal)
- hs_timestamp = ms epoch UTC at 09:00Z
- properties: firstname/lastname/jobtitle/company/email/hs_linkedin_url , dealname/description/pipeline/dealstage , hs_task_*
- name split, error msgs, {id: str} returns

See ARCHITECTURE.md, contracts/crm-client.md, crm_client.py for details.
Constructor takes access token (Bearer).
"""

from datetime import datetime
from typing import Any

import httpx

from .types import CrmClient, CrmContactInput, CrmDealInput, CrmTaskInput, CrmId


class HubspotClient:
    """Implements CrmClient Protocol for HubSpot."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, access_token: str):
        if not access_token or not isinstance(access_token, str):
            raise ValueError("HubSpot access token is required")
        self.access_token = access_token

    # ─── Core HTTP ───────────────────────────────────────────────────────────────

    async def _call(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=body, headers=headers)
            except Exception as err:
                raise RuntimeError(f"Network error calling HubSpot ({path}): {err}") from err

            try:
                body_json: dict[str, Any] = response.json()
            except Exception:
                body_json = {}

            if response.status_code >= 400:
                msg = body_json.get("message") or body_json.get("error") or response.reason_phrase
                corr = f" (corr: {body_json.get('correlationId')})" if body_json.get("correlationId") else ""
                raise RuntimeError(f"HubSpot HTTP {response.status_code} on {path}: {msg}{corr}")

            if body_json and body_json.get("status") == "error":
                raise RuntimeError(
                    f"HubSpot API error on {path}: {body_json.get('message', 'unknown error')}"
                )

            if "id" not in body_json:
                raise RuntimeError(f"HubSpot returned no id for {path}")

            return body_json

    # ─── Helpers ─────────────────────────────────────────────────────────────────

    def _split_name(self, full: str) -> tuple[str, str]:
        """Split name like Bitrix24Client (first + rest as last)."""
        parts = full.strip().split()
        return (
            parts[0] if parts else full,
            " ".join(parts[1:]) if len(parts) > 1 else "",
        )

    def _to_hubspot_timestamp(self, due_date: str) -> int:
        """Convert YYYY-MM-DD or ISO to ms-since-epoch UTC at 09:00Z (parity with Bitrix)."""
        base = due_date.split("T")[0] if "T" in due_date else due_date
        iso = f"{base}T09:00:00.000Z"
        try:
            # datetime.fromisoformat needs care for Z; use timestamp
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception:
            return int(datetime.utcnow().timestamp() * 1000)

    # ─── Contact ─────────────────────────────────────────────────────────────────

    async def createContact(self, contact: CrmContactInput) -> CrmId:
        if isinstance(contact, dict):
            name = contact.get("name", "")
            role = contact.get("role")
            company = contact.get("company", "")
            email = contact.get("email")
            linkedin = contact.get("linkedin")
        else:
            name = contact.name
            role = contact.role
            company = contact.company
            email = contact.email
            linkedin = contact.linkedin

        firstname, lastname = self._split_name(name)

        properties: dict[str, str] = {
            "firstname": firstname,
            "lastname": lastname,
            "company": company,
        }
        if role:
            properties["jobtitle"] = role
        if email:
            properties["email"] = email
        if linkedin:
            properties["hs_linkedin_url"] = linkedin

        result = await self._call(
            "/crm/v3/objects/contacts",
            {"properties": {k: v for k, v in properties.items() if v}},
        )

        return {"id": result["id"]}

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

        properties: dict[str, str] = {
            "dealname": title,
            "description": comments,
            "pipeline": "default",
            "dealstage": "appointmentscheduled",
        }

        body = {
            "properties": properties,
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 3,
                        }
                    ],
                }
            ],
        }

        result = await self._call("/crm/v3/objects/deals", body)

        return {"id": result["id"]}

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

        hs_timestamp = self._to_hubspot_timestamp(due_date)

        properties: dict[str, Any] = {
            "hs_task_subject": title,
            "hs_task_body": description,
            "hs_timestamp": hs_timestamp,
            "hs_task_status": "NOT_STARTED",
        }

        associations = [
            {
                "to": {"id": deal_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 216,
                    }
                ],
            }
        ]

        result = await self._call(
            "/crm/v3/objects/tasks",
            {"properties": properties, "associations": associations},
        )

        return {"id": result["id"]}
