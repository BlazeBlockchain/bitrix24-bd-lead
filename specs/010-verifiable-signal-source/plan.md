# Implementation Plan: A Verifiable Source for the Buying Signal

**Feature Branch**: `ai-bd-assistant` · **Spec**: [spec.md](./spec.md) ·
**Contract**: [contracts/citation-contract.md](./contracts/citation-contract.md) · **Date**: 2026-08-15
**Status**: P1 in progress.

## Summary

Give `buying_signal` a citation the rep can check: an `https` link plus the supporting sentence from
the cited page. Retrieval comes from Gemini's built-in Google Search grounding, run as a **separate
pre-call** whose evidence is fenced into the existing enrichment prompt.

**The central finding**: unlike 009, this is a capability change, and the risk it adds is not
fabrication but **unsupported attribution** — a real link to a real page that does not say what the
brief claims. The design answers that with three structural defences rather than prompt discipline:

1. The model **cannot author a URL** — `source_url` is stripped from model JSON unconditionally and
   attached afterwards from retrieval metadata only.
2. The **quote is extracted, not generated** — it is the span grounding metadata attributes to the
   chunk, so the model cannot mis-quote a page it never quoted.
3. A **quote cannot exist without a URL**, so every quote is one click from being falsified.

## Technical Context

| Aspect | Value |
|---|---|
| Contract owner | `backend/app/services/llm_service.py` — `_validate_buying_signal`, `_build_prompt`, `_mock_generate`, `generate_enrichment` |
| New service | `backend/app/services/retrieval_service.py` — grounded pre-call, kept out of the already-849-line `llm_service` |
| Retrieval provider | Gemini Google Search grounding, `gemini-2.5-flash` |
| Renderers | `web/src/components/Preview.tsx`, `extension/sidepanel.js` |
| Gates | `cd backend && pytest tests/` (137), `cd web && npm run build`, `make check-tokens`, `make check-icons` |

### Why retrieval must be a separate call

`_call_gemini` sets `response_mime_type: application/json`. On `gemini-2.5-flash` the API **rejects**
`google_search` together with controlled generation. On Gemini 3, where it is permitted,
`grounding_chunks` and `grounding_supports` come back **empty** — losing exactly the citation data
this feature needs. So the architecture is forced, and it happens to be the one we want anyway:

```
retrieval_service.retrieve()      grounded call, 6s cap, NO json mode
      │  evidence: [{uri, title, quote}]
      ▼
_build_prompt(..., evidence)      fenced, last, labelled untrusted
      │
      ▼
_call_gemini()                    unchanged: json mode, strict parse
      │
      ▼
_validate_buying_signal()         STRIPS any model-authored source_url/quote
      │
      ▼
attach_citation()                 server attaches the validated citation
      │
      ├──────────────► Preview.tsx
      └──────────────► sidepanel.js
```

## Phasing

Confirmed with the user before implementation. Each phase independently shippable and revertible.

| Phase | Scope | Ships alone? |
|---|---|---|
| **P1 — Contract + mock + validation** | `_validate_citation`, strip model-authored fields, `attach_citation`, full mock shape, tests for absent / malformed / `javascript:` / `data:` / `http:` / quote-without-url / over-length / model-authored. No network anywhere. | Yes — invisible; proves the shape on the mock path |
| **P2 — Render** | Both surfaces render link + quote, re-validating the scheme client-side. Harness at 320/400/500/720 with a long real URL. | Yes — degrades to exact 009 output in prod until P3 lands |
| **P3 — Retrieval service** | `retrieval_service.py`: grounded pre-call, 6s timeout, evidence fencing, injection defences, query from company+signal only. Wired into `generate_enrichment`. Config: timeout, enable flag, grounding price. Tests mocked. | Yes — the capability |
| **P4 — Live verification** | ≥6 real leads including a deliberately obscure company. Every citation opened and hand-checked. Latency + cost measured. | Yes — the acceptance gate |

P3 sits after P2 (where 009's live tuning sat) so P4's hand-check happens against what the rep
actually sees. **P1+P2 shipped without P3 produce byte-identical output to today**, because nothing
populates the new fields — that is what makes this ordering safe.

## File plan

**New**

| Path | Purpose |
|---|---|
| `backend/app/services/retrieval_service.py` | P3 — grounded retrieval, isolated from `llm_service` |
| `backend/tests/test_retrieval_service.py` | P3 — fully mocked |

**Modified**

| Path | Phase | Change |
|---|---|---|
| `backend/app/services/llm_service.py` | P1, P3 | citation validation + strip + attach; evidence in the prompt |
| `backend/tests/test_llm_service.py` | P1 | citation validation cases |
| `backend/tests/conftest.py` | P1 | mock fixture gains a citation |
| `backend/app/config.py` | P3 | retrieval enable flag, timeout, grounding price |
| `web/src/api/client.ts` | P2 | two additive optional fields |
| `web/src/components/Preview.tsx` | P2 | citation branch + client-side scheme check |
| `extension/sidepanel.js` | P2 | same, via `createElement`/`textContent` |
| `extension/sidepanel.css` | P2 | citation + quote styling below the generated token block |

**Untouched**: `/api/leads/push`, CRM adapters, `manifest.json`, `design/tokens.css` and the
generated token blocks, all of `docs/design/`.

## Constitution Check

| Gate | Status | Evidence |
|---|---|---|
| Buildless extension preserved | PASS | rendering-only on the client; no npm, no bundler |
| Frozen three unchanged | PASS | additive inside `buying_signal`; FR-001, NFR-001 |
| 009 objects not reshaped | PASS | two optional keys added to one object |
| Push contract unchanged | PASS | untouched |
| No XSS surface | PASS | `createElement`; `href` post-validation; https allowlist both sides |
| Skill content stays server-side | PASS | FR-009 — retrieval query is company + signal only |
| No fabricated AI output | **PASS by construction** | model cannot author a URL; quote is extracted, not generated |
| Untrusted input handled | PASS | fenced, delimiter-stripped, scope-limited to `buying_signal` |
| 12px floor / no h-overflow | VERIFY | P2 harness with a long real URL |
| Version not hand-edited | PASS | `make bump-*` |
| Tests hermetic and offline | VERIFY | P3 mocks retrieval; NFR-002 |
| Backend tests / web build green | VERIFY | 137 must not drop |

## P2 results — measured 2026-08-15

Both surfaces render the citation. 8 fixtures × 2 surfaces (full citation, long hostname, URL without
quote, quote without URL, `javascript:`, `data:`, `http:`, no citation), plus a layout sweep at
320/400/500/720. All green; 11 mutations confirmed each assertion is live.

### Two harness traps that made the first sweep vacuous

Both are worth recording, because a harness that cannot fail looks exactly like one that passes.

1. **`#previewSection` ships `style="display: none"`.** The first version of the sweep measured
   without un-hiding it, so every element returned width 0 and the font-size scan skipped the entire
   brief (it filters `display:none`). The DOM assertions were unaffected — they query, not measure —
   which is why the link-safety mutations still caught correctly while the layout half proved
   nothing. The sweep now asserts `measured > 15` so it cannot go quiet again undetected.

2. **The classic `documentElement.scrollWidth <= clientWidth` assertion is a tautology on this
   surface.** `body`, `.panel-container` and `.panel-content` all set `overflow-x: hidden`, so the
   document can never report horizontal scroll no matter what is rendered. Overflow here does not
   scroll, it **clips** — the real failure mode is content silently cut off. The check is now against
   the container's right edge (`rect.right > container.right + 1`) plus the container's own
   `scrollWidth`, which does catch it.

A third finding changed the fixtures: once link text is the hostname, a long *path* no longer
threatens the layout, so `overflow-wrap` on `.brief-link` looked unnecessary. It is not — a long
*hostname* still overflows, and mutating the rule to `nowrap` pushes content to x=750 in a 320px
panel. The stress fixture is a 121-character hostname for that reason.

### Design decisions settled during the render

- **Link text is the hostname, and a valid link replaces the plain `source` chip rather than joining
  it.** Two source chips that disagree is worse than one that is checkable, and a model-supplied
  publisher name ("TechCrunch") sitting over a link to somewhere else is a mismatch the rep has no
  way to notice. Rendering the hostname makes the link text structurally incapable of misdescribing
  the destination. This is not the client-side derivation the contract forbids: it makes no new
  claim, it renders the datum the server sent.
- **The quote is a `<blockquote>` with a left rule**, not a boxed section — it is evidence for the
  summary above it, not a section of its own, and the visual break signals "somebody else's words".

## Risks

| Risk | Mitigation |
|---|---|
| **A real link that does not support the claim.** The failure this feature exists to prevent, and the one most likely to occur | Quote extracted from grounding metadata rather than generated; quote requires URL; hand-check of ≥6 real enrichments in P4 including an obscure company, where the temptation to cite something adjacent is highest. One unsupportive citation is a FAIL |
| **Prompt injection from a retrieved page** | Evidence fenced last, labelled untrusted, delimiters stripped; scope-limited to `buying_signal`; instructions inside evidence are grounds to discard the chunk |
| Model emits its own plausible URL now that it has a retrieval context | Stripped unconditionally in `_validate_buying_signal`, and logged — the log is also the P4 signal for how often it tries |
| Retrieval latency pushes the flow past the point a rep assumes it hung | 6s cap; timeout degrades to 009 output, never fails the enrichment |
| Grounding cost at scale — ≈3.5¢/enrichment past 1,500 RPD, ~4× today's total | Recorded in config next to `LLM_PRICE_CENTS_PER_MTOK` with the same not-fetched caveat; enable flag allows switching it off |
| Long URL breaks the resizable panel | Hostname as link text, full URL in `title`; `overflow-wrap: anywhere` retained; harness at 320/400/500/720 |
| Skill methodology leaking into a third-party request | Retrieval service builds its own query from company + signal; it never receives the prompt |
| Two renderers drift | One contract doc drives both; the 008/009 harness asserts both surfaces |

## Open questions — resolved 2026-08-15

1. **Retrieval source?** — **Gemini built-in Google Search grounding, as a separate pre-call.** No
   new vendor, key, or licensing; never fetches third-party HTML into our process; returns
   span-level citations. A dedicated search API is 10–100× cheaper per call but adds a vendor, a
   fetcher, robots/licensing questions, and gives no span-level attribution.
2. **May the citation be a clickable URL?** — **Yes.** Plain text is barely better than 009, and the
   whole complaint is that the rep cannot check it. The obligations (https allowlist, post-validation
   `href`, `rel="noopener noreferrer"`, no template strings) are bounded and accepted. MV3 CSP does
   not restrict outbound links, so no manifest change.
3. **Must the model quote the supporting sentence?** — **The quote is required, but the model does
   not write it.** It is the span grounding metadata attributes to the chunk, which is categorically
   stronger than a prompt rule: the model cannot mis-quote text it never quoted. Capped at 240 chars
   to prevent a paragraph of licensed text passing through.
4. **What happens when retrieval finds nothing?** — **Exactly today's 009 behaviour.** Summary with
   no source link. Not an error, not a weaker guess, no partial render.
5. **Latency budget?** — **6s retrieval cap, ~20s total.** Timeout degrades per (4). Retrieval is the
   optional half and must never make the flow worse than 009.
6. **Is retrieval failure visible to the user?** — **No.** "Could not verify" on every brief is noise
   and is indistinguishable from the normal, correct outcome of finding nothing. Absence of the chip
   is the signal. Outcome is logged server-side, which is where the useful visibility actually is.

## Next steps

- P1 in progress. `.specify/feature.json` repointed to this feature.
