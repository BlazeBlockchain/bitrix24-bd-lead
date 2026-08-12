# Phase 1 Data Model: Extension Side Panel Workspace

**Feature**: `specs/007-extension-side-panel` | **Date**: 2026-08-12

This feature introduces **no database entities and no backend schema changes**. Everything below is
client-side state held in `chrome.storage` or in the panel's memory.

## LeadDraft

The user's in-progress capture. One per browser window (spec A-003, A-007).

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `company_name` | string | non-empty at submit | guarded default at request build |
| `contact_name` | string | non-empty at submit | guarded default at request build |
| `contact_role` | string | non-empty at submit | guarded default at request build |
| `signal` | string \| null | — | omitted from request when empty |
| `pain_point` | string \| null | — | omitted when empty |
| `notes` | string \| null | — | omitted when empty |
| `provider` | `'bitrix24' \| 'hubspot'` | enum | mirrors `STORAGE_KEYS.PROVIDER` |
| `source_url` | string \| null | — | set by capture; appended into notes |

**Storage**: `chrome.storage.session` under `STORAGE_KEYS.DRAFT`. Session storage is memory-backed
and cleared when the browser closes, so prospect data never lands on disk (NFR-006).

**Persistence rules**:
- Written debounced (~400ms) on input, and immediately when a preview is generated.
- Read on panel open to rehydrate.
- Cleared after a successful push.
- `deal_name` and `email_subject` are **derived**, not stored — computed at request-build time from
  `company_name`, exactly as the current popup does.

**Lifecycle**:

```
empty ──user input──▶ dirty ──generate──▶ previewed ──push ok──▶ cleared ──▶ empty
                        ▲                     │
                        └────user edits───────┘   (preview invalidated, push re-disabled)
```

Editing any form field after a preview exists invalidates the preview: the push action returns to
disabled, because pushing would send input that no longer matches what the user reviewed.

## Enrichment

The generated preview. Shape is **fixed by the API contract** and must not be reshaped (NFR-002).

| Field | Type | Required | Rendering |
|---|---|---|---|
| `company_snapshot` | string | yes | body paragraph |
| `personalized_opener` | string | yes | quoted block, copyable |
| `follow_ups` | FollowUp[3] | yes | ordered list of cards |
| `model_used` | string | no | provenance footer |
| `memory_note` | string | no | provenance footer |

### FollowUp

| Field | Type | Rendering |
|---|---|---|
| `title` | string | card heading |
| `description` | string | card body |
| `due_in_days` | number | `+N days` badge |
| `rationale` | string | muted sub-line |

**Held in memory only**, alongside the draft in `storage.session`. Every string is rendered via
`textContent` — never interpolated into `innerHTML` (NFR-005). The current `popup.js:83-121` builds
HTML by string concatenation with an `escapeHtml` helper; the rewrite uses DOM construction so
escaping cannot be forgotten on a future field.

**Validation before render**: if `company_snapshot` is absent, treat the response as unusable and
show the `service` error state rather than a half-rendered preview. If `follow_ups` has fewer than 3
entries, render what exists and note the shortfall — do not pad with placeholders.

## Session

The signed-in identity and the credential presented to the API.

| Field | Type | Storage key | Notes |
|---|---|---|---|
| `token` | string | `bd_jwt` | backend-issued JWT; **key unchanged** so existing pasted tokens survive |
| `user` | `{ id, email, display_name }` | `bd_user` | for the "signed in as" display |
| `expires_at` | number (epoch ms) | `bd_jwt_exp` | `Date.now() + expires_in * 1000` |

**Storage**: `chrome.storage.local` — must outlive browser restarts, unlike the draft.

**States**:

```
absent ──signIn()──▶ valid ──expiry passes──▶ expired ──signIn()──▶ valid
   ▲                   │                        │
   └───signOut()───────┴────401 from /me────────┘
```

`state` is derived from `expires_at`, never stored, so it cannot go stale. A 401 from any endpoint
transitions to `expired` and clears `token`.

**Constraints**:
- Never logged. The existing `background.js:26-30` catch-all message logger is removed for this
  reason.
- Never sent to any origin other than `API_BASE`.
- Not readable by visited pages: it lives in extension storage, and no content script is injected
  that could bridge it into a page.

## PageContext

Transient capture from the active tab. **Never persisted.**

| Field | Type | Source heuristic |
|---|---|---|
| `company` | string \| null | `og:site_name` → `application-name` → JSON-LD `Organization.name` → hostname |
| `signal` | string \| null | user selection → `og:description` → `meta[description]`, truncated |
| `title` | string \| null | `document.title` |
| `url` | string \| null | canonical link → `location.href` |
| `selection` | string \| null | `window.getSelection().toString()`, trimmed |

Discarded once merged into the draft. `contact_name` and `contact_role` are deliberately **not**
inferred (research R-004): a wrong contact name is worse than an empty field.

## Relationships

```
Session ──authorizes──▶ Enrichment requests
                              │
LeadDraft ───generates────────┘
    ▲
    │ merge (patch, user-confirmed on conflict)
PageContext (transient)
```

`Enrichment` is bound to the `LeadDraft` that produced it and is invalidated when that draft changes.
`PageContext` has no lifetime beyond a single capture action.
