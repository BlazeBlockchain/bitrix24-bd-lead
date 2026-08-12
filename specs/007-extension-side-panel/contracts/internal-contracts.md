# Internal Contracts: extension module surfaces

**Feature**: `specs/007-extension-side-panel`

All modules are **classic scripts** exposing a single global (no ES modules, no bundler — NFR-001),
matching the existing `config.js` pattern. Load order matters and is fixed per page.

## Load order

```html
<!-- sidepanel.html -->
<link rel="stylesheet" href="tokens.css">
<script src="config.js"></script>   <!-- constants only, no side effects -->
<script src="auth.js"></script>     <!-- depends on config -->
<script src="lead-api.js"></script> <!-- depends on config + auth -->
<script src="capture.js"></script>  <!-- depends on nothing but chrome.* -->
<script src="sidepanel.js"></script>
```

`popup.html` loads `tokens.css`, `config.js`, `auth.js`, `popup.js`.
`options.html` loads `tokens.css`, `config.js`, `auth.js`, `options.js`.

## `config.js` — additions

```js
const DEFAULT_GOOGLE_CLIENT_ID = '';   // ships empty; real value is a stored setting
const OAUTH_SCOPES = 'openid email profile';
const MIN_CHROME_FOR_PANEL = 116;

const STORAGE_KEYS = {
  JWT: 'bd_jwt',              // unchanged key — existing pasted tokens keep working
  PROVIDER: 'bd_provider',    // unchanged
  DEMO_TOKEN: 'bd_demo_token',// unchanged
  USER: 'bd_user',            // NEW: { id, email, display_name }
  JWT_EXPIRES_AT: 'bd_jwt_exp', // NEW: epoch ms, from expires_in
  DRAFT: 'bd_draft',          // NEW: session-scoped lead draft
  GOOGLE_CLIENT_ID: 'bd_google_client_id', // NEW: configured via the options page
};
```

### Why the client ID is a stored setting, not a constant

A Google OAuth *web* client ID is public — the web app ships it in its bundle. But in this repo the
value lives in `web/.env`, which is **gitignored**, while `extension/config.js` is **tracked**.
Hardcoding it would commit a value the repo deliberately keeps untracked, and would leave every
developer with a permanently dirty working tree after editing it.

Resolution: `config.js` ships `DEFAULT_GOOGLE_CLIENT_ID = ''`, and the real value is entered once on
the options page and kept in `chrome.storage.local[bd_google_client_id]`.

```js
BDAuth.getClientId(): Promise<string>   // stored value, else DEFAULT_GOOGLE_CLIENT_ID
```

When it resolves empty, `signIn()` rejects with a `setup`-classed error whose message points at the
options page — rather than launching a doomed auth flow. Rejected alternatives: a gitignored
`config.local.js` (a missing file logs a console 404, violating SC-006) and committing the value
directly (contradicts the repo's own `.gitignore`).

## `BDAuth` (`auth.js`)

```js
BDAuth.signIn(): Promise<Session>
```
Runs `chrome.identity.launchWebAuthFlow` against Google's authorization endpoint with
`response_type=id_token`, `scope=openid email profile`, `nonce=<crypto.randomUUID()>`,
`redirect_uri=chrome.identity.getRedirectURL()`. Parses the **fragment** of the returned URL,
verifies the `nonce` claim round-tripped, then `POST /api/auth/google`. Persists JWT, user, and
expiry. Rejects with a classified error.

```js
BDAuth.signOut(): Promise<void>
```
Clears `JWT`, `USER`, `JWT_EXPIRES_AT`. Never clears `PROVIDER` (a UI preference, not a credential).

```js
BDAuth.getSession(): Promise<Session>
```
Returns `{ state, user }` **without** a network call, using stored expiry:

| `state` | Condition |
|---|---|
| `'absent'` | no stored JWT |
| `'expired'` | stored expiry is in the past |
| `'valid'` | stored JWT present and unexpired |

```js
BDAuth.validate(): Promise<Session>
```
`GET /api/auth/me`. On 401 clears the session and returns `{ state: 'expired' }`. Called on panel
open, not on every keystroke.

```js
BDAuth.authHeaders(): Promise<Record<string,string>>
```
Returns `{ Authorization: 'Bearer …' }`, or throws a `session`-classed error if absent/expired —
so callers cannot accidentally send an unauthenticated request the backend will 401 (see
`api-contracts.md`).

## `BDApi` (`lead-api.js`)

```js
BDApi.buildInput(formValues): LeadPushInput
```
Sole owner of the request shape. Applies the required-field guards and omits empty optionals.

```js
BDApi.enrich(input): Promise<Enrichment>
BDApi.push(input, provider): Promise<PushResult>
BDApi.health(): Promise<boolean>
```
All attach `BDAuth.authHeaders()`. All reject with `{ class, message }` where `class` is one of
`unreachable | session | service | input`.

`health()` uses `HEAD ${API_BASE}/health` and resolves to a boolean; it never throws.

## `BDCapture` (`capture.js`)

```js
BDCapture.fromActiveTab(): Promise<PageContext>
```

Returns `{ company, signal, url, title, selection }` with any field possibly `null`. Implementation:
`chrome.tabs.query({ active: true, currentWindow: true })` then `chrome.scripting.executeScript`
with a **self-contained** `func` (no closure over panel scope — it is serialized into the page).

Rejects with `{ class: 'restricted' }` on `chrome://`, Web Store, PDF viewer, and other blocked URLs.
Resolves with all-`null` fields when the page yields nothing usable — the caller then leaves the form
untouched and reports "nothing found" (spec edge case 2).

```js
BDCapture.merge(pageContext, currentFormValues): { patch, conflicts }
```
Pure function, no DOM access, so it is directly testable. `patch` covers only currently-empty fields;
`conflicts` lists fields that hold a different non-empty value. The caller confirms before applying
conflicts (FR-007).

## `background.js` message contract

The panel and popup are extension pages with direct API access, so **no fetch proxying is needed**
(that requirement applies only to the content-script design that was rejected). The service worker
handles only panel lifecycle:

| Message | From | Effect |
|---|---|---|
| `{ type: 'OPEN_PANEL', windowId }` | popup | `chrome.sidePanel.open({ windowId })` |

Plus non-message duties: `chrome.sidePanel.setOptions` registration on install, a context-menu entry,
and a `chrome.commands` keyboard shortcut — both of which open the panel.

The existing catch-all `onMessage` listener that logs every message and replies
`{ status: 'received' }` is replaced; it currently logs full message payloads, which would leak
credentials to the console once auth traffic exists (NFR-006).
