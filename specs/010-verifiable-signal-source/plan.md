# Implementation Plan: A Verifiable Source for the Buying Signal

**Feature Branch**: `ai-bd-assistant` · **Spec**: [spec.md](./spec.md) ·
**Contract**: [contracts/citation-contract.md](./contracts/citation-contract.md) · **Date**: 2026-08-15
**Status**: P1–P4 complete. SC-002 passed on hand-check after four rounds.

## Summary

Give `buying_signal` a citation the rep can check: an `https` link to the publisher plus the grounded
sentence attributed to it. Retrieval comes from Gemini's built-in Google Search grounding, run as a **separate
pre-call** whose evidence is fenced into the existing enrichment prompt.

**The central finding**: unlike 009, this is a capability change, and the risk it adds is not
fabrication but **unsupported attribution** — a real link to a real page that does not say what the
brief claims. The design answers that with three structural defences rather than prompt discipline:

1. The model **cannot author a URL** — `source_url` is stripped from model JSON unconditionally and
   attached afterwards from retrieval metadata only.
2. The **finding comes from the retrieval call's grounded answer**, not the enrichment model's
   free-association, and it is the same evidence text the enrichment model is given.
   *(This defence was originally stated as "the quote is extracted from the page, so the model cannot
   mis-quote it". P3's live probe disproved that: `groundingSupports[].segment.text` is a span of the
   MODEL's text and the API exposes no page text at all. See P3 results.)*
3. A **finding cannot exist without a URL**, so every finding is one click from being falsified.
4. Retrieval asks the model to **verify a claim, not search for news** — added in P4, after an
   open-ended search cited a real bankruptcy record for a different company with a similar name.

## Technical Context

| Aspect | Value |
|---|---|
| Contract owner | `backend/app/services/llm_service.py` — `_validate_buying_signal`, `_build_prompt`, `_mock_generate`, `generate_enrichment` |
| New service | `backend/app/services/retrieval_service.py` — grounded pre-call, kept out of the already-849-line `llm_service` |
| Retrieval provider | Gemini Google Search grounding, `gemini-2.5-flash` |
| Renderers | `web/src/components/Preview.tsx`, `extension/sidepanel.js` |
| Gates | `cd backend && pytest tests/` (192), `cd web && npm run build`, `make check-tokens`, `make check-icons` |

### Why retrieval must be a separate call

`_call_gemini` sets `response_mime_type: application/json`. On `gemini-2.5-flash` the API **rejects**
`google_search` together with controlled generation. On Gemini 3, where it is permitted,
`grounding_chunks` and `grounding_supports` come back **empty** — losing exactly the citation data
this feature needs. So the architecture is forced, and it happens to be the one we want anyway:

```
retrieval_service.retrieve()      grounded call, 6s cap, NO json mode
      │  evidence: {finding, source_url, publisher}
      ▼
_build_prompt(..., evidence)      fenced, last, labelled untrusted
      │
      ▼
_call_gemini()                    unchanged: json mode, strict parse
      │
      ▼
_validate_buying_signal()         STRIPS any model-authored source_url/finding
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
| **P2 — Render** | Both surfaces render link + finding, re-validating the scheme client-side. Harness at 320/400/500/720 with a long hostname. | Yes — degrades to exact 009 output in prod until P3 lands |
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
| `extension/tokens.css` | P2 | citation + finding styling below the generated token block |

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
| No fabricated AI output | **PASS** | model cannot author a URL; retrieval verifies rather than searches; every citation hand-checked in P4 |
| Untrusted input handled | PASS | fenced, delimiter-stripped, scope-limited to `buying_signal` |
| 12px floor / no h-overflow | PASS | P2 harness, 320/400/500/720, long hostname |
| Version not hand-edited | PASS | `make bump-*` |
| Tests hermetic and offline | PASS | verified with sockets poisoned and a key set |
| Backend tests / web build green | PASS | 137 → 192 |

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
- **The finding is a `<blockquote>` with a left rule**, not a boxed section — evidence for the
  summary above it, not a section of its own. *(Superseded in P3: the blockquote and italics were
  removed once the live probe showed this is not a page quotation. It now renders as a plain
  `Search found:` line.)*

## P3 results — measured 2026-08-15

Retrieval built as `backend/app/services/retrieval_service.py` and wired into
`generate_enrichment` ahead of the model call. 181 backend tests pass (137 → 154 → 181), hermetic.

### The probe overturned a load-bearing assumption

The plan claimed the quote would be **extracted from grounding metadata, not generated**, and sold
that as the strongest defence against a confident-but-wrong citation. Measured against the live API,
that defence does not exist:

```
groundingSupports[].segment.text  ==  a slice of the MODEL's own answer   (verified True)
```

The API exposes **no source-page text at all**. What the metadata asserts is "the provider attributes
this sentence to this source" — genuinely useful, but not a quotation. The field was therefore
renamed `quote` → `finding` before it ever carried production data, the blockquote styling was
dropped, and both renderers now prefix it `Search found:`. What it does carry is the exact evidence
text the enrichment model was given, which is a real trust property: the rep sees the model's input.

Two further findings from the same probe:

- **`groundingChunks[].web.uri` is a `vertexaisearch.cloud.google.com` redirect**, not a publisher
  URL. P2's hostname-as-link-text would have rendered every citation as
  "vertexaisearch.cloud.google.com" — useless, and implying Google is the source. The service now
  follows the redirect (302 → `https://en.wikipedia.org/wiki/Anthropic`) before the URL goes near the
  brief. Only the redirect is followed; the page body is never read, so no HTML parsing, no robots
  question, no third-party page content in the process.
- **`groundingChunks[].web.title` is the publisher domain** (`techcrunch.com`, `anthropic.com`),
  which is what makes the resolved link legible.

### Why REST instead of the SDK

The installed `google-generativeai` 0.8.6 cannot express the tool at all — a string tool raises
*"The only string that can be passed as a tool is 'code_execution'"*, and `google_search_retrieval`
is refused by the API for 2.5 models (*"use google_search tool instead"*). `httpx` is already a
dependency for the CRM adapters, the response is plain JSON, and parsing `groundingMetadata`
directly is clearer than unwrapping protobufs. **No new dependency was added.**

### Hermeticity is now structural, not accidental

`generate_enrichment` reaches the network, so the suite could have started making live calls the
moment anyone ran it with a key exported — and it would have looked fine. Two guards:

- an autouse `conftest` fixture disables retrieval for every test; the retrieval tests opt back in
  and install an `httpx.MockTransport`;
- verified by running the whole suite with `socket.connect`/`getaddrinfo` poisoned **and**
  `GEMINI_API_KEY` set: 181 passed, no socket opened.

### Mutation check

Nine mutations, each reverted before the next; eight failed exactly the intended test. The ninth is
worth recording:

**"timeout no longer degrades" initially PASSED.** A timeout and a crash both return `None`, so
asserting the return value proved nothing about which branch ran — the test passed with the timeout
handler deleted. It now asserts the logged outcome (`RETRIEVAL: timeout`, and *not* `RETRIEVAL:
error`), because telling a slow search from a broken one is the only way to know whether the 6s
budget is set correctly. Re-mutated: caught.

Also caught during test-writing: patching `httpx.AsyncClient` with a factory that itself calls
`httpx.AsyncClient` recursed until the service swallowed a `RecursionError` as a generic retrieval
failure — a green-looking test proving nothing. The real class is now captured before patching.

## P4 results — hand-checked 2026-08-15 (SC-002, SC-006)

7 leads against real Gemini and real grounded retrieval, four rounds. **Every surviving citation was
opened and read.** Three of the seven leads are deliberate traps.

### Final round

| Lead | Citation | Hand-check |
|---|---|---|
| Anthropic — $13B Series F | `anthropic.com/news/…series-f…` | ✅ *"completed a Series F fundraising of $13 billion… $183 billion post-money"* |
| Figma — NYSE IPO | `blogs.easyequities.co.za/figma-lands-on-nyse…` | ✅ *"NYSE debut on July 31, 2025"* — date explicit |
| Klarna — US IPO filing | `klarna.com/…/klarna-files-registration-statement…` | ✅ Form F-1 language verbatim, dated March 14 2025 |
| **TRAP** obscure company | none | ✅ correctly declined |
| **TRAP** ambiguous name | none | ✅ correctly declined |
| **TRAP** false signal | none | ✅ correctly declined |
| partial date ("in March") | none | ✅ no citation, no fabricated date (009 holds) |

Latency mean **18.2s**, max **23.1s**. Mock fallbacks **0**. Citations **3/7** — and three of the four
absences are the correct answer.

### Four defects found, all by running it

**1. The predicted failure, exactly. (round 1 — FAIL)**
A deliberately FALSE signal — "Notion announced it is shutting down and filing for bankruptcy" —
produced a real PACER federal court record for **"Get Notion, LLC"**, a different, similarly-named
company. The brief would have corroborated a false premise with an official-looking court citation:
worse than no citation and worse than a fabricated one, because it is independently verifiable and
still wrong.

Root cause was the framing. Retrieval asked *"search for news about X"* — a question that has an
answer for any input, so something is always findable and the model finds something. It now asks
*"verify this claim about this entity"*, which can answer **no**, with namesakes, subsidiaries,
same-name businesses in other jurisdictions, and different-events named as mandatory rejections. The
verdict is a machine-checked `CONFIRMED:` prefix rather than prose inspected for the absence of a
denial.

**2. Evidence silently collapsed 3 of 7 leads to the mock. (round 1)**
Adding evidence to the prompt made responses longer and the JSON truncated mid-string at
`max_output_tokens: 4096` — raised to 8192. This is precisely the failure the 009 comment on that
constant warned about, re-triggered by a new cause. A mock brief also now carries **no citation at
all**: round 1 paired a real court-records link with *"That opens a short window to start a
conversation"*, lending borrowed authority to generic filler nothing grounded.

**3. A real, correctly-resolved URL that opens on nothing. (round 2 — FAIL)**
A true Figma claim cited `ebc.com/forex/figma-ipo-…`, which itself 302s to a broker's homepage with
no mention of Figma. Real link, true claim, and a rep clicking it lands on CFD marketing. Resolving
one hop from the grounding redirect is not enough. A liveness probe now HEADs the resolved URL and
drops the citation on 4xx/5xx or a cross-host bounce; same-site hops (`www.`, trailing slash) pass.

**4. One sentence, five sources, one link. (round 3 — FAIL)**
The Klarna citation asserted "Form F-1… on March 14, 2025" against a page carrying neither. The
grounding metadata showed why: a single support cited `groundingChunkIndices [0,1,2,3,4]` — the
sentence is a **synthesis across five pages**, no one of which need contain all of it — and the code
attributed it to index 0, `ultimamarkets.com`, while `klarna.com` sat unused at index 4. Retrieval
now prefers the company's **own domain** among the cited chunks, which is both a better source for
the rep and far likelier to state the specifics, since it is the company announcing its own news.

### Known gap

**Multi-chunk synthesis is mitigated, not solved.** When a support cites several chunks we still show
one link beside a sentence the provider attributes to all of them. Preferring the primary source
makes the shown link the one most likely to carry the detail, and the liveness probe ensures it
opens — but this is not a proof of attribution. Fully closing it means citing only sentences the
provider attributes to exactly one chunk, which would cut citation yield sharply. Worth revisiting
with real usage data on how often the single-chunk case occurs.

**Source quality is uncontrolled** where the company has no own-domain page in the results — the
Figma citation is a South African broker's blog, which is accurate here but not what a rep would
choose. There is no reputation ranking beyond the primary-source preference.

## P5 — multi-source, caution, and the terms question (2026-08-15)

Three follow-ups after P4, at the user's direction.

### Every cited source is now shown

P4's known gap is closed rather than mitigated. A grounded sentence attributed to
`groundingChunkIndices [0,1,2,3,4]` now renders **five chips**, not one. Showing a single link beside
a synthesis asserts that page says the whole sentence — the overstatement this feature exists to
prevent, and the exact shape of the Klarna defect. Sources keep the company's-own-domain-first
ordering, capped at 4 (`MAX_SOURCES`), each resolved and liveness-checked concurrently so N sources
cost one round trip rather than N.

`source_url` (singular) is still read by both clients for enrichments stored earlier in 010.

### The rep is warned when no source is the company's own

`unverified_by_company` renders an amber caution: *"No source from the company itself — this signal
may not be accurate. Check before sending."* When every source is third-party, they may simply be
reporting each other, which is the weakest evidence this feature can produce while still producing
something. That was previously visible only as a list of domain names the rep had to interpret.

Shown only alongside a citation — with no sources the section is already 009's honest presentation
and needs no warning. **Its absence is not a guarantee of accuracy**, only the absence of this
specific weakness, and the copy is worded to match.

### Google's grounding terms — resolved, and the answer is uncomfortable

Read directly from the Gemini API terms. Two clauses bear on what we built:

> *"you will not modify, or intersperse any other content with, the Grounded Results or Search
> Suggestions"* … *"you will only display the Grounded Results with the associated Search
> Suggestion(s) to the end user who submitted the prompt"*

Measured against those, **this implementation does not currently comply on two points**:

1. **We modify the Link.** Resolving `vertexaisearch.cloud.google.com/grounding-api-redirect/…` to the
   publisher URL replaces the Link Google returned. The product argument for it is strong and was the
   explicit instruction: a chip reading "vertexaisearch.cloud.google.com" tells the rep nothing,
   implies Google is the source, and hides the destination before the click — which defeats
   checkability, the entire point of the feature. Kept, deliberately.
2. **We do not render Search Suggestions.** `groundingMetadata.searchEntryPoint` returns HTML/CSS the
   terms require be displayed alongside grounded results. We currently discard it.

A third clause — *"you will not cache … Grounded Results"* — is arguably engaged by storing the
citation on a persisted enrichment, though the terms do permit storage for "end-user chat history",
which a saved lead brief plausibly is.

**This needs legal sign-off before real reps see it, and it is not a decision this plan can make.**
The compliance-shaped alternative is to render the redirect URI as-is plus the Search Suggestions
block, at a real cost to the feature's usefulness. Recorded here rather than resolved.

## Risks

| Risk | Mitigation |
|---|---|
| **A real link that does not support the claim.** The failure this feature exists to prevent, and the one most likely to occur — **it occurred, three times, in three distinct forms** | Retrieval verifies a claim rather than searching for news, with a machine-checked `CONFIRMED:` verdict; a liveness probe drops links that 404 or bounce off-host; the company's own domain is preferred among cited chunks; finding requires URL. All four defences were added *because* P4 caught the corresponding failure — none were sufficient in advance |
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
3. **Must the model quote the supporting sentence?** — **Answered yes, then overturned by
   measurement.** The plan assumed grounding metadata exposes the source page's text. It does not:
   `segment.text` is a span of the model's own answer. There is no page quote to be had without
   fetching and parsing the page, which is out of scope. The field became `finding` — the grounded,
   provider-attributed sentence, which is also the exact evidence the enrichment model receives —
   and is never presented as a quotation. Capped at 240 chars.
4. **What happens when retrieval finds nothing?** — **Exactly today's 009 behaviour.** Summary with
   no source link. Not an error, not a weaker guess, no partial render.
5. **Latency budget?** — **6s retrieval cap, ~20s total.** Timeout degrades per (4). Retrieval is the
   optional half and must never make the flow worse than 009.
6. **Is retrieval failure visible to the user?** — **No.** "Could not verify" on every brief is noise
   and is indistinguishable from the normal, correct outcome of finding nothing. Absence of the chip
   is the signal. Outcome is logged server-side, which is where the useful visibility actually is.

## Next steps

- P1 in progress. `.specify/feature.json` repointed to this feature.
