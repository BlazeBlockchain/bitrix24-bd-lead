"""
LLM Proxy Service (T007).

Primary: Gemini 2.5 Flash (google-generativeai) with structured JSON.
Fallback: Claude Haiku 3.5 (anthropic) .

- Prompt builder injects:
  - user memory context (stub for T006 vault/profiles + tone_samples; real later)
  - lead brief (company, signal, pain, style hints)
  - style from "history" (stub)
- Structured output: {company_snapshot, personalized_opener, follow_ups: [{title, description, due_in_days, rationale}, ...], model_used, ...}
- Per-user budget guards (hard daily cap stub + request size).
- Usage logging to usage_ledger (stub: logs + dict; real DB in T009).
- Cheap models only; zero-cost mock when no keys or DEBUG.

Integrates into lead_service (for dynamic task/desc generation in CrmClient flow) and future /enrich.
No changes to CrmClient adapters or core orchestration shape.
Mocks used for verif (both "providers").

Refs: ARCHITECTURE §LLM, plan T007, spec FR-003/FR-008/NFR-001, data-model usage_ledger, src/tool.ts task logic.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Budget + usage (per-user stub; T009 will persist to usage_ledger + models) ──
# In-memory for skeleton (process lifetime). Real: Redis + DB ledger per current_user.id
_user_daily_usage: dict[str, dict[str, Any]] = {}  # user_id -> {"date": str, "cents": int, "calls": int}


def _get_user_key(user: dict | None) -> str:
    if not user:
        return "anonymous"
    return str(user.get("id") or user.get("email") or "unknown")


def _check_budget(user: dict | None, estimated_cents: int = 2) -> bool:
    """Hard per-user daily guard (NFR). Returns True if within budget."""
    if settings.DEBUG:
        return True  # allow in dev
    uid = _get_user_key(user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    rec = _user_daily_usage.get(uid, {"date": today, "cents": 0, "calls": 0})
    if rec["date"] != today:
        rec = {"date": today, "cents": 0, "calls": 0}
    if rec["cents"] + estimated_cents > settings.LLM_DAILY_BUDGET_CENTS:
        logger.warning(f"LLM budget exceeded for {uid}: {rec['cents']}+{estimated_cents} > {settings.LLM_DAILY_BUDGET_CENTS}")
        return False
    return True


async def _record_usage(
    user: dict | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_cents: int,
    db: Any = None,  # AsyncSession | None; using Any to avoid import cycles
    lead_id: str | None = None,
) -> None:
    """Log + update stub ledger + persist to DB (T010).

    Mirrors usage_ledger table (id, user_id, lead_id, model, tokens, estimated_cost_cents).

    Args:
        user: current_user dict with id/email
        model: model name (e.g. "gemini-2.5-flash")
        input_tokens, output_tokens: token counts
        cost_cents: estimated cost in cents
        db: optional AsyncSession for DB persistence (T010)
        lead_id: optional UUID string of associated lead (for future attribution)
    """
    uid = _get_user_key(user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if uid not in _user_daily_usage or _user_daily_usage[uid]["date"] != today:
        _user_daily_usage[uid] = {"date": today, "cents": 0, "calls": 0}
    _user_daily_usage[uid]["cents"] += cost_cents
    _user_daily_usage[uid]["calls"] += 1

    # Structured log for observability
    logger.info(
        "LLM_USAGE: user=%s model=%s in=%d out=%d cost_cents=%d daily_total=%d calls=%d",
        uid, model, input_tokens, output_tokens, cost_cents,
        _user_daily_usage[uid]["cents"], _user_daily_usage[uid]["calls"],
    )

    # T010: persist to DB if db session available (non-fatal if fails)
    if db:
        try:
            # Import here to avoid circular dependency
            from app.models.usage_ledger import UsageLedger
            from app.services.token_vault import derive_user_uuid

            # Convert user id to UUID using the SAME derivation as the read path
            # (app/api/usage.py) and the T012/T024 patterns (connections.py,
            # memory.py). Previously this used a bespoke uuid.UUID(id_str) parse
            # that silently collapsed almost every stub user id (e.g.
            # "stub-user-00000000-...", "stub-from-token") onto one hardcoded
            # placeholder UUID whenever the raw string wasn't itself a valid
            # UUID -- since derive_user_uuid() instead falls back to a
            # deterministic uuid5() hash of the id string, the write path and
            # read path disagreed and GET /api/usage/summary would show zero
            # usage even though rows existed.
            raw_user_id = (user or {}).get("id") if user else None
            user_id = derive_user_uuid(raw_user_id or "00000000-0000-0000-0000-000000000001")

            # Parse lead_id if provided
            lead_uuid = None
            if lead_id:
                try:
                    lead_uuid = uuid.UUID(lead_id) if isinstance(lead_id, str) else lead_id
                except Exception:
                    pass

            # Create ledger entry
            ledger_entry = UsageLedger(
                id=uuid.uuid4(),
                user_id=user_id,
                lead_id=lead_uuid,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_cents=cost_cents,
                created_at=datetime.utcnow(),
            )
            db.add(ledger_entry)
            await db.commit()
            logger.debug(f"Persisted usage ledger entry for user {user_id} with model {model}")
        except Exception as e:
            logger.warning(f"Non-fatal: failed to persist usage ledger: {e}")
            try:
                await db.rollback()
            except Exception:
                pass


# ─── Memory context injection (T006 vault + profiles stub) ─────────────────────
def _build_memory_context(user: dict | None, memory_context: dict | None = None) -> str:
    """Injects user memory / profile for personalization (per ARCH + spec FR-005).
    Stub now: static + derived from current_user (T006 will query user_memory_profiles + recent outreach_history via vault).
    Real later: tone_samples (opener/outcome), icp_industries, typical_cadence, profile_embedding recall.
    """
    if memory_context:
        # Future hook for passed real context
        tone = memory_context.get("tone", "concise benefit-focused")
        icp = ", ".join(memory_context.get("icp", ["SaaS", "B2B"]))
        cadence = memory_context.get("cadence") or [4, 9, 14]
        cadence_str = "/".join(f"+{c}" for c in cadence)

        # T024: surface real tone samples (if loaded from UserMemoryProfile) so the
        # LLM mimics the user's actual accepted openers rather than a generic label.
        tone_samples = memory_context.get("tone_samples") or []
        samples_str = ""
        if tone_samples:
            examples = "; ".join(
                f'"{ts.get("opener", "")[:160]}"' for ts in tone_samples[:3] if ts.get("opener")
            )
            if examples:
                samples_str = f" Prior accepted openers (mimic this exact style): {examples}."

        return (
            f"User memory: tone={tone}; ICP={icp}; cadence preference={cadence_str} days."
            f"{samples_str} Prior accepted openers used benefit-first language."
        )

    if not user:
        return "No prior memory for this user (first lead). Use professional, direct, value-focused tone."

    # Derive stub from user (email hints or display)
    name = user.get("display_name", "the rep")
    return (
        f"User {name} typical style from history: concise, respectful of time, benefit-first, "
        "references specific signals. Recent tone samples (stub): "
        '"Hi X, saw the launch—here is how we helped Y achieve Z in 6 weeks." '
        "ICP focus: tech/ops leaders in scaling SaaS or infra companies. "
        "Cadence preference: +4/+9/+14 days."
    )


# ─── Prompt builder ───────────────────────────────────────────────────────────
def _build_prompt(lead_brief: dict, memory_ctx: str) -> str:
    """Builds the system+user prompt for structured enrichment.
    Includes lead brief + injected memory + explicit JSON contract + 3-task requirement.
    """
    company = lead_brief.get("company_name", "Acme Corp")
    contact = lead_brief.get("contact_name", "Decision Maker")
    role = lead_brief.get("contact_role", "Head of Ops")
    signal = lead_brief.get("signal", "recent trigger")
    signal_type = lead_brief.get("signal_type", "new_launch")
    pain = lead_brief.get("pain_point", "process friction")
    email_subj = lead_brief.get("email_subject", "Intro")
    notes = lead_brief.get("notes", "")

    return f"""You are an expert B2B BD assistant for a non-technical sales rep. Generate a personalized lead enrichment.

MEMORY CONTEXT (inject style/tone/ICP):
{memory_ctx}

LEAD BRIEF:
- Company: {company}
- Contact: {contact} ({role})
- Buying signal: {signal} (type: {signal_type})
- Pain point: {pain}
- Suggested subject: {email_subj}
- Notes: {notes}

REQUIREMENTS:
- company_snapshot: 1-2 sentence factual snapshot based on public signal + why now.
- personalized_opener: short cold email opener (2-4 sentences) in user's tone from memory. Address contact by first name. Reference signal directly. Benefit-focused, no hype.
- follow_ups: EXACTLY 3 objects with:
  title (e.g. "Follow-up 1 — Check + Connect")
  description (actionable steps, 2-4 sentences, use memory tone, reference contact/company/signal)
  due_in_days: 4, 9, 14 respectively
  rationale (1 sentence why this timing + why this action)
- Keep total output short. Never mention guidelines.

Respond ONLY with a single valid minified JSON object exactly matching:
{{"company_snapshot": "...", "personalized_opener": "...", "follow_ups": [{{"title": "...", "description": "...", "due_in_days": 4, "rationale": "..."}}, ...] }}
No prose, no ```json, no extra keys.
"""


# ─── Structured JSON parser (defensive) ───────────────────────────────────────
def _parse_structured_json(text: str) -> dict[str, Any]:
    """Extract + validate JSON. Falls back to minimal if malformed."""
    text = text.strip()
    if text.startswith("```"):
        # strip fences
        text = text.split("```", 2)[1] if "```" in text else text
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except Exception:
        # last resort: find first { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except Exception:
                data = {}
        else:
            data = {}

    # Normalize shape (match UI_UX + ARCH expectation + BdLeadResult prep)
    snapshot = data.get("company_snapshot") or data.get("snapshot") or "Company scaling after recent signal."
    opener = data.get("personalized_opener") or data.get("opener") or "Hi there, saw the update at the company."
    raw_tasks = data.get("follow_ups") or data.get("tasks") or data.get("followUps") or []
    tasks = []
    defaults = [
        ("Follow-up 1 — Check + Connect", 4, "Prompt timing after initial signal."),
        ("Follow-up 2 — Short Bump", 9, "Keep momentum without pressure."),
        ("Follow-up 3 — Close the Loop", 14, "Address pain point directly."),
    ]
    for i, d in enumerate(defaults):
        if i < len(raw_tasks) and isinstance(raw_tasks[i], dict):
            t = raw_tasks[i]
            tasks.append({
                "title": t.get("title", d[0]),
                "description": t.get("description", ""),
                "due_in_days": int(t.get("due_in_days", d[1])),
                "rationale": t.get("rationale", d[2]),
            })
        else:
            tasks.append({"title": d[0], "description": "", "due_in_days": d[1], "rationale": d[2]})

    return {
        "company_snapshot": str(snapshot)[:500],
        "personalized_opener": str(opener)[:800],
        "follow_ups": tasks[:3],
    }


# ─── Mock (for verif, no keys, DEBUG, budget fail) ────────────────────────────
def _mock_generate(lead_brief: dict, memory_ctx: str) -> dict[str, Any]:
    """Deterministic mock output. Used when no API keys or for tests. Verifiable shapes."""
    company = lead_brief.get("company_name", "Acme")
    contact = lead_brief.get("contact_name", "Jane Doe")
    first = contact.split()[0] if contact else "there"
    role = lead_brief.get("contact_role", "Decision Maker")
    signal = lead_brief.get("signal", "recent signal")
    pain = lead_brief.get("pain_point", "friction")
    signal_type = lead_brief.get("signal_type", "new_launch")

    snapshot = f"{company} is showing {signal}. Key stakeholder: {contact} ({role})."
    opener = (
        f"Hi {first}, saw the {signal} at {company} — this looks like a good moment to discuss how we help teams "
        f"address {pain.lower()}. Similar companies saw results in weeks."
    )

    tasks = [
        {
            "title": "Follow-up 1 — Check + Connect",
            "description": f"Check email open. Connect on LinkedIn: 'Hi {first} — sent note about {company} signal. Worth a direct connect?'",
            "due_in_days": 4,
            "rationale": "Prompt timing after initial signal; uses memory tone.",
        },
        {
            "title": "Follow-up 2 — Short Bump",
            "description": f"Short reply referencing {signal_type} window at {company}.",
            "due_in_days": 9,
            "rationale": "Keep momentum; references specific buying signal type.",
        },
        {
            "title": "Follow-up 3 — Close the Loop",
            "description": f"Final note on {pain}. Leave door open.",
            "due_in_days": 14,
            "rationale": "Address core pain point directly after two touches.",
        },
    ]
    return {
        "company_snapshot": snapshot,
        "personalized_opener": opener,
        "follow_ups": tasks,
        "model_used": "mock-llm",
        "mock": True,
    }


# ─── Provider calls (Gemini primary, Haiku fallback) ──────────────────────────
async def _call_gemini(prompt: str) -> Optional[dict[str, Any]]:
    """Primary: Gemini 2.5 Flash. Structured via prompt + parse (response_schema supported in recent SDK)."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 800,
            },
        )
        # Run sync SDK in thread to keep async
        def _sync_call() -> str:
            resp = model.generate_content(prompt + "\n\nJSON ONLY.")
            return getattr(resp, "text", "") or str(resp)

        text = await asyncio.to_thread(_sync_call)
        parsed = _parse_structured_json(text)
        parsed["model_used"] = settings.GEMINI_MODEL
        return parsed
    except Exception as e:
        logger.warning(f"Gemini call failed (will fallback): {e}")
        return None


async def _call_haiku(prompt: str) -> Optional[dict[str, Any]]:
    """Fallback: Claude Haiku. Instruct for JSON."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import AsyncAnthropic  # type: ignore

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=800,
            temperature=0.4,
            messages=[
                {"role": "user", "content": prompt + "\n\nReturn ONLY the minified JSON object, nothing else."}
            ],
            system="You are a precise JSON generator. Output must be valid JSON only.",
        )
        text = ""
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                text += block.text  # type: ignore
        parsed = _parse_structured_json(text)
        parsed["model_used"] = settings.ANTHROPIC_MODEL
        return parsed
    except Exception as e:
        logger.warning(f"Haiku fallback failed: {e}")
        return None


# ─── Public API ───────────────────────────────────────────────────────────────
async def generate_enrichment(
    lead_brief: dict[str, Any],
    current_user: dict[str, Any] | None = None,
    memory_context: dict[str, Any] | None = None,
    db: Any = None,  # AsyncSession | None; using Any to avoid import cycles (T010)
) -> dict[str, Any]:
    """Main entry: returns structured enrichment for preview or for enriching CRM create payloads.

    Shape (used by lead_service + web preview):
      company_snapshot, personalized_opener, follow_ups: list[dict with title/desc/due_in_days/rationale],
      model_used, mock?, usage?

    Budget guard + usage ledger logging applied.
    Memory injected from T006 context (stubbed).

    Args:
        lead_brief: dict with lead info (company_name, contact_name, etc)
        current_user: optional dict with user id/email for memory + budget + ledger
        memory_context: optional dict for tone/icp/cadence override
        db: optional AsyncSession for usage ledger persistence (T010)
    """
    if not lead_brief:
        lead_brief = {}

    mem = _build_memory_context(current_user, memory_context)
    prompt = _build_prompt(lead_brief, mem)

    # Budget estimate (~1-2 cents for flash/haiku)
    if not _check_budget(current_user, estimated_cents=2):
        logger.info("Budget guard triggered; using mock response")
        result = _mock_generate(lead_brief, mem)
        result["note"] = "budget_exceeded_mocked"
        return result

    # Request size guard (cheap)
    if len(prompt) > 6000:
        logger.warning("Prompt too large; truncating for budget")
        prompt = prompt[:6000]

    # Primary Gemini
    result = await _call_gemini(prompt)
    used_model = None
    if result:
        used_model = result.get("model_used", settings.GEMINI_MODEL)
    else:
        # Fallback
        result = await _call_haiku(prompt)
        if result:
            used_model = result.get("model_used", settings.ANTHROPIC_MODEL)

    if not result:
        # Final deterministic mock (always works for verif + no keys)
        result = _mock_generate(lead_brief, mem)
        used_model = result["model_used"]

    # Record usage (mocked tokens/cost for real calls too; real SDK usage in resp) + persist to DB (T010)
    await _record_usage(
        current_user,
        used_model or "unknown",
        input_tokens=400,  # rough
        output_tokens=250,
        cost_cents=1 if "mock" not in result else 0,
        db=db,
    )

    # Always include memory note for transparency (UI shows "using your memory")
    result.setdefault("memory_note", "Personalized using your style from prior leads (stub memory context)")
    return result


# Convenience for tests: reset stub counters
def _reset_usage_ledger_for_tests() -> None:
    _user_daily_usage.clear()
