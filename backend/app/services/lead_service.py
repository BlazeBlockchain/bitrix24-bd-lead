"""
Lead orchestration service (T008).

Centralizes the exact lead creation flow previously inline in main.py /push
(and mirroring src/tool.ts:executeBdLead):

  createContact -> createDeal (with contactId) -> 3x createTask (dueDate +4/+9/+14, dealId)

- Uses create_crm_client(provider, token) EXACTLY (no direct adapter usage).
- Simple date helpers here (moved from duplicated _add_days stub).
- Returns core result dict: {contact_id, deal_id, task1/2/3: {id, date}}
- Accepts LeadPushInput (Pydantic) or plain dict (stub; full models + validation ready per T009).
- T007: LLM enrichment (via llm_service.generate_enrichment) called BEFORE CrmClient ops to
  produce company_snapshot + personalized_opener + rich follow-up tasks+rationale.
  These replace stub text in deal comments + task descriptions (CrmClient call shapes + dates + linking 100% unchanged).
  Enriched data also returned for preview/history (non-breaking extra fields).
- current_user drives memory context injection (T006 vault + profiles; T009 models ready for real query).
- T009: models (Lead, UserMemoryProfile, etc) + migration ready for persist + queries (T010+).

All CrmClient calls remain camelCase, pass dicts (supported by adapters), use string IDs.
"""

from datetime import datetime, timedelta
from typing import Any

from app.adapters.crm import create_crm_client
from app.services.llm_service import generate_enrichment


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
    db: Any = None,  # AsyncSession | None; using Any to avoid import cycles (T010)
) -> dict[str, Any]:
    """Create contact + deal + 3 follow-up tasks via CrmClient.

    Exact flow and field construction as exercised by current /push stub.
    current_user passed for future (T009+) per-user context / auditing (not used in CRM calls here).

    Args:
        lead_input: Pydantic model or dict with lead info
        provider: 'bitrix24' or 'hubspot'
        token: plaintext CRM token/webhook
        current_user: dict with user id/email for memory context
        db: optional AsyncSession for usage ledger persistence (T010)
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

    # T007: Call enrichment BEFORE any CrmClient (injects memory context from current_user).
    # Uses structured output; falls back to mocks if no keys. Rich data used for CRM text.
    # CrmClient flow, dates, linking, return ids shape remain EXACT and untouched.
    # T010: Pass db for usage ledger persistence (non-fatal if not provided)
    enriched = await generate_enrichment(data, current_user=current_user, db=db)

    # T006: pass current_user so factory can resolve via vault if needed (token here is plaintext resolved upstream or override).
    client = create_crm_client(provider, token, current_user=current_user)

    # 1. Contact (exact dict shape used in main stub + supported by both adapters)
    contact = await client.createContact({
        "name": contact_name,
        "role": contact_role,
        "company": company_name,
    })

    # 2. Deal (now uses LLM personalized_opener + snapshot for comments; shape identical)
    opener = enriched.get("personalized_opener", "")
    snapshot = enriched.get("company_snapshot", "")
    deal_comments = (
        f"AI Snapshot: {snapshot}\n\n"
        f"Personalized Opener:\n{opener}\n\n"
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

    # 3. Tasks with cadence dates (exact +4/9/14 from tool.ts and stub).
    # Descriptions now from LLM follow_ups (rich + rationale); titles/dates/CRM linking unchanged.
    date1 = _add_days(4)
    date2 = _add_days(9)
    date3 = _add_days(14)

    fu = enriched.get("follow_ups", [])
    t1 = fu[0] if len(fu) > 0 else {}
    t2 = fu[1] if len(fu) > 1 else {}
    t3 = fu[2] if len(fu) > 2 else {}

    task1 = await client.createTask({
        "title": t1.get("title", "Follow-up 1 — Check + Connect"),
        "description": t1.get("description") or f"Check email + connect on LinkedIn for {contact_name} at {company_name}.",
        "dueDate": date1,
        "dealId": deal["id"],
    })
    task2 = await client.createTask({
        "title": t2.get("title", "Follow-up 2 — Short Bump"),
        "description": t2.get("description") or f"Short bump for {signal_type}.",
        "dueDate": date2,
        "dealId": deal["id"],
    })
    task3 = await client.createTask({
        "title": t3.get("title", "Follow-up 3 — Close the Loop"),
        "description": t3.get("description") or f"Close on: {pain_point}",
        "dueDate": date3,
        "dealId": deal["id"],
    })

    # Core result shape (matches executeBdLead / prior inline return) + T007 enriched for preview/history.
    # Extra fields are additive (no breakage to callers expecting ids).
    return {
        "contact_id": contact["id"],
        "deal_id": deal["id"],
        "task1": {"id": task1["id"], "date": date1},
        "task2": {"id": task2["id"], "date": date2},
        "task3": {"id": task3["id"], "date": date3},
        "enriched_preview": {
            "company_snapshot": enriched.get("company_snapshot"),
            "personalized_opener": enriched.get("personalized_opener"),
            "follow_ups": enriched.get("follow_ups"),
            "model_used": enriched.get("model_used"),
            "memory_note": enriched.get("memory_note"),
        },
    }
