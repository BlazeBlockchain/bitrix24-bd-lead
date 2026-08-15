# Feature Specification: Enrich–Design Parity — Filling the Inert Brief Sections

**Feature Branch**: `ai-bd-assistant`
**Created**: 2026-08-15
**Status**: Draft — planning only, not yet implemented
**Input**: User request — "plan to make enrich part of design", following `specs/008-design-system-pass/`,
which shipped those sections as deliberately inert.

## Problem

The 008 design pass applied the full visual language to every surface, but four sections of the lead
brief ship **inert** — styled, labelled "not available yet", and empty:

| Section | Designed in `docs/design/` | Returned by `/api/leads/enrich` |
|---|---|---|
| Company snapshot | ✅ | ✅ |
| Personalized opener | ✅ | ✅ |
| Follow-ups (3, with day chips) | ✅ | ✅ |
| **Buying signal** (source + date) | ✅ | ❌ |
| **Contact confidence** (HIGH/MED/LOW) | ✅ | ❌ |
| **Outreach email** (To / Subject / body) | ✅ | ❌ |
| **CRM entry** (field mapping grid) | ✅ | ❌ |
| **Source count / research steps** | ✅ | ❌ |

That was the right call for a design pass — fabricating a confidence pill would have violated the
product's own "AI is visible and trustworthy" principle. But it leaves the product visibly
half-finished: the user sees four dashed boxes telling them the feature does not exist yet.

**The gap is in the output contract, not in the model's capability.** `_build_prompt` in
`backend/app/services/llm_service.py` already injects the full encrypted skill methodology, which
governs signal priority, buyer psychology, email angles, banned phrases, and date rules. The model is
already being taught how to produce a buying-signal assessment and a complete outreach email. The
prompt then asks for only three fields and explicitly forbids extra keys:

> `No prose, no markdown, no ```json fences, no extra keys, no text before or after the JSON.`

So the work is to widen the contract and the prompt's JSON shape — not to teach the model anything
new, and not to add a research pipeline.

## User Story

As a business-development user, I want the brief to show the buying signal it found, how confident it
is in the contact, and a ready-to-send email, so that I can judge whether the lead is worth acting on
and send the outreach without rewriting it — instead of reading a snapshot and composing the rest
myself.

### Acceptance Scenarios

1. **Signal is attributed** — Given a lead is enriched, when the user opens the brief, then the
   buying signal is shown with what it is and where it came from, and a date when the model can
   establish one.

2. **Confidence is stated, not implied** — Given a lead is enriched, when the user views the contact
   section, then a confidence level (high / medium / low) is shown together with a one-line reason,
   and the level is the model's own assessment rather than a value derived client-side.

3. **The email is sendable** — Given a lead is enriched, when the user opens the outreach section,
   then a complete email is present with a subject line and body, addressed to the contact, and can
   be copied in one action.

4. **CRM mapping is visible before push** — Given a lead is enriched, when the user reviews the CRM
   entry section, then they can see which values will land in which CRM fields, before pushing.

5. **Nothing regresses** — Given any existing consumer of the enrichment response, when this feature
   ships, then the three original fields are unchanged in name, type, and meaning.

6. **Degradation stays honest** — Given the model omits or fails to produce one of the new fields,
   when the brief renders, then that section falls back to its inert presentation rather than showing
   an empty box, a fabricated value, or a broken layout.

7. **Every surface gains it together** — Given the new fields are returned, when the user compares
   the web app and the side panel, then both render the same sections from the same data.

### Edge Cases

- The model returns a confidence value outside the allowed set — must be treated as absent, not
  rendered raw.
- The model invents a source URL or a date it cannot support — needs an explicit prompt rule and a
  server-side sanity check, since a fabricated citation is worse than no citation.
- The signal the user typed is already specific; the model should attribute rather than replace it.
- A cached or historical enrichment created before this feature has none of the new fields — it must
  render inert, exactly as today.
- The mock generator (used when no API keys are configured, and by tests) must produce the new fields
  too, or every mock-path test renders an inert brief.
- Longer output raises token cost and truncation risk — the existing parser already detects
  truncation mid-JSON and that path must keep working.

## Requirements

### Functional

- **FR-001**: The enrichment response MUST carry a buying-signal object with, at minimum, a summary,
  and optionally a source and a date.
- **FR-002**: The enrichment response MUST carry a contact-confidence object with a level constrained
  to `high` / `medium` / `low`, plus a short reason.
- **FR-003**: The enrichment response MUST carry an outreach-email object with a subject and a body.
- **FR-004**: The enrichment response MUST carry a CRM field-mapping object describing the values
  destined for CRM fields.
- **FR-005**: All new fields MUST be **additive and optional**. The three existing fields keep their
  exact names, types, and meanings.
- **FR-006**: Any new field that is missing, malformed, or out of range MUST be treated as absent, and
  the corresponding section MUST fall back to its existing inert presentation.
- **FR-007**: The model MUST be instructed not to invent sources, URLs, or dates it cannot support,
  and unverifiable attributions MUST be omitted rather than guessed.
- **FR-008**: The mock generator MUST produce all new fields, so the no-API-key path and the test
  suite exercise the populated presentation.
- **FR-009**: The side panel and the web app MUST both render the new sections, replacing their inert
  counterparts, using the same data.
- **FR-010**: The outreach email MUST be copyable in one action from both surfaces.

### Non-Functional

- **NFR-001**: The three existing preview fields MUST remain unchanged; existing backend tests MUST
  pass without modification to their assertions about those fields.
- **NFR-002**: The extension MUST remain buildless, and all new content MUST continue to be rendered
  with `createElement`/`textContent`, never `innerHTML` with interpolation.
- **NFR-003**: The BD Lead Research skill methodology MUST remain server-side; none of it may leak
  into the response.
- **NFR-004**: No text below 12px, and no horizontal overflow in the panel at any width, when the new
  sections are populated with long real content.
- **NFR-005**: Token cost per enrichment MUST be measured before and after; a materially longer
  response must be a conscious, recorded trade-off rather than a surprise on the budget path.
- **NFR-006**: The existing truncation and malformed-JSON handling MUST keep working with the larger
  response.
- **NFR-007**: Enrichment latency MUST stay within the user's tolerance for the existing flow; if the
  larger response slows generation materially, that must be measured and reported.

## Success Criteria

- **SC-001**: A user enriching a lead sees the buying signal, contact confidence, outreach email, and
  CRM mapping populated — zero inert sections on the happy path.
- **SC-002**: The three original fields are byte-identical in shape; the existing suite passes with no
  assertion changes about them.
- **SC-003**: With any single new field forced absent or malformed, the brief still renders correctly,
  with only that section inert.
- **SC-004**: The web app and side panel render the same sections from the same enrichment.
- **SC-005**: Token cost and latency per enrichment are measured before and after, and recorded.
- **SC-006**: No fabricated source or date survives review of a sample of real enrichments.

## Key Entities

- **Buying signal** — what triggered the outreach: a summary, an optional source, an optional date.
- **Contact confidence** — a constrained level plus a human-readable reason.
- **Outreach email** — subject and body; the recipient is already known from the lead input.
- **CRM entry mapping** — the values destined for CRM fields, shown before push.
- **Field availability state** — per section: populated, or absent and therefore inert. This is the
  entity that already exists from 008 and is being extended, not replaced.

## Assumptions

- The existing skill methodology is sufficient to produce these fields; this is a contract and prompt
  change, not a new research or web-scraping capability.
- "Source" means what the model can attribute from the user's supplied signal and its own knowledge —
  **not** a live web lookup. Actual retrieval is a separate, larger feature.
- The 5-step research progress animation in the design is presentational. It is out of scope here
  because it requires streaming progress, which is an API-shape change of a different kind.
- The inert presentation built in 008 remains the fallback and is not removed.

## Out of Scope

- Live web retrieval, search, or citation verification.
- Streaming or step-by-step research progress from the server.
- Any change to `/api/leads/push` or to CRM adapters.
- Onboarding and billing screens.
- Changing the three existing preview fields.
