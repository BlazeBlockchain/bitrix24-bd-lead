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

## P3 results — measured 2026-08-15 (NFR-005, NFR-007, SC-005, SC-006)

Real `gemini-2.5-flash`, 5 leads × before/after, same leads and same model both times so the delta is
attributable to the widened contract alone. "Before" is the v0.2.0 prompt (`f5e5e8c`). 10/10 calls
parsed; 4/4 new fields present in 5/5 after-runs.

| | before | after (tuned) | delta |
|---|---|---|---|
| input tokens (mean) | 5,165 | 5,929 | +764 (+14.8%) |
| output tokens (mean) | 487 | 742 | +255 (+52.4%) |
| total incl. reasoning | 8,124 | 9,072 | +948 (+11.7%) |
| latency mean | 13.44s | 14.24s | +0.80s |
| latency max | 17.57s | 15.36s | — |

**Verdict**: accepted. Output tokens rise by half, but output is the small half of this request — the
skill methodology dominates the prompt — so total cost rises ~12% and latency is within noise of the
existing flow. This is the conscious, recorded trade-off NFR-005 asks for.

**On the "output tokens" row**: it is `candidates_token_count`, which is the visible answer only.
2.5-class models also charge *reasoning* tokens at the output rate, and those land in
`total_token_count` — roughly 2,900 billable output tokens per enrichment against ~740 visible. The
before/after delta above is still sound because both sides were measured the same way, but the
absolute cost per enrichment is **~0.91 cents**, not the ~0.36 that the visible count alone implies.
`_call_gemini` therefore records `total_token_count - prompt_token_count` as output.

### Two defects found by the first live run, and fixed

1. **Fabricated date (SC-006).** Signal "hired a new CTO from Epic in March" — no year — produced
   `date: "2024-03-15"`, inventing both the year (it is 2026) and the day. The server-side check only
   rejects *future* dates, so a confidently-wrong past date passed. Fixed in the prompt: a partial
   date (month with no year, quarter, season, "recently") must omit the key entirely, and the model
   must never complete a partial date. Re-run: 0/5 fabricated dates.
2. **Confidence was decorative.** 5/5 returned `high`, including the deliberately vague stress lead,
   with circular reasons ("Contact and role explicitly provided in the lead brief") — the model was
   assessing whether the form was filled in, not role fit. This is the exact risk in the table below.
   Fixed in the prompt: level is defined as role-fit against the pain point, the contact being
   supplied is named as the input and not evidence, per-level criteria are spelled out, and a
   too-vague brief must yield `low`. Re-run: the vague lead drops to `low` with a role-fit reason;
   reasons now cite the role and the pain point.

### Known gaps

- **`source` is uninformative.** 5/5 returned "reported in the lead brief". That is *correct* — it is
  the only honest attribution available without retrieval — but it means the Source chip tells the
  user nothing. Fixing it properly requires live retrieval, which is out of scope.
- **The Haiku fallback is still unverified live.** `ANTHROPIC_API_KEY` is empty in `.env`, so
  `_call_haiku` returns `None` immediately and the chain is really Gemini → mock with no Haiku step.
  The P1 `max_tokens` 800 → 4096 change is reasoned, not measured. Both providers now log *why* they
  were skipped, so an unset key no longer looks identical to a failing provider — but confirming the
  fallback needs a key.

### Fixed after the P3 review

- **The usage ledger recorded fabricated token counts.** `generate_enrichment` passed hardcoded
  `input_tokens=400, output_tokens=250, cost_cents=1` for every real call, against a measured ~5,950
  in / ~2,900 billable out — input under-recorded ~15×, and `_check_budget` guarding a number
  unrelated to spend. Now: both providers return real usage on a private `_usage` key, priced from
  `LLM_PRICE_CENTS_PER_MTOK` in config, and the key is popped before the response leaves the service
  so the enrich contract is unchanged. The in-memory daily total accumulates a **float**, because
  rounding a ~0.91-cent call to an integer would floor every enrichment to zero and freeze the budget
  guard entirely. The `usage_ledger.estimated_cost_cents` column is still an integer and still rounds
  per row — widening it needs a migration — but `input_tokens`/`output_tokens` are now exact, so true
  spend stays recomputable from the row.

## Risks

| Risk | Mitigation |
|---|---|
| **The model invents sources and dates.** The most damaging failure — a fabricated citation is worse than none, and it directly attacks the product's trust principle | Explicit prompt rule to omit rather than guess; treat unsupported values as absent; sample real enrichments in P3 before shipping |
| Longer response truncates mid-JSON | Existing truncation detection already handles this; raise `max_output_tokens` and add a regression test at the new length |
| Token cost per enrichment rises | Measure before/after in P3 (NFR-005); the budget path already exists in `_check_budget` |
| Confidence pill becomes decorative | Enum-validate on both sides; require a `reason` alongside the level so it is falsifiable |
| Two renderers drift | Same contract doc drives both; the 008 harness asserts both surfaces |
| Panel overflow with a full email body | `pre-wrap` + `overflow-wrap: anywhere` already in the token CSS; re-run the harness at narrow widths with long content |

## Open questions — resolved 2026-08-15

1. **Should `crm_entry` eventually drive the actual push?** — **Yes, eventually.** Out of scope for
   009, which keeps it display-only and labels the section "CRM entry (preview)" to say so. Wiring it
   to `/api/leads/push` is a separate feature with real blast radius on the CRM adapters.
2. **Is "source" allowed to be a bare claim, or must it be a URL?** — **Bare claim.** Encoded in
   `_build_prompt` as of P1: a short plain-text attribution ("company blog"), explicitly *not* a URL
   the model cannot verify. URLs invite exactly the fabrication FR-007 exists to prevent.
3. **Does the outreach email replace `personalized_opener`, or wrap it?** — **Replaces it, in the UI
   only.** Both surfaces hide the "Suggested Opener" card when a valid email is present, because two
   different openings for one lead invite the user to send a message contradicting the one below it.
   The field itself stays frozen in the response and still builds the CRM deal comment
   (`lead_service.py:95`), so the ADDITIVE-ONLY constraint and its 76 assertions are untouched. The
   opener card remains the email's fallback, which keeps "use the opener above" true when inert.

## Next steps

- `/speckit-tasks` against this plan to generate `tasks.md`, or start at P1 directly.
- Note `.specify/feature.json` still points at `specs/008-design-system-pass`; repoint it when this
  feature becomes active.
