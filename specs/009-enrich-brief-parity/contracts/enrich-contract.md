# Contract: Extended Enrichment Response

**Endpoint**: `POST /api/leads/enrich` — request shape **unchanged**.
**Rule**: every field below is **additive and optional**. Nothing existing is renamed, retyped, or
given new meaning.

## Existing — frozen

```jsonc
{
  "company_snapshot": "string",
  "personalized_opener": "string",
  "follow_ups": [
    { "title": "string", "description": "string", "due_in_days": 4, "rationale": "string" }
  ]
}
```

`follow_ups` stays exactly 3, with `due_in_days` 4 / 9 / 14 in that order. 76 assertions across
`backend/tests/{conftest,test_llm_service,test_lead_service,test_skill_privacy}.py` depend on this.

Already-present optional extras (`model_used`, `mock`, `memory_note`, `authenticated_as`) are
existing proof that the response is additively extensible in practice.

## New — all optional

```jsonc
{
  "buying_signal": {
    "summary": "string",           // required if the object is present
    "source": "string | null",     // where it came from; omit rather than invent
    "date": "YYYY-MM-DD | null"    // omit rather than guess
  },

  "contact_confidence": {
    "level": "high | medium | low",  // constrained; anything else is treated as absent
    "reason": "string"
  },

  "outreach_email": {
    "subject": "string",
    "body": "string"                 // plain text, newlines preserved, rendered pre-wrap
  },

  "crm_entry": {
    "deal_name": "string | null",
    "contact_role": "string | null",
    "signal": "string | null",
    "pain_point": "string | null",
    "pipeline": "string | null"
  }
}
```

## Client-side rules

1. **Absent, malformed, or out-of-range means inert.** A section renders in the 008 inert
   presentation whenever its object is missing, is not an object, or fails validation. Never render a
   partially-filled section as if it were complete.
2. **`contact_confidence.level` is validated against the enum before use.** An unrecognised value is
   treated as absent — never rendered raw, never shown as a pill of unknown meaning.
3. **No client-side derivation.** The client must not compute a confidence level, infer a source, or
   synthesise a subject line. If the server did not send it, the section is inert. This is the rule
   that keeps the brief trustworthy, and it is the same rule 008 established.
4. **All values render as text.** `createElement` + `textContent` only. `outreach_email.body` uses
   `white-space: pre-wrap`, never `innerHTML`.

## Server-side rules

1. **The JSON contract in `_build_prompt` gains the new keys**, and its closing instruction changes
   from "no extra keys" to an explicit full shape. That sentence is currently what suppresses these
   fields.
2. **Anti-fabrication is an explicit prompt rule**: omit `source` and `date` rather than guess. A
   fabricated citation is worse than an absent one — it is the failure mode most damaging to trust.
3. **`_parse_structured_json` validates additively.** New fields are dropped when malformed; the three
   existing fields keep their current strict/non-strict behaviour, including the truncation detection
   that raises on unparseable output.
4. **`_mock_generate` returns the full shape**, so the no-API-key path and the tests exercise the
   populated presentation rather than the inert one.

## Compatibility matrix

| Consumer | Impact |
|---|---|
| `backend/tests/*` | none — additive; existing assertions untouched |
| `web/src/api/client.ts` `EnrichedPreview` | additive optional fields; already has `[key: string]: any` |
| `web/src/components/Preview.tsx` | replaces inert blocks with populated ones when present |
| `extension/sidepanel.js` | same, via `createElement`/`textContent` |
| `/api/leads/push` + CRM adapters | **none** — `crm_entry` is display-only in this feature |
| Stored historical enrichments | render inert, exactly as today |

## Explicitly not in this contract

- `sources_count` and research-step progress — presentational in the design, and the step animation
  needs streaming, which is a different API shape.
- Any request-side change.
- Any change to what gets pushed to the CRM.
