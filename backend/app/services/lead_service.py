"""
Lead orchestration service (T008).

Centralizes the exact lead creation flow previously inline in main.py /push
(and mirroring src/tool.ts:executeBdLead):

  createContact -> createDeal (with contactId) -> 3x createTask (dueDate +4/+9/+14, dealId)

- Uses create_crm_client(provider, token) EXACTLY (no direct adapter usage).
- Simple date helpers here (moved from duplicated _add_days stub).
- Returns core result dict: {contact_id, deal_id, task1/2/3: {id, date}}
- Accepts LeadPushInput (Pydantic) or plain dict (stub; full models + validation in T009).
- Stub descriptions / comments kept explicit (real dynamic + LLM enrichment in T007/T008+).
- Prepares for T009 (will accept/persist Lead + use current_user + real DB).

All CrmClient calls remain camelCase, pass dicts (supported by adapters), use string IDs.
"""

from datetime import datetime, timedelta
from typing import Any

from app.adapters.crm import create_crm_client


def _add_days(n: int) -> str:
    """Simple date helper for follow-up due dates.

    Returns YYYY-MM-DD (UTC based, matches TS addDays + prior stub in main.py).
    Used for CrmTask.dueDate (adapters normalize to required format internally).
    """
    d = datetime.utcnow() + timedelta(days=n)
    return d.strftime("%Y-%m-%d")


async def create_lead_with_followups(
    lead_input: Any,
    provider: str,
    token: str,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    """Create contact + deal + 3 follow-up tasks via CrmClient.

    Exact flow and field construction as exercised by current /push stub.
    current_user passed for future (T009+) per-user context / auditing (not used in CRM calls here).
    """
    # Support Pydantic model (LeadPushInput) or dict (flexible for tests/mocks)
    if hasattr(lead_input, "model_dump"):
        data = lead_input.model_dump()
    elif isinstance(lead_input, dict):
        data = lead_input
    else:
        data = dict(lead_input) if lead_input else {}

    # Resolve fields (defaults match LeadPushInput)
    contact_name = data.get("contact_name", "")
    contact_role = data.get("contact_role", "")
    company_name = data.get("company_name", "")
    deal_name = data.get("deal_name", "")
    signal = data.get("signal", "")
    pain_point = data.get("pain_point", "")
    email_subject = data.get("email_subject", "")
    notes = data.get("notes", "")
    signal_type = data.get("signal_type", "")

    client = create_crm_client(provider, token)

    # 1. Contact (exact dict shape used in main stub + supported by both adapters)
    contact = await client.createContact({
        "name": contact_name,
        "role": contact_role,
        "company": company_name,
    })

    # 2. Deal (comments construction stub; will be enriched by LLM later)
    deal_comments = (
        f"Signal: {signal}\n\n"
        f"Pain Point: {pain_point}\n\n"
        f"Email Subject: {email_subject}\n\n"
        f"Notes:\n{notes}"
    )
    deal = await client.createDeal({
        "title": deal_name,
        "contactId": contact["id"],
        "comments": deal_comments,
    })

    # 3. Tasks with cadence dates (exact +4/9/14 from tool.ts and stub)
    date1 = _add_days(4)
    date2 = _add_days(9)
    date3 = _add_days(14)

    task1 = await client.createTask({
        "title": "Follow-up 1 — Check + Connect",
        "description": f"Stub: check email + connect on LinkedIn for {contact_name} at {company_name}.",
        "dueDate": date1,
        "dealId": deal["id"],
    })
    task2 = await client.createTask({
        "title": "Follow-up 2 — Short Bump",
        "description": f"Stub bump for {signal_type}.",
        "dueDate": date2,
        "dealId": deal["id"],
    })
    task3 = await client.createTask({
        "title": "Follow-up 3 — Close the Loop",
        "description": f"Stub close on: {pain_point}",
        "dueDate": date3,
        "dealId": deal["id"],
    })

    # Core result shape (matches executeBdLead / prior inline return)
    return {
        "contact_id": contact["id"],
        "deal_id": deal["id"],
        "task1": {"id": task1["id"], "date": date1},
        "task2": {"id": task2["id"], "date": date2},
        "task3": {"id": task3["id"], "date": date3},
    }
