# Contract: Citation on the Buying Signal

**Endpoint**: `POST /api/leads/enrich` — request shape **unchanged**.
**Rule**: additive within the existing `buying_signal` object. Nothing in 009 is renamed, retyped, or
given new meaning.

## Existing — frozen

The three preview fields (`company_snapshot`, `personalized_opener`, `follow_ups[3]`) and the four
009 objects (`buying_signal`, `contact_confidence`, `outreach_email`, `crm_entry`) are unchanged.
See [009's contract](../../009-enrich-brief-parity/contracts/enrich-contract.md).

## New — three optional fields inside `buying_signal`

```jsonc
"buying_signal": {
  "summary": "string",            // 009, unchanged — required if the object is present
  "source":  "string | null",     // 009, unchanged — publisher name when retrieved,
                                  //   009's plain attribution when not
  "date":    "YYYY-MM-DD | null", // 009, unchanged

  "sources": [                    // NEW — EVERY cited source, company's own domain
    { "url": "https://…",         //   first. https only; ONLY ever from retrieval
      "publisher": "string" }     //   metadata. Max 4.
  ],
  "finding": "string | null",     // NEW — the grounded search result attributed to
                                  //   `sources`. NOT a quote from any of them. <=240 chars
  "unverified_by_company": true   // NEW — present only when NO source is the company's
                                  //   own domain; renders as a caution to the rep
}

`source_url` (a single string) appears in enrichments stored before multi-source landed. Clients read
it as a one-entry `sources` and must not synthesise anything else from it.
```

## The three rules that make this safe

Enforced **server-side and client-side**, per the 009 both-sides principle: a stored enrichment can
predate a server-side validator.

### 1. `finding` requires at least one valid source

An unattributable claim is a fabrication surface, not evidence. Finding-without-sources drops
**both**. The reverse is allowed: sources with no finding are a weaker but honest citation.

**Every cited source is shown, not the best one.** A grounded sentence is routinely a synthesis
across several pages — P4's Klarna lead cited five, and no one of them contained the whole sentence.
Showing a single link beside such a sentence asserts that page says all of it, which is the
overstatement this feature exists to prevent. Sources are ordered with the company's own domain
first, because a company announcing its own news is both the better source and the likeliest to carry
the specifics.

**`finding` is not a quotation, and must never be presented as one.** Measured against the live API:
`groundingSupports[].segment.text` carries spans of the **model's own generated text**, not the
source page's — the API exposes no page text at all. What the metadata asserts is "the provider
attributes this sentence to this source". That is still worth showing, because it is the exact
evidence text the enrichment model was given, but rendering it in quote marks or a blockquote would
claim something untrue. Hence the name, and hence the `Search found:` prefix in both renderers.

### 2. `source_url` never comes from model-authored JSON

The model **cannot** put a URL into the response. `_validate_buying_signal` strips `source_url`,
`finding` and the legacy `quote` from whatever the LLM emits, unconditionally, and logs when it sees
them. The citation is
attached afterwards, by the server, from retrieval metadata only.

This is the rule that closes the hole retrieval opens. Without it, giving the model a retrieval
context would license it to emit plausible-looking URLs — which is exactly the fabrication 009's
FR-007 exists to prevent, dressed up as progress.

### 3. Scheme allowlist is `https` only

Anything else is treated as absent, including `http`. `javascript:` and `data:` are the attack cases;
`http` is excluded because a citation the rep is invited to click should not be downgradeable in
transit, and every credible publisher serves https.

## Presentation rules

1. **Link text is the hostname**, not the raw URL. The full URL goes in `title`. The hostname is
   the *resolved publisher* — the grounding API returns a `vertexaisearch.cloud.google.com` redirect,
   which the retrieval service follows before the URL is allowed near the brief. Rendering the raw
   redirect would tell the rep nothing and imply Google is the source. This is both more
   legible and the reason a long URL cannot break the resizable panel — though
   `overflow-wrap: anywhere` on `.brief-meta-item` remains the actual guarantee and must stay.
2. **The anchor is built with `createElement`.** `href` is assigned only after the client's own
   scheme check passes. Never a template string, never `innerHTML`.
3. **`rel="noopener noreferrer"`, `target="_blank"`.**
4. **The finding renders as plain text** on its own line, prefixed `Search found:` — deliberately
   not italicised, quoted, or set in a blockquote, since it is not a quotation.
5. **`unverified_by_company` renders a caution** in amber, telling the rep the signal may not be
   accurate and to check before sending. It is shown only alongside a citation: with no sources at
   all the section is already the honest 009 presentation and needs no warning. Its absence is not a
   guarantee of accuracy — only the absence of this specific weakness.
5. **No client-side derivation.** No source inferred from a domain, no date parsed from a URL slug,
   no favicon or site name synthesised from a hostname. Unchanged from 009, and it now has more
   surface to apply to.

## Degradation

| Situation | Result |
|---|---|
| Retrieval finds nothing | `summary` (+ 009 `source`/`date`); no `source_url`, no `finding` |
| Retrieval times out | identical to above |
| Retrieval errors | identical to above |
| Retrieval disabled / key unset | identical to above |
| Model emits a `source_url` | stripped; identical to above |
| `finding` present, every source invalid | both dropped; identical to above |
| Some sources invalid, at least one valid | valid ones render; invalid ones silently omitted |
| Grounding URI does not resolve to an https publisher URL | identical to above |
| Stored pre-010 enrichment | identical to above |

There is **one** degraded state and it is exactly 009's output. No partial render, no error, no
"could not verify" copy on the brief. Retrieval outcome is logged server-side instead.

## Prompt-side rules

1. **Evidence is fenced, last, and labelled untrusted.** Text inside the fence is evidence to be
   cited, never instructions to follow; instructions found inside are grounds to discard that chunk.
   Delimiters are stripped from retrieved text so it cannot close its own fence.
2. **The model may cite only what was retrieved.** No evidence → no citation, even if the model
   believes it knows one. This is 009's omit-rather-than-guess rule in retrieval shape.
3. **Evidence supports `buying_signal` only.** It must not be echoed into the snapshot, the opener,
   the email, or the CRM entry.
4. **The retrieval query carries company + signal only.** No skill methodology, no memory context, no
   agency setup reaches a third-party request.

## Compatibility matrix

| Consumer | Impact |
|---|---|
| `backend/tests/*` | none — additive; the 137 existing assertions untouched |
| `web/src/api/client.ts` | additive optional fields on the `buying_signal` type |
| `web/src/components/Preview.tsx` | citation branch inside the existing buying-signal section |
| `extension/sidepanel.js` | same, via `createElement`/`textContent` |
| `/api/leads/push` + CRM adapters | **none** |
| Stored historical enrichments | render as 009, exactly as today |
