# Contract: Citation on the Buying Signal

**Endpoint**: `POST /api/leads/enrich` — request shape **unchanged**.
**Rule**: additive within the existing `buying_signal` object. Nothing in 009 is renamed, retyped, or
given new meaning.

## Existing — frozen

The three preview fields (`company_snapshot`, `personalized_opener`, `follow_ups[3]`) and the four
009 objects (`buying_signal`, `contact_confidence`, `outreach_email`, `crm_entry`) are unchanged.
See [009's contract](../../009-enrich-brief-parity/contracts/enrich-contract.md).

## New — two optional fields inside `buying_signal`

```jsonc
"buying_signal": {
  "summary": "string",            // 009, unchanged — required if the object is present
  "source":  "string | null",     // 009, unchanged — publisher name when retrieved,
                                  //   009's plain attribution when not
  "date":    "YYYY-MM-DD | null", // 009, unchanged

  "source_url": "string | null",  // NEW — https only; ONLY ever from retrieval metadata
  "quote":      "string | null"   // NEW — attributed span from the source page, <= 240 chars
}
```

## The three rules that make this safe

Enforced **server-side and client-side**, per the 009 both-sides principle: a stored enrichment can
predate a server-side validator.

### 1. `quote` requires `source_url`

A quote with nothing to check it against is a fabrication surface, not evidence. Quote-without-URL
drops **both** fields. The reverse is allowed: a URL with no quote is a weaker but honest citation.

### 2. `source_url` never comes from model-authored JSON

The model **cannot** put a URL into the response. `_validate_buying_signal` strips `source_url` and
`quote` from whatever the LLM emits, unconditionally, and logs when it sees them. The citation is
attached afterwards, by the server, from retrieval metadata only.

This is the rule that closes the hole retrieval opens. Without it, giving the model a retrieval
context would license it to emit plausible-looking URLs — which is exactly the fabrication 009's
FR-007 exists to prevent, dressed up as progress.

### 3. Scheme allowlist is `https` only

Anything else is treated as absent, including `http`. `javascript:` and `data:` are the attack cases;
`http` is excluded because a citation the rep is invited to click should not be downgradeable in
transit, and every credible publisher serves https.

## Presentation rules

1. **Link text is the hostname**, not the raw URL. The full URL goes in `title`. This is both more
   legible and the reason a long URL cannot break the resizable panel — though
   `overflow-wrap: anywhere` on `.brief-meta-item` remains the actual guarantee and must stay.
2. **The anchor is built with `createElement`.** `href` is assigned only after the client's own
   scheme check passes. Never a template string, never `innerHTML`.
3. **`rel="noopener noreferrer"`, `target="_blank"`.**
4. **The quote renders as text**, visually distinct from the summary so it reads as somebody else's
   words rather than the model's.
5. **No client-side derivation.** No source inferred from a domain, no date parsed from a URL slug,
   no favicon or site name synthesised from a hostname. Unchanged from 009, and it now has more
   surface to apply to.

## Degradation

| Situation | Result |
|---|---|
| Retrieval finds nothing | `summary` (+ 009 `source`/`date`); no `source_url`, no `quote` |
| Retrieval times out | identical to above |
| Retrieval errors | identical to above |
| Retrieval disabled / key unset | identical to above |
| Model emits a `source_url` | stripped; identical to above |
| `quote` present, `source_url` invalid | both dropped; identical to above |
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
| `web/src/api/client.ts` | two additive optional fields on the `buying_signal` type |
| `web/src/components/Preview.tsx` | citation branch inside the existing buying-signal section |
| `extension/sidepanel.js` | same, via `createElement`/`textContent` |
| `/api/leads/push` + CRM adapters | **none** |
| Stored historical enrichments | render as 009, exactly as today |
