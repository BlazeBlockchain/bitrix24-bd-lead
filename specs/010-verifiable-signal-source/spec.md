# Feature Specification: A Verifiable Source for the Buying Signal

**Feature Branch**: `ai-bd-assistant`
**Created**: 2026-08-15
**Status**: Draft — P1 in progress
**Input**: User request — "give the buying signal a real, verifiable source", following
`specs/009-enrich-brief-parity/`, which shipped `buying_signal.source` honest but uninformative.

## Problem

009 made the buying-signal section real: it carries a summary, an optional source, and an optional
date. Measured against real Gemini across 5 diverse leads, `source` came back as
**"reported in the lead brief" 5 times out of 5**.

That is correct behaviour, not a bug. Without retrieval the model has nothing else it can honestly
attribute to, and 009's anti-fabrication rule tells it to omit rather than guess. The result is a
Source chip that is honest and completely uninformative — it tells the rep something they already
know, because they typed it.

Making the chip informative requires the thing 009 declared out of scope: **actual retrieval**.
009 was a contract change. **This is a capability change**, and it is the highest-risk feature in the
product so far.

### Why the risk is higher, not lower

009's design principle is *a fabricated citation is worse than an absent one*. Retrieval does not
remove that risk — it **relocates** it. Instead of the model inventing a plausible source string, it
can now cite a **real URL that does not say what the model claims it says**. A confident link to a
real page that does not support the claim is *more* damaging than "reported in the lead brief",
because the link looks like proof. The rep's trust goes up while the accuracy goes down.

This feature must therefore be designed against *unsupported-but-real* citations, not merely against
*invented* ones.

### The technical constraint that shapes the design

On `gemini-2.5-flash`, Grounding with Google Search and controlled generation are **mutually
exclusive** — the API rejects the combination ("controlled generation is not supported with
google_search tool"). On Gemini 3, where the combination is permitted, `grounding_chunks` and
`grounding_supports` return **empty**, which removes the citation data that is the entire point.

`_call_gemini` sets `response_mime_type: application/json`, and that is load-bearing for the whole
parse path. Retrieval therefore **cannot** be folded into the existing call. It must be a separate,
earlier call whose output is fed to the enrichment call as evidence.

## User Story

As a business-development user, I want the buying signal to cite a page I can open and a sentence I
can read, so that I can tell in one glance whether the brief is describing something that actually
happened — instead of being told the signal came from the form I filled in myself.

### Acceptance Scenarios

1. **The citation is checkable in one glance** — Given a lead whose signal is publicly reported, when
   the user opens the brief, then the buying-signal section shows a link to the source page and the
   supporting sentence from that page, without the user needing to open the link to judge it.

2. **The citation supports the claim** — Given any brief showing a citation, when a reviewer opens
   the cited page, then that page states what the brief's summary claims. A real link that does not
   support its claim is a defect of the same severity as a fabricated one.

3. **Nothing found degrades to 009** — Given retrieval finds nothing, times out, or fails, when the
   brief renders, then the buying-signal section is exactly what 009 ships today: a summary, and no
   source link. Not an error, not a warning on the brief, and not a weaker guess.

4. **The model cannot author a citation** — Given the model emits a `source_url` in its JSON, when
   the response is validated, then that URL is discarded. Only URLs carried by retrieval metadata may
   reach the client.

5. **A quote is never orphaned** — Given a quote is present without a URL to check it against, when
   the response is validated, then both are dropped, because an uncheckable quote is a fabrication
   surface rather than evidence.

6. **Links are safe** — Given a citation renders as a clickable link, when the user clicks it, then
   the scheme has been validated `https`-only on the server and re-validated on the client, and the
   anchor carries `rel="noopener noreferrer"`.

7. **Nothing regresses** — Given any existing consumer, when this feature ships, then the three
   frozen preview fields and the four 009 objects keep their exact names, types, and meanings.

### Edge Cases

- A deliberately obscure company with little web presence — where a retrieval system is most tempted
  to cite something adjacent rather than nothing. This is the primary stress case.
- The retrieved page is about a *different* company with a similar name.
- The retrieved page supports a *different* signal than the one the rep typed.
- Retrieved page content contains instructions aimed at the model (prompt injection).
- Retrieval succeeds but the grounding metadata carries no usable URI.
- A very long URL in a user-resizable panel that must never scroll horizontally.
- A stored enrichment created before this feature: no `source_url`, no `quote`, renders as 009.
- Retrieval is disabled by configuration or the provider key is unset — must be identical to case 3.

## Requirements

### Functional

- **FR-001**: `buying_signal` MUST gain optional `sources`, `finding` and `unverified_by_company`
  fields. The 009 fields `summary`, `source`, `date` keep their exact names, types, and meanings.
- **FR-002**: Every source URL MUST be `https`-only. Any other scheme — including `http`,
  `javascript:`, and `data:` — MUST be treated as absent.
- **FR-003**: `finding` MUST NOT survive without at least one valid source. Finding-without-sources
  drops both.
- **FR-004**: `finding` MUST be length-capped so a paragraph of third-party text cannot pass through.
- **FR-005**: Model-authored `sources`, `source_url`, `finding`, `quote` or `unverified_by_company`
  in the LLM's JSON MUST be discarded. These fields may only be populated from retrieval metadata,
  by the server, after parsing.
- **FR-006**: When retrieval returns nothing, times out, errors, or is disabled, the response MUST be
  shaped exactly as 009 — the new keys simply absent.
- **FR-007**: Retrieval MUST be bounded by a configurable timeout, and exceeding it MUST degrade per
  FR-006 rather than failing the enrichment.
- **FR-008**: Retrieved third-party text MUST be treated as untrusted input: fenced in the prompt,
  labelled as evidence and never as instructions, and unable to escape its own delimiters.
- **FR-009**: The retrieval query MUST be built from the lead's company and signal only. No skill
  methodology, no memory context, and no agency setup may enter a third-party request.
- **FR-010**: Retrieved evidence MAY support `buying_signal` only. It MUST NOT be echoed into
  `company_snapshot`, `personalized_opener`, `outreach_email`, or `crm_entry`.
- **FR-011**: The mock generator MUST produce the full shape including a citation, so the
  no-API-key path and the test suite exercise the populated presentation.
- **FR-012**: Both surfaces MUST render the link and quote, and MUST re-validate the scheme
  client-side, per the 009 both-sides rule.
- **FR-013**: Retrieval outcome (attempted / found / empty / timeout / error) MUST be logged
  server-side. It MUST NOT be surfaced on the brief.
- **FR-014**: When a grounded statement is attributed to several sources, ALL of them MUST be shown.
  Attributing a multi-source synthesis to one link overstates what that page says.
- **FR-015**: Cited sources MUST be ordered with the company's own domain first, and a citation with
  NO company-own source MUST carry a caution telling the rep the signal may not be accurate.
- **FR-016**: A cited URL MUST be confirmed reachable and MUST NOT redirect to a different host. A
  citation the rep cannot open, or that lands somewhere else, is not a citation.
- **FR-017**: Retrieval MUST be framed as verifying a claim about a named entity, not as an
  open-ended search. It MUST reject namesakes, subsidiaries, same-name entities in other
  jurisdictions, and different events, and MUST return an explicit machine-checkable verdict.

### Non-Functional

- **NFR-001**: The three frozen preview fields and the four 009 objects MUST be unchanged; the
  existing 137 backend tests MUST pass without assertion changes about them.
- **NFR-002**: The test suite MUST stay hermetic and offline. Retrieval is mocked; no live network.
- **NFR-003**: The extension MUST remain buildless, and the citation MUST be rendered with
  `createElement`/`textContent`. `href` may be assigned only after scheme validation, and the anchor
  MUST NOT be built from a template string.
- **NFR-004**: Retrieval MUST NOT add more than ~6s to enrichment; total MUST stay within ~20s.
- **NFR-005**: Retrieval cost per enrichment MUST be recorded alongside the existing LLM prices, with
  the same "list price, not fetched, verify before billing" caveat.
- **NFR-006**: No text below 12px, and no horizontal overflow in the panel at any width, verified
  with a long real URL in the source chip.
- **NFR-007**: The BD Lead Research skill methodology MUST remain server-side and MUST NOT leak into
  any third-party retrieval request.

## Success Criteria

- **SC-001**: On a lead whose signal is publicly reported, the brief shows a working link and a
  supporting sentence — not "reported in the lead brief".
- **SC-002**: In a hand-checked sample of ≥6 real enrichments including a deliberately obscure
  company, **every** citation is both real and supportive of its claim. One real-but-unsupportive
  citation is a FAIL.
- **SC-003**: With retrieval forced to return nothing, the brief is byte-identical to 009 output.
- **SC-004**: A model-authored source never reaches the client, proven by test.
- **SC-008**: A multi-source synthesis shows every source; a citation with no company-own source
  shows a caution. Both proven by test and by the browser harness on both surfaces.
- **SC-005**: No non-`https` scheme reaches an `href`, proven by test on both sides.
- **SC-006**: Latency and cost delta are measured and recorded.
- **SC-007**: The panel does not scroll horizontally at 320/400/500/720 with a long real URL.

## Key Entities

- **Citation** — a validated `source_url` plus an optional supporting `quote`, produced only by
  retrieval, never by the model.
- **Evidence** — the retrieved text and its source URIs, as returned by grounding metadata. Untrusted
  input; fenced in the prompt; supports `buying_signal` only.
- **Retrieval outcome** — attempted / found / empty / timeout / error. Logged, never rendered.
- **Buying signal** — the 009 entity, extended with a citation. Not reshaped.

## Assumptions

- Gemini's built-in Google Search grounding is the retrieval source, as a separate pre-call. Chosen
  over a dedicated search API because it adds no vendor, key, or licensing question, never fetches
  third-party HTML into our process, and returns citations tied to text spans.
- Grounding is free under 1,500 requests/day, then $35/1,000 grounded prompts (≈3.5¢ per enrichment,
  roughly 4× today's total cost). Verified 2026-08-15 on ai.google.dev/gemini-api/docs/pricing; not
  fetched at runtime.
- ~~The supporting quote is taken from grounding metadata's attributed text span~~ — **disproved in
  P3.** `groundingSupports[].segment.text` is a span of the MODEL's own answer, and the API exposes
  no source-page text. The field is `finding`: the grounded, provider-attributed sentence, which is
  also the exact evidence the enrichment model receives. It is never presented as a quotation.
- Absence of a citation is a legible signal on its own. No "we could not verify this" copy. The one
  exception, added after P4: when sources exist but none is the company's own, a caution IS shown —
  that is a specific, actionable weakness rather than the generic absence of evidence.

- **Google's Grounding with Google Search terms are not fully met by this implementation.** See the
  compliance note in the plan. Resolving the redirect URI to the publisher and not rendering the
  returned Search Suggestions are both deliberate product choices that need legal sign-off before
  this is exposed to real reps.

## Out of Scope

- Streaming or step-by-step research progress from the server (needs a different API shape).
- Wiring `crm_entry` to the actual push, or any change to `/api/leads/push` or the CRM adapters.
- Retrieval for anything other than the buying signal.
- Onboarding and billing screens.
- Changing the three frozen preview fields or reshaping the four 009 objects.
