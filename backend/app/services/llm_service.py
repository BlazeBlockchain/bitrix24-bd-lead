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
from urllib.parse import urlsplit

from app.config import settings
from app.services.retrieval_service import fence_evidence, retrieve_signal_evidence
from app.services.skill_loader import get_skill_methodology

logger = logging.getLogger(__name__)

# ─── Budget + usage (per-user stub; T009 will persist to usage_ledger + models) ──
# In-memory for skeleton (process lifetime). Real: Redis + DB ledger per current_user.id
_user_daily_usage: dict[str, dict[str, Any]] = {}  # user_id -> {"date": str, "cents": int, "calls": int}


def _get_user_key(user: dict | None) -> str:
    if not user:
        return "anonymous"
    return str(user.get("id") or user.get("email") or "unknown")


# ─── Cost model (009 P3) ───────────────────────────────────────────────────────
# Private key used to carry real provider usage back from _call_gemini/_call_haiku
# to generate_enrichment. It is popped before the result is returned, so it never
# reaches /api/leads/enrich or either client. Underscore-prefixed to make an
# accidental leak obvious in a response body.
_USAGE_KEY = "_usage"


def _cost_cents(model: str, input_tokens: int, output_tokens: int) -> float:
    """Cost of one call, in cents, as a float.

    Float on purpose: a single enrichment costs ~0.36 cents, so rounding per call
    would floor every real call to zero and the daily budget would never move.
    Callers accumulate the float and round only when writing the integer ledger
    column.
    """
    rates = settings.LLM_PRICE_CENTS_PER_MTOK.get(
        model, settings.LLM_PRICE_CENTS_PER_MTOK_DEFAULT
    )
    return (input_tokens * rates["in"] + output_tokens * rates["out"]) / 1_000_000


def _check_budget(user: dict | None, estimated_cents: float = 2) -> bool:
    """Hard per-user daily guard (NFR). Returns True if within budget.

    The estimate is deliberately conservative and is checked BEFORE the call, when
    the real token count cannot be known. Erring high means the guard trips early
    rather than late, which is the safe direction for a spend cap.
    """
    if settings.DEBUG:
        return True  # allow in dev
    uid = _get_user_key(user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    rec = _user_daily_usage.get(uid, {"date": today, "cents": 0.0, "calls": 0})
    if rec["date"] != today:
        rec = {"date": today, "cents": 0.0, "calls": 0}
    if rec["cents"] + estimated_cents > settings.LLM_DAILY_BUDGET_CENTS:
        logger.warning(f"LLM budget exceeded for {uid}: {rec['cents']}+{estimated_cents} > {settings.LLM_DAILY_BUDGET_CENTS}")
        return False
    return True


async def _record_usage(
    user: dict | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_cents: float,
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
        _user_daily_usage[uid] = {"date": today, "cents": 0.0, "calls": 0}
    # Accumulated as a float so sub-cent calls actually move the daily total. Rounding
    # here instead would floor every real enrichment (~0.36 cents) to zero and the
    # budget guard would never trip no matter how many calls were made.
    _user_daily_usage[uid]["cents"] += cost_cents
    _user_daily_usage[uid]["calls"] += 1

    # Structured log for observability
    logger.info(
        "LLM_USAGE: user=%s model=%s in=%d out=%d cost_cents=%.4f daily_total=%.4f calls=%d",
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
                # The column is an integer, so a single sub-cent enrichment rounds to
                # 0 here. That is a known limitation of the schema, not of the
                # measurement: input_tokens/output_tokens above are the exact provider
                # counts, so true spend stays recomputable from the row. Widening this
                # column to a finer unit needs a migration.
                estimated_cost_cents=round(cost_cents),
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
def _build_prompt(lead_brief: dict, memory_ctx: str, evidence: str = "") -> str:
    """Builds the system+user prompt for structured enrichment.
    Includes: encrypted skill methodology + lead brief + injected memory + JSON contract.

    The skill provides the authoritative methodology (signal priority, buyer psychology,
    email formulas, banned phrases, date rules); the JSON contract ensures the output
    shape is stable for UI/lead_service/tests.
    """
    company = lead_brief.get("company_name", "Acme Corp")
    contact = lead_brief.get("contact_name", "Decision Maker")
    role = lead_brief.get("contact_role", "Head of Ops")
    signal = lead_brief.get("signal", "recent trigger")
    signal_type = lead_brief.get("signal_type", "new_launch")
    pain = lead_brief.get("pain_point", "process friction")
    email_subj = lead_brief.get("email_subject", "Intro")
    notes = lead_brief.get("notes", "")

    # Load encrypted skill methodology (server-side IP, never sent to client)
    skill_methodology = get_skill_methodology()

    # Fill AGENCY SETUP placeholders from memory where available (T024 will expand this)
    # For now use neutral defaults; T024 profile will inject real agency context
    agency_setup = (
        "AGENCY SETUP (from user profile; using defaults if not configured):\n"
        "AGENCY NAME:        [Your Agency Name]\n"
        "SERVICES:           [Web development, UX/UI, digital marketing, or similar]\n"
        "CORE CLIENTS:       [Example client 1, Example client 2]\n"
        "IDEAL CLIENT:       [Based on ICP from memory]\n"
        "VALUE PROP:         [Your unique positioning]\n"
        "AVOID:              [Any industry/type constraints]\n"
        "OUTREACH LANGUAGE:  [English]\n"
    )

    # Retrieved evidence is UNTRUSTED third-party text. It is fenced by
    # retrieval_service.fence_evidence and placed LAST, after the output contract, so
    # that nothing inside it can be read as the instruction that governs the response.
    evidence_block = f"\n\n{evidence}\n" if evidence else ""

    return f"""{skill_methodology}

────────────────────────────────────────────────────────────────────────────────
AGENCY SETUP (injected from user context; override with your actual details in T024)
────────────────────────────────────────────────────────────────────────────────
{agency_setup}

────────────────────────────────────────────────────────────────────────────────
YOUR PERSONALIZATION (memory context)
────────────────────────────────────────────────────────────────────────────────
{memory_ctx}

────────────────────────────────────────────────────────────────────────────────
LEAD BRIEF (company + signal + context)
────────────────────────────────────────────────────────────────────────────────
- Company: {company}
- Contact: {contact} ({role})
- Buying signal: {signal} (type: {signal_type})
- Pain point: {pain}
- Suggested subject: {email_subj}
- Notes: {notes}

────────────────────────────────────────────────────────────────────────────────
REQUIREMENTS (strict output contract)
────────────────────────────────────────────────────────────────────────────────
1. company_snapshot: 1-2 sentence factual snapshot based on the signal + why now
2. personalized_opener: short cold email opener (2-4 sentences) in the user's tone
   - Address contact by first name
   - Reference the signal directly
   - Benefit-focused, no hype, no banned phrases
3. follow_ups: EXACTLY 3 objects with:
   - title (e.g. "Follow-up 1 — Check + Connect")
   - description (actionable steps, 2-4 sentences, reference contact/company/signal)
   - due_in_days: 4, 9, 14 (strictly in this order)
   - rationale (1 sentence on timing + action)
4. buying_signal: your assessment of the trigger, with
   - summary (1 sentence: what the signal is and why it matters now)
   - source (where the signal came from, as a short plain-text attribution such as
     "company blog" or "reported in the lead brief" — NEVER a URL. Do not output a
     source_url or a quote: citations are attached by the server from what it
     actually retrieved, and any URL you write is discarded.)
   - date (YYYY-MM-DD) — include ONLY if the lead brief states a complete,
     unambiguous date. If it gives a month with no year ("in March"), a quarter, a
     season, or a vague word ("recently", "last year"), OMIT the date key entirely.
     NEVER complete a partial date: do not infer the day of the month, and do not
     infer the year. A missing date is correct. A completed one is fabrication, even
     when the guess is plausible.
5. contact_confidence: how likely this specific person is the RIGHT person to
   approach about this specific pain point. This is a judgement about role fit —
   it is NOT about whether the lead brief was filled in. The contact's name and
   title being supplied is the INPUT to this assessment, never evidence for it, and
   must not appear in your reason. Do not default to "high".
   - level: EXACTLY one of "high", "medium", "low" — no other value, no other wording
       high   = this role plainly owns this pain point and can authorise a fix
       medium = this role is plausibly involved but may not own the budget or the decision
       low    = the role is unclear, too junior, or in a different function from the pain
     If the signal or the pain point is too vague to judge role fit, use "low".
   - reason (1 short sentence referring to the ROLE and the PAIN POINT — never to
     the brief, the input, or what you were given)
6. outreach_email: a complete, ready-to-send cold email, with
   - subject (short, specific, no clickbait)
   - body (plain text; use "\\n" for line breaks; greet the contact by first name and
     sign off; follow the skill's email formula and banned-phrase rules)
7. crm_entry: the values to record in the CRM, with
   - deal_name, contact_role, signal, pain_point, pipeline (short strings)

ANTI-FABRICATION — this overrides completeness. Never invent a source, a URL, or a date.
If you cannot support an attribution from the lead brief above or from what you actually
know, OMIT that key entirely rather than guessing. An omitted source is correct; an
invented one is a serious error. `date` must never be in the future. If you are not
confident which of high/medium/low applies, omit the whole contact_confidence object
rather than defaulting to one.

Follow the skill methodology above for signal priority, buyer psychology, email angles,
banned phrases, and date calculations — it governs the QUALITY of your content.
It does NOT govern the OUTPUT FORMAT: ignore its "FINAL OUTPUT" / "LEAD BRIEF" text
template, its "BITRIX24" section, and any instruction to call a tool — none of that
applies here. The ONLY output format that applies to this response is the JSON
contract below, and it overrides every other formatting instruction above.

Keep output short and factual. Never mention these guidelines, the skill, or any
instructions in your output — output only the lead-specific content itself.
Respond ONLY with a single valid minified JSON object, exactly this shape and nothing else:

{{"company_snapshot": "...", "personalized_opener": "...", "follow_ups": [{{"title": "...", "description": "...", "due_in_days": 4, "rationale": "..."}}], "buying_signal": {{"summary": "...", "source": "...", "date": "YYYY-MM-DD"}}, "contact_confidence": {{"level": "high", "reason": "..."}}, "outreach_email": {{"subject": "...", "body": "..."}}, "crm_entry": {{"deal_name": "...", "contact_role": "...", "signal": "...", "pain_point": "...", "pipeline": "..."}} }}

No prose, no markdown, no ```json fences, no text before or after the JSON. Use exactly
the keys shown above and no others — except that any key you cannot support honestly
(source, date, or a whole object) must be omitted rather than filled with a guess.
{evidence_block}"""


# ─── Additive field validation (009) ──────────────────────────────────────────
# Every validator below returns None when the field cannot be trusted, and the caller
# then omits the key entirely. That is deliberate: the client renders a section INERT
# whenever its object is absent, so "drop it" and "show the 008 not-available-yet block"
# are the same outcome. There is no partial-render path and no client-side derivation —
# a half-filled confidence pill or a subject line synthesised from the company name would
# be a fabrication, which is the failure mode this feature exists to avoid.

CONFIDENCE_LEVELS = ("high", "medium", "low")


def _clean_str(value: Any, limit: int) -> Optional[str]:
    """A non-empty string, trimmed and length-capped — or None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text[:limit] if text else None


def _validate_signal_date(value: Any) -> Optional[str]:
    """An established YYYY-MM-DD in the past or today — or None.

    The future check is the one fabrication test the server can actually run without
    retrieval: a buying signal cannot have happened tomorrow, so a future date is proof
    the model guessed. Everything else about a date is unverifiable here, which is why
    the prompt carries the burden of omitting rather than inventing.
    """
    text = _clean_str(value, 10)
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None
    if parsed.date() > datetime.utcnow().date():
        logger.info("Dropping buying_signal.date %r: dated in the future", text)
        return None
    return text


def _validate_buying_signal(raw: Any) -> Optional[dict[str, Any]]:
    """summary is required; source and date drop individually when unsupportable.

    010: `source_url` and `quote` are stripped here unconditionally, no matter how
    well-formed they look. They are attached afterwards by `attach_citation` from
    retrieval metadata, and that is the ONLY path that may set them. See the docstring
    on `_validate_citation` for why the model is not allowed to author a URL.
    """
    if not isinstance(raw, dict):
        return None
    summary = _clean_str(raw.get("summary"), 400)
    if not summary:
        return None
    out: dict[str, Any] = {"summary": summary}
    source = _clean_str(raw.get("source"), 200)
    if source:
        out["source"] = source
    date = _validate_signal_date(raw.get("date"))
    if date:
        out["date"] = date
    for authored in ("source_url", "finding", "quote"):
        if raw.get(authored) is not None:
            # Worth a log line rather than a silent drop: how often the model reaches
            # for a URL once it has been shown retrieved evidence is exactly the
            # measurement P4 needs, and it is invisible if we discard it quietly.
            logger.info("Dropping model-authored buying_signal.%s: citations come from retrieval only", authored)
    return out


# ─── Citation validation (010) ────────────────────────────────────────────────
# 009 left `source` honest but uninformative: 5/5 real enrichments attributed the signal
# to "the lead brief", which is where the user typed it. Retrieval fixes that, and in
# doing so RELOCATES the fabrication risk rather than removing it — the model can now
# cite a real page that does not say what the brief claims. A confident link to a real
# page that does not support the claim is worse than no link at all, because it looks
# like proof.
#
# Three structural defences, none of which rely on the model behaving:
#   1. The model cannot author a URL. `_validate_buying_signal` strips source_url/quote
#      from model JSON unconditionally; only `attach_citation` may set them.
#   2. The `finding` is the RETRIEVAL call's grounded sentence, which the grounding
#      metadata attributes to this specific source, and it is the same evidence text
#      the enrichment model is given. The rep sees the model's actual input.
#      NOTE: it is NOT a quotation from the page. The API's groundingSupports carry
#      spans of the MODEL's text, not the source's, so no page quote is available —
#      which is why this field is `finding` and is never rendered as a quote.
#   3. A finding cannot survive without a URL, so every finding is one click from
#      being falsified by the rep.

CITATION_ALLOWED_SCHEMES = ("https",)
FINDING_MAX_CHARS = 240
SOURCE_URL_MAX_CHARS = 2000


def _validate_source_url(value: Any) -> Optional[str]:
    """An https URL with a host — or None.

    http is excluded alongside javascript: and data:. The latter two are the attack
    cases; http is refused because a citation we invite the rep to click should not be
    downgradeable in transit, and any publisher worth citing serves https.
    """
    text = _clean_str(value, SOURCE_URL_MAX_CHARS)
    if not text:
        return None
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.scheme.lower() not in CITATION_ALLOWED_SCHEMES:
        logger.info("Dropping citation URL: scheme %r not allowed", parts.scheme)
        return None
    if not parts.hostname:
        return None
    return text


def _validate_citation(url: Any, finding: Any = None) -> Optional[dict[str, str]]:
    """A validated {source_url, quote?} — or None.

    Finding-without-URL returns None for BOTH: an unattributable claim is a
    fabrication surface, not evidence. The reverse is fine — a URL with no finding is
    a weaker citation, but an honest one.
    """
    source_url = _validate_source_url(url)
    if not source_url:
        return None
    out = {"source_url": source_url}
    text = _clean_str(finding, FINDING_MAX_CHARS)
    if text:
        out["finding"] = text
    return out


def attach_citation(preview: dict[str, Any], url: Any, finding: Any = None) -> dict[str, Any]:
    """Attach a retrieval-sourced citation to `buying_signal`, in place.

    The only sanctioned path for setting `source_url`/`quote`. A citation with no
    buying_signal to hang on is dropped: there would be nothing for it to support, and
    a floating citation is the definition of an unsupported claim.
    """
    citation = _validate_citation(url, finding)
    if not citation:
        return preview
    signal = preview.get("buying_signal")
    if not isinstance(signal, dict) or not signal.get("summary"):
        logger.info("Dropping citation: no buying_signal.summary for it to support")
        return preview
    signal.update(citation)
    return preview


def _validate_contact_confidence(raw: Any) -> Optional[dict[str, Any]]:
    """Both level and reason are required.

    A level with no reason is dropped rather than shown: an unfalsifiable HIGH pill is
    precisely the decorative-confidence failure 008 refused to ship. The enum is checked
    here AND on the client, so an unrecognised value can never be rendered raw.
    """
    if not isinstance(raw, dict):
        return None
    level = _clean_str(raw.get("level"), 20)
    reason = _clean_str(raw.get("reason"), 300)
    if not level or not reason:
        return None
    level = level.lower()
    if level not in CONFIDENCE_LEVELS:
        logger.info("Dropping contact_confidence: level %r not in %s", level, CONFIDENCE_LEVELS)
        return None
    return {"level": level, "reason": reason}


def _validate_outreach_email(raw: Any) -> Optional[dict[str, Any]]:
    """Both subject and body are required — half an email is not sendable."""
    if not isinstance(raw, dict):
        return None
    subject = _clean_str(raw.get("subject"), 200)
    body = _clean_str(raw.get("body"), 4000)
    if not subject or not body:
        return None
    return {"subject": subject, "body": body}


def _validate_crm_entry(raw: Any) -> Optional[dict[str, Any]]:
    """Keep whichever of the known fields are present; drop the object if none are.

    Display-only in this feature — /api/leads/push and the CRM adapters are untouched,
    so this never decides what actually lands in the CRM.
    """
    if not isinstance(raw, dict):
        return None
    out = {}
    for key in ("deal_name", "contact_role", "signal", "pain_point", "pipeline"):
        value = _clean_str(raw.get(key), 300)
        if value:
            out[key] = value
    return out or None


_OPTIONAL_VALIDATORS = {
    "buying_signal": _validate_buying_signal,
    "contact_confidence": _validate_contact_confidence,
    "outreach_email": _validate_outreach_email,
    "crm_entry": _validate_crm_entry,
}


# ─── Structured JSON parser (defensive) ───────────────────────────────────────
def _parse_structured_json(text: str, strict: bool = False) -> dict[str, Any]:
    """Extract + validate JSON. Falls back to minimal if malformed.

    strict=True raises ValueError when NOTHING usable could be parsed, instead of
    returning the placeholder defaults below.

    Why that matters: when a provider returns unparseable output, the non-strict
    path hands back an all-placeholder result ("Company scaling after recent
    signal.", empty descriptions) that the caller then stamps with a real
    model_used. A total failure becomes indistinguishable from a real generation
    — the request logs 200 OK, nothing warns, and the user is shown canned text
    attributed to the model. Provider calls therefore use strict=True so the
    fallback chain (Gemini -> Haiku -> mock) actually engages; the mock at least
    interpolates the real lead fields.
    """
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

    if strict and not (isinstance(data, dict) and data):
        # A response that starts like JSON but does not close is almost always the
        # output-token budget cutting the object off mid-string — a very different
        # problem from the model ignoring the format, so say which one it is.
        looks_truncated = text.lstrip().startswith("{") and not text.rstrip().endswith("}")
        why = (
            "response was TRUNCATED mid-JSON (raise max_output_tokens)"
            if looks_truncated
            else "response was not JSON"
        )
        sample = text[:300].replace("\n", " ")
        raise ValueError(f"Model returned no parseable JSON — {why} (first 300 chars: {sample!r})")

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

    result = {
        "company_snapshot": str(snapshot)[:500],
        "personalized_opener": str(opener)[:800],
        "follow_ups": tasks[:3],
    }

    # 009: the four sections 008 shipped inert. Strictly additive — the three fields
    # above keep their exact names, types, and normalization, and a new field failing
    # validation never affects them. Omitted keys render inert on both surfaces.
    for key, validate in _OPTIONAL_VALIDATORS.items():
        value = validate(data.get(key))
        if value is not None:
            result[key] = value

    return result


# ─── Mock (for verif, no keys, DEBUG, budget fail) ────────────────────────────
def _mock_generate(lead_brief: dict, memory_ctx: str) -> dict[str, Any]:
    """Deterministic mock output aligned with skill conventions.

    Used when no API keys or for tests. Follows skill methodology:
    - No banned phrases (touching base, leverage, synergy, etc)
    - Signal-specific opener language (signal buyer psychology)
    - Follow-ups at days +4, +9, +14
    - Benefit-focused, direct tone
    """
    company = lead_brief.get("company_name", "Acme")
    contact = lead_brief.get("contact_name", "Jane Doe")
    first = contact.split()[0] if contact else "there"
    role = lead_brief.get("contact_role", "Decision Maker")
    signal = lead_brief.get("signal", "recent signal")
    pain = lead_brief.get("pain_point", "friction")
    signal_type = lead_brief.get("signal_type", "new_launch")

    # Company snapshot: factual, why now
    snapshot = f"{company} is showing {signal}. With {contact} as {role}, this is an opportunity window."

    # Opener: benefit-focused, specific to signal, no banned phrases
    opener = (
        f"Hi {first}, saw the {signal} at {company} — we've helped similar companies address {pain.lower()} quickly. "
        f"Worth a quick conversation?"
    )

    # Follow-ups: strictly at +4/+9/+14 days, signal-aware, no generic filler
    tasks = [
        {
            "title": "Follow-up 1 — Check + Connect",
            "description": f"Check if the email landed. Connect on LinkedIn with: 'Hi {first}, sent a note about {company} earlier this week. Worth connecting directly?'",
            "due_in_days": 4,
            "rationale": "Capture attention early after initial signal; separate channel (LinkedIn) increases visibility.",
        },
        {
            "title": "Follow-up 2 — Short Bump",
            "description": f"Reply to original email: 'Still relevant? Most teams in {company}'s position find momentum matters — we can show what worked for similar companies.'",
            "due_in_days": 9,
            "rationale": f"Break silence without pressure; reference {signal_type} context to stay specific.",
        },
        {
            "title": "Follow-up 3 — Close the Loop",
            "description": f"Final note: 'Last message from me — if {pain} becomes a priority, you know where to find us.'",
            "due_in_days": 14,
            "rationale": "Honor the decision while leaving door open; full context (the pain point) justifies the touchpoint.",
        },
    ]
    # 009: the mock must carry the FULL shape. The no-API-key path and every mock-path
    # test run through here, so a mock that returned only the frozen three would render
    # an inert brief everywhere the real providers are not configured — exactly the gap
    # this feature closes.
    #
    # Note what `source` says: it attributes the signal the user typed into the lead
    # brief. That is honest by construction. A mock is still allowed to be wrong about
    # the world, but it must not model fabrication as acceptable behaviour, because it
    # is also the fixture developers read to learn what good output looks like.
    signal_date = datetime.utcnow().strftime("%Y-%m-%d")

    email_body = (
        f"Hi {first},\n\n"
        # The signal is free text from the rep and may be a noun or a verb phrase, so it
        # goes after a colon rather than inside a sentence that would have to agree with it.
        f"Something caught my eye at {company} — {signal}. For teams at that stage, "
        f"{pain.lower()} tends to become the bottleneck right as everything else speeds up.\n\n"
        f"We have helped similar companies work through exactly that, usually within "
        f"a few weeks and without disrupting what already works.\n\n"
        f"Worth a short call to see if it applies to you?\n\n"
        f"Best,\nThe team"
    )

    result = {
        "company_snapshot": snapshot,
        "personalized_opener": opener,
        "follow_ups": tasks,
        "buying_signal": {
            "summary": f"{company} — {signal}. That opens a short window to start a conversation.",
            "source": "Reported by the rep in the lead brief",
            "date": signal_date,
        },
        "contact_confidence": {
            "level": "medium",
            "reason": f"{role} is a plausible owner for {pain.lower()}, but the fit has not been independently confirmed.",
        },
        "outreach_email": {
            "subject": f"{company} — {signal}",
            "body": email_body,
        },
        "crm_entry": {
            "deal_name": lead_brief.get("deal_name") or f"{company} — {signal}",
            "contact_role": role,
            "signal": signal,
            "pain_point": pain,
            "pipeline": "New leads",
        },
        "model_used": "mock-llm",
        "mock": True,
    }
    # 010: the mock carries a citation so the no-API-key path and the tests exercise the
    # populated presentation rather than the 009 one. It goes through attach_citation
    # rather than being written inline, so the mock walks the same sanctioned path as
    # retrieval and cannot drift from it.
    #
    # example.com is deliberate. RFC 2606 reserves it as a non-resolving placeholder, so
    # this cannot be mistaken for a real citation — extending the rule the 009 mock set
    # for `source`: a mock may be wrong about the world, but it must never model
    # fabrication as acceptable, because it is also the fixture developers read to learn
    # what good output looks like.
    attach_citation(
        result,
        f"https://example.com/newsroom/{signal_type}",
        f"Example Newsroom reports that {company} {signal}.",
    )
    return result


# ─── Provider calls (Gemini primary, Haiku fallback) ──────────────────────────
async def _call_gemini(prompt: str) -> Optional[dict[str, Any]]:
    """Primary: Gemini 2.5 Flash. Structured via prompt + parse (response_schema supported in recent SDK)."""
    if not settings.GEMINI_API_KEY:
        # Says which of the two "returned None" cases this is. Without it, an
        # unconfigured key and a failing provider are indistinguishable in the logs,
        # and the fallback chain looks identical either way.
        logger.info("Gemini skipped: GEMINI_API_KEY is not set")
        return None
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": 0.4,
                # Ask the API for JSON directly rather than hoping the prompt is obeyed.
                # Without this the model may wrap the object in prose or fences, and the
                # parser then falls through to placeholder text.
                "response_mime_type": "application/json",
                # Must comfortably fit the WHOLE JSON object. 800 (and even 2048) truncated
                # it mid-string: the model writes a full email in personalized_opener plus
                # three follow-ups with descriptions, and a JSON object cut off partway is
                # unparseable, so every field fell back to placeholder text. Reasoning
                # tokens count against this budget too on 2.5-class models.
                # 010 raised this from 4096. Adding retrieved evidence to the prompt
                # makes the model write MORE, and at 4096 the JSON truncated mid-string
                # on 3 of 7 P4 leads — each one silently collapsing to the mock, which
                # is the exact failure the 009 note below warned about, triggered by a
                # new cause. Reasoning tokens count against this budget too.
                "max_output_tokens": 8192,
            },
        )

        # Run sync SDK in thread to keep async
        def _sync_call() -> tuple[str, dict[str, int]]:
            resp = model.generate_content(prompt + "\n\nJSON ONLY.")
            text = getattr(resp, "text", "") or ""
            if not text.strip():
                # Never fall back to str(resp): that is the repr of the response
                # object, which is never valid JSON but IS a non-empty string, so it
                # sailed past the parser and silently produced placeholder output.
                # Surface why the model returned nothing instead.
                reason = ""
                try:
                    cand = (getattr(resp, "candidates", None) or [None])[0]
                    reason = f" finish_reason={getattr(cand, 'finish_reason', None)}"
                    fb = getattr(resp, "prompt_feedback", None)
                    if fb:
                        reason += f" prompt_feedback={fb}"
                except Exception:
                    pass
                raise ValueError(f"Gemini returned empty text.{reason}")
            # Real provider counts. Previously the caller logged a hardcoded
            # 400/250 for every call, which under-recorded input by roughly 15x
            # and left the budget guard watching a number unrelated to spend.
            # candidates_token_count excludes reasoning tokens, which 2.5-class
            # models bill separately; total_token_count is what actually gets
            # charged, so the difference is attributed to output.
            um = getattr(resp, "usage_metadata", None)
            in_tok = int(getattr(um, "prompt_token_count", 0) or 0)
            out_tok = int(getattr(um, "candidates_token_count", 0) or 0)
            total = int(getattr(um, "total_token_count", 0) or 0)
            if total > in_tok + out_tok:
                out_tok = total - in_tok
            return text, {"input_tokens": in_tok, "output_tokens": out_tok}

        text, usage = await asyncio.to_thread(_sync_call)
        parsed = _parse_structured_json(text, strict=True)
        parsed["model_used"] = settings.GEMINI_MODEL
        parsed[_USAGE_KEY] = usage
        return parsed
    except Exception as e:
        logger.warning(f"Gemini call failed (will fallback): {e}")
        return None


async def _call_haiku(prompt: str) -> Optional[dict[str, Any]]:
    """Fallback: Claude Haiku. Instruct for JSON."""
    if not settings.ANTHROPIC_API_KEY:
        # Distinguishes "no key configured" from "the call failed" — both used to
        # surface as a bare None. With the key unset the chain is really
        # Gemini -> mock, with no Haiku step at all, and nothing said so.
        logger.info("Haiku fallback skipped: ANTHROPIC_API_KEY is not set")
        return None
    try:
        from anthropic import AsyncAnthropic  # type: ignore

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            # Matches Gemini's budget above, and for the same reason: 800 could not fit
            # the three-field object reliably, and the 009 contract adds a full outreach
            # email on top. A JSON object cut off mid-string is unparseable, so an
            # undersized cap here makes the fallback chain collapse straight to mock on
            # every Gemini failure — silently, since the parser reports truncation but
            # _call_haiku swallows it as "fallback failed".
            max_tokens=4096,
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
        if not text.strip():
            raise ValueError(f"Claude returned empty text (stop_reason={getattr(msg, 'stop_reason', None)})")
        parsed = _parse_structured_json(text, strict=True)
        parsed["model_used"] = settings.ANTHROPIC_MODEL
        usage = getattr(msg, "usage", None)
        parsed[_USAGE_KEY] = {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        }
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

    # 010: grounded search BEFORE the enrichment call, so its result can be fenced into
    # the prompt as evidence. Never raises and never blocks the flow — when it returns
    # None (disabled, no key, nothing found, timeout, error) the brief degrades to
    # exactly the 009 output: a buying signal with no source link.
    evidence = await retrieve_signal_evidence(lead_brief)
    evidence_block = (
        fence_evidence(evidence["finding"], evidence.get("publisher", "")) if evidence else ""
    )
    prompt = _build_prompt(lead_brief, mem, evidence_block)

    # Budget estimate (~1-2 cents for flash/haiku)
    if not _check_budget(current_user, estimated_cents=2):
        logger.info("Budget guard triggered; using mock response")
        result = _mock_generate(lead_brief, mem)
        result["note"] = "budget_exceeded_mocked"
        return result

    # Request size guard (increased for skill-inclusive prompt; ~40KB safe for Gemini/Haiku)
    if len(prompt) > 40000:
        logger.warning("Prompt too large (>40KB); truncating to fit model limits")
        prompt = prompt[:40000]

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

    # 010: the citation is attached HERE, by the server, from what retrieval actually
    # returned — never from the model's JSON, which had source_url/finding stripped on
    # parse. That ordering is the whole defence: showing the model retrieved evidence
    # gives it every incentive to emit a plausible URL of its own, and nothing about
    # the string would distinguish that from a real one.
    #
    # It is attached to a mock result too. The mock ships a placeholder citation, and
    # leaving that in place when a real one exists would show example.com over a brief
    # the rep may act on.
    if result.get("mock"):
        # A mock brief is generic filler that no model grounded in anything, so it gets
        # no source — neither the real one nor the placeholder the mock ships. P4 showed
        # why this matters: a truncated Gemini response fell back to mock, and the brief
        # then paired "That opens a short window to start a conversation" with a real
        # court-records link. A citation next to text nothing grounded lends borrowed
        # authority, which is the opposite of what a citation is for.
        signal = result.get("buying_signal")
        if isinstance(signal, dict):
            signal.pop("source_url", None)
            signal.pop("finding", None)
    elif evidence:
        attach_citation(result, evidence["source_url"], evidence["finding"])

    # Real provider token counts, priced from the table in config. Popped here so the
    # private carrier key can never reach /api/leads/enrich or either client — the
    # response contract stays exactly what contracts/enrich-contract.md says it is.
    #
    # A mock result has no usage: it cost nothing, so it records nothing rather than
    # a nominal cent, and the ledger stays a record of actual spend.
    usage = result.pop(_USAGE_KEY, None) or {}
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    await _record_usage(
        current_user,
        used_model or "unknown",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_cents=_cost_cents(used_model or "unknown", input_tokens, output_tokens),
        db=db,
    )

    # Always include memory note for transparency (UI shows "using your memory")
    result.setdefault("memory_note", "Personalized using your style from prior leads (stub memory context)")
    return result


# Convenience for tests: reset stub counters
def _reset_usage_ledger_for_tests() -> None:
    _user_daily_usage.clear()
