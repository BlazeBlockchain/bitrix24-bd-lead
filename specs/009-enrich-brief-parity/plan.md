# Implementation Plan: Enrich–Design Parity

**Feature Branch**: `ai-bd-assistant` · **Spec**: [spec.md](./spec.md) · **Date**: 2026-08-15
**Status**: Plan only — no implementation started.

## Summary

Widen the enrichment output contract so the four sections that 008 shipped inert — buying signal,
contact confidence, outreach email, CRM entry — carry real model output. All fields additive and
optional, so the frozen three-field shape and its 76 test assertions are untouched, and the inert
presentation stays as the fallback.

**The central finding**: this is a contract change, not a capability change. `_build_prompt` already
injects the full encrypted skill methodology governing signal priority, buyer psychology, email
formulas, banned phrases, and date rules. The model is already being taught to produce this material.
The prompt then asks for three fields and ends with:

> `No prose, no markdown, no ```json fences, no extra keys, no text before or after the JSON.`

That sentence is what suppresses the richer brief. The work is to widen the requested shape and
render it — not to build research, retrieval, or a new prompt discipline.

## Technical Context

| Aspect | Value |
|---|---|
| Contract owner | `backend/app/services/llm_service.py` — `_build_prompt`, `_parse_structured_json`, `_mock_generate` |
| Providers | Gemini 2.5 Flash (primary, `response_mime_type: application/json`), Haiku 4.5 (fallback) |
| Pinned by | 76 assertions in `backend/tests/{conftest,test_llm_service,test_lead_service,test_skill_privacy}.py` |
| Web type | `web/src/api/client.ts` `EnrichedPreview` — already has `[key: string]: any` |
| Renderers | `web/src/components/Preview.tsx`, `extension/sidepanel.js` (+ `sidepanel.html` inert blocks) |
| Gates | `cd backend && pytest tests/` (77), `cd web && npm run build`, `make check-tokens`, `make check-icons` |

## Architecture

### Where the change lands

```
_build_prompt()          widen the JSON contract; add anti-fabrication rule
      │
      ▼
Gemini / Haiku           unchanged call path, unchanged providers
      │
      ▼
_parse_structured_json() validate new fields ADDITIVELY; drop malformed, keep the
      │                  existing strict/truncation behaviour for the frozen three
      ▼
lead_service             passes through; no shape logic
      │
      ├──────────────► web/src/components/Preview.tsx
      └──────────────► extension/sidepanel.js
                       both: populated when valid, INERT otherwise
```

`_mock_generate` mirrors the full shape so the no-key path and the tests exercise the populated
presentation rather than the inert one.

### The design principle that governs this feature

008 established: **a section is populated only when the server sent valid data; otherwise it is
inert.** No client-side derivation, ever. 009 does not relax that — it just makes the populated
branch reachable. Concretely: no confidence computed from string heuristics, no subject line
synthesised from the company name, no source inferred from a domain. If the model did not say it, the
section stays inert.

This is why `contact_confidence.level` is enum-validated server-side *and* client-side: an
unrecognised value is absent, never rendered raw.

## Phasing

Deliberately ordered so each phase is independently shippable and independently revertible.

| Phase | Scope | Ships value? |
|---|---|---|
| **P1 — Contract + mock** | Extend `_build_prompt` JSON shape, `_parse_structured_json` additive validation, `_mock_generate` full shape. New backend tests for absent/malformed/out-of-range. | No UI change yet; proves the shape end to end on the mock path |
| **P2 — Render** | `Preview.tsx` and `sidepanel.js` render populated sections, falling back to the 008 inert blocks. | Yes — the visible payoff |
| **P3 — Live model tuning** | Run real Gemini/Haiku enrichments, tune the prompt for quality and anti-fabrication, measure token cost and latency. | Yes — quality |

P1 is safe to land alone: the contract widens, nothing renders differently, and the mock path proves
the plumbing. P3 is where the real risk lives, and it is deliberately last so it can be tuned against
a working UI.

## File plan

**Modified**

| Path | Change |
|---|---|
| `backend/app/services/llm_service.py` | widen prompt contract; additive parse validation; full mock |
| `backend/tests/test_llm_service.py` | new cases: each field absent, malformed, enum out of range |
| `backend/tests/conftest.py` | mock fixture gains the new fields |
| `web/src/api/client.ts` | additive optional types on `EnrichedPreview` |
| `web/src/components/Preview.tsx` | populated branches; keep `InertSections` as fallback |
| `extension/sidepanel.js` | render new sections via `createElement`/`textContent` |
| `extension/sidepanel.html` | inert blocks become the fallback branch, not the only branch |

**Untouched**: `/api/leads/push`, CRM adapters, `manifest.json`, the design token pipeline, all of
`docs/design/`.

## Constitution Check

| Gate | Status | Evidence |
|---|---|---|
| Buildless extension preserved | PASS | rendering-only change; no npm, no bundler |
| Existing preview shape unchanged | PASS | additive by contract; FR-005, NFR-001 |
| Push contract unchanged | PASS | `crm_entry` is display-only in this feature |
| No XSS surface | PASS | `createElement`/`textContent`; email body via `pre-wrap`, never `innerHTML` |
| Skill content stays server-side | PASS | methodology is prompt input; only lead-specific output is returned |
| No fabricated AI output | PASS by design | anti-fabrication prompt rule + enum validation + inert fallback |
| 12px floor / no h-overflow | VERIFY | new long content must be re-checked with the 008 harness |
| Version not hand-edited | PASS | `make bump-*` |
| Backend tests / web build green | VERIFY | real gate; additive changes should keep 77 passing |

## Risks

| Risk | Mitigation |
|---|---|
| **The model invents sources and dates.** The most damaging failure — a fabricated citation is worse than none, and it directly attacks the product's trust principle | Explicit prompt rule to omit rather than guess; treat unsupported values as absent; sample real enrichments in P3 before shipping |
| Longer response truncates mid-JSON | Existing truncation detection already handles this; raise `max_output_tokens` and add a regression test at the new length |
| Token cost per enrichment rises | Measure before/after in P3 (NFR-005); the budget path already exists in `_check_budget` |
| Confidence pill becomes decorative | Enum-validate on both sides; require a `reason` alongside the level so it is falsifiable |
| Two renderers drift | Same contract doc drives both; the 008 harness asserts both surfaces |
| Panel overflow with a full email body | `pre-wrap` + `overflow-wrap: anywhere` already in the token CSS; re-run the harness at narrow widths with long content |

## Open questions to resolve before P3

1. **Should `crm_entry` eventually drive the actual push**, or stay display-only? This plan keeps it
   display-only. Wiring it to the push contract is a separate feature with real blast radius.
2. **Is "source" allowed to be a bare claim** ("company blog, Q2") or must it be a URL? Bare claims
   are more achievable without retrieval; URLs invite fabrication. This plan assumes bare claims,
   omitted when unsupported.
3. **Does the outreach email replace `personalized_opener`, or wrap it?** This plan keeps both: the
   opener stays frozen, and the email is additive. Merging them later is a contract change.

## Next steps

- `/speckit-tasks` against this plan to generate `tasks.md`, or start at P1 directly.
- Note `.specify/feature.json` still points at `specs/008-design-system-pass`; repoint it when this
  feature becomes active.
