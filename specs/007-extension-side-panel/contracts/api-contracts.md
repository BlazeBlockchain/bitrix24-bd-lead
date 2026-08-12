# API Contracts (FROZEN — regression reference)

**Feature**: `specs/007-extension-side-panel`

These contracts are **not** changed by this feature. They are transcribed here from the current
backend and the current `extension/popup.js` so that the rewrite can be diffed against them. The web
app and the backend test suite depend on these shapes (NFR-002).

Source of truth: `backend/app/api/leads.py`, `backend/app/api/auth.py`.

## Authentication — applies to every leads endpoint

All leads endpoints depend on `get_current_user_api` (`backend/app/api/auth.py:54`), which **raises
401 when the `Authorization` header is absent**. The former DEBUG stub-user fallback was removed.

```
Authorization: Bearer <backend-issued JWT>     # REQUIRED, not optional
```

## POST /api/leads/enrich

### Request

`Content-Type: application/json`, body is `LeadPushInput` (`backend/app/api/leads.py:42`):

| Field | Type | Required | Default |
|---|---|---|---|
| `company_name` | string | yes | — (`min_length=1`) |
| `deal_name` | string | yes | — (`min_length=1`) |
| `contact_name` | string | yes | — (`min_length=1`) |
| `contact_role` | string | yes | — (`min_length=1`) |
| `signal` | string | no | `"stub signal"` |
| `signal_type` | string | no | `"new_launch"` |
| `pain_point` | string | no | `"stub pain"` |
| `email_subject` | string | no | `"Intro"` |
| `notes` | string | no | `"stub notes"` |

The four required fields have `min_length=1`, so the client must never send `""` for them. The
current popup guards this with placeholder defaults (`'Acme Corp'`, `'Jane Doe'`, `'Head of Growth'`,
`` `${company} Intro Deal` ``); `lead-api.js` must preserve equivalent guarding.

Optional fields are omitted (`undefined`) rather than sent empty — preserve that, since sending `""`
is not equivalent to omitting (the server default would be lost).

### Response 200

```jsonc
{
  "company_snapshot":    "string",
  "personalized_opener": "string",
  "follow_ups": [                      // exactly 3
    {
      "title":       "string",
      "description": "string",
      "due_in_days": 0,                // number
      "rationale":   "string"
    }
  ],
  "model_used":     "string",          // optional, rendered as provenance
  "memory_note":    "string",          // optional
  "authenticated_as": "string",
  "provider_default": "string",
  "memory_context_injected": true
}
```

The panel MUST render `company_snapshot`, `personalized_opener`, and all three `follow_ups` entries
with `title`, `description`, `due_in_days`, `rationale` (FR-012).

### Errors

| Status | Meaning | Panel message class |
|---|---|---|
| 401 | missing/expired/invalid JWT | "session" — offer sign-in |
| 422 | request body failed validation | "input" |
| 502 | `LLM enrichment failed: …` | "service" |
| network throw | backend unreachable | "unreachable" |

## POST /api/leads/push

### Request

Query: `?provider=bitrix24|hubspot` (optional `&token=` override — **not** used by the extension).
Body: identical `LeadPushInput` as above.

### Response 200

Ids shape from the orchestration service plus:

```jsonc
{
  "contact_id": "…",
  "deal_id":    "…",
  // …task ids / core result fields…
  "enriched_preview": { /* same shape as /enrich */ },
  "provider": "bitrix24",
  "authenticated_as": "…",
  "note": "…"
}
```

The current popup surfaces `result.contact_id` and `result.deal_id` on success — preserve.

### Errors

| Status | Meaning |
|---|---|
| 400 | no CRM token configured for provider |
| 401 | missing/expired/invalid JWT |
| 502 | `CRM operation failed: …` |

## POST /api/auth/google — used by the new sign-in flow

### Request

```jsonc
{ "id_token": "<Google ID token>" }
```

`aud` **must** equal the backend's `GOOGLE_CLIENT_ID` — `verify_oauth2_token` pins a single
audience (`backend/app/api/auth.py:160`). Hence the extension reuses the web app's OAuth client ID.

### Response 200

```jsonc
{
  "access_token": "<JWT>",
  "token_type":   "bearer",
  "expires_in":   3600,          // seconds; JWT_EXPIRE_MINUTES * 60
  "user": { "id": "…", "email": "…", "display_name": "…" }
}
```

### Errors

| Status | Meaning |
|---|---|
| 401 | `Invalid Google ID token: …` |
| 501 | `GOOGLE_CLIENT_ID` not configured server-side — surface as a setup message, not a crash |
| 500 | user lookup/creation failed |

## GET /api/auth/me — used for session validation

Requires `Authorization: Bearer <JWT>`.

```jsonc
{ "id": "…", "email": "…", "display_name": "…", "created_at": "…" }
```

401 ⇒ treat the stored session as expired: clear it and prompt sign-in (FR-010).

## Error classification contract (internal)

`lead-api.js` maps every failure into exactly one of the three states FR-014 requires, so the UI
never shows a raw status code:

| Class | Trigger | User-facing meaning |
|---|---|---|
| `unreachable` | `fetch` rejects / `/health` fails | "Can't reach the BD Lead service" |
| `session` | HTTP 401 | "Signed out or session expired" + sign-in action |
| `service` | any other non-2xx | server's `detail`, verbatim but escaped |
