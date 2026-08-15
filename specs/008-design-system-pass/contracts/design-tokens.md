# Contract: Design Token Sync

**Producer**: `design/tokens.css` (tracked upstream — the only file where a token value is edited)
**Consumers**: `web/src/index.css`, `extension/tokens.css`
**Enforcer**: `scripts/sync_design_tokens.py`

## Marker contract

Each consumer contains exactly one generated region, delimited verbatim:

```css
/* >>> generated: design tokens — edit design/tokens.css, run `make sync-tokens` */
:root { … }
/* <<< end generated */
```

Rules:

1. The script replaces **only** the text between the markers. Everything else in the consumer is
   hand-written and preserved.
2. Both markers MUST be present exactly once per consumer. Zero or duplicate markers is an error,
   not a silent no-op — a missing marker means a consumer would drift forever undetected.
3. Nothing outside the markers may define a token that the upstream also defines. The check greps
   for this and fails on a shadowing redefinition.
4. Content between the markers is machine-owned. Hand edits there are destroyed on the next sync,
   which is the intended behavior and why `--check` exists.

## Modes

| Invocation | Behavior | Exit |
|---|---|---|
| `python3 scripts/sync_design_tokens.py` | rewrite both consumers from upstream | 0 |
| `python3 scripts/sync_design_tokens.py --check` | compare only, write nothing | 0 if in sync, non-zero + diff on drift |

`make sync-tokens` and `make check-tokens` wrap these. `--check` is the gate-facing mode.

## Failure output

On drift, `--check` MUST print which consumer diverged and a line-level diff of the token region.
"Tokens are out of sync" alone is not actionable.

## Regression guard

`--check` additionally fails if any retired legacy value appears anywhere in either consumer:

```
#f97316  #0d1117  #161b22  #30363d  #e6edf3  #8b949e  #38bdf8  #4ade80  #f87171
```

This is what makes FR-002 ("the legacy palette MUST be fully retired") a test rather than an
intention. Hard-coded `rgba(249, 115, 22, …)` — the orange focus ring currently in
`sidepanel.html` — is caught by the same guard on the `249, 115, 22` triplet.

## Non-goals

- The script does not parse CSS. It does textual region replacement plus targeted greps. A CSS
  parser would be a dependency, and the extension tree must stay dependency-free.
- The script does not read `docs/design/`. That bundle is prose and React prototypes; the
  transcription into `design/tokens.css` is a deliberate one-time human step, not an automated
  import.
