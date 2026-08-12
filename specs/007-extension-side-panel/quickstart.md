# Quickstart: Extension Side Panel Workspace

**Feature**: `specs/007-extension-side-panel`

How to set up, load, and drive the upgraded extension. Requires **Chrome 116+** (see research R-002).

## 1. Start the backend and web app

```bash
make dev                       # or: docker compose up --build
curl -s localhost:8000/api/health
```

The extension talks to `API_BASE` from `extension/config.js` (`http://localhost:8000/api` in dev),
which is already covered by `host_permissions`. **`CORS_ORIGINS` does not need to be set for the
extension** — extension pages are not subject to CORS for hosts they hold permissions for. You still
want `CORS_ORIGINS=http://localhost:5173` for the Vite dev server.

## 2. Pin the extension ID (one time)

Google OAuth redirect URIs must be registered in advance, and the redirect URI embeds the extension
ID. An unpacked extension's ID is derived from its `key`, so pin one or the ID will change and
sign-in will break.

```bash
# generate a keypair and print the manifest "key" value
openssl genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out extension-key.pem
openssl rsa -in extension-key.pem -pubout -outform DER | base64 -w0
```

Add the printed base64 as `"key"` in `extension/manifest.json`.

> Keep `extension-key.pem` **out of the repository** — add it to `.gitignore`. The public `key` in
> the manifest is not a secret; the `.pem` is.

Load the extension (step 3), then copy the ID Chrome shows on the card. Confirm the redirect URI by
running this in the extension's service-worker console:

```js
chrome.identity.getRedirectURL()   // => https://<EXTENSION_ID>.chromiumapp.org/
```

## 3. Load unpacked

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select the `extension/` directory
4. Note the extension ID on the card

After each code change: click the reload icon on the card. Changes to `manifest.json` always require
a reload; changes to `sidepanel.js`/`popup.js` require closing and reopening the surface.

## 4. Register the OAuth redirect URI (one time)

In Google Cloud Console → **APIs & Services → Credentials** → open the **same** OAuth 2.0 Web
application client the web app uses (`web/.env` → `VITE_GOOGLE_CLIENT_ID`):

- Add to **Authorized redirect URIs**: `https://<EXTENSION_ID>.chromiumapp.org/`

Then set the matching value in the extension's **options page** (right-click the extension icon →
Options, or the gear in the launcher) → **Google Client ID**. Paste the same value as
`web/.env` → `VITE_GOOGLE_CLIENT_ID`.

It is stored in `chrome.storage.local`, not in a tracked file — `web/.env` is gitignored, so
hardcoding the ID in `extension/config.js` would commit a value this repo keeps untracked. Until it
is set, sign-in reports a setup error pointing back here instead of launching a doomed auth flow.

> **Why the same client ID?** `backend/app/api/auth.py:160` verifies the ID token against exactly one
> audience (`settings.GOOGLE_CLIENT_ID`). A separate extension client would mint tokens with a
> different `aud` and be rejected with 401. Reusing the web client keeps the backend untouched.

Confirm the backend has `GOOGLE_CLIENT_ID` set in `backend/.env`; without it `/api/auth/google`
returns **501** and sign-in cannot work.

## 5. Drive it

### Open the workspace
1. Click the toolbar icon → the launcher popup appears
2. Click **Open panel** → the side panel docks on the right
3. Drag its inner edge → the layout reflows without horizontal scrolling

### Sign in
4. Click **Sign in with Google** → a Google account chooser opens
5. After consent, the panel shows **Signed in as \<your email\>**

### Persistence check (the whole point of the feature)
6. With the panel open, click around the page, scroll, then navigate to a different URL
7. The panel stays open and the form retains its values

### Capture, generate, push
8. Visit a prospect's page; optionally select a sentence describing a signal
9. Click **Grab from this page**. The first time you use it on a given site, Chrome prompts to let
   the extension read that site — accept it. The grant is **per-origin** and remembered, so you are
   asked once per site, not once per capture. Then company / signal / source prefill, all editable.

   (Why the prompt: Chrome grants `activeTab` only when you invoke the extension from the toolbar
   icon, a context menu, or a keyboard shortcut — never from a button inside the side panel. So the
   extension asks for that one origin on demand rather than requesting all sites up front.)
10. Fill contact and role, choose a provider, click **Generate with AI**
11. Confirm the preview shows the snapshot, the opener, and **three** follow-ups with rationale
12. Click **Push to CRM** → success reports the contact and deal ids

### Console check
13. Right-click the panel → **Inspect** → Console
14. Expect **no CORS errors** and no unhandled rejections. Also inspect the service worker from
    `chrome://extensions` and confirm no token values are logged.

## 6. Verify nothing else regressed

```bash
cd backend && pytest tests/          # must stay green
cd web && npm run build              # must stay green
```

Neither is touched by this feature — they are the guard that it stayed inside `extension/`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **Open panel** button missing | Chrome < 116 | upgrade; the popup says so explicitly |
| `redirect_uri_mismatch` on sign-in | URI not registered, or extension ID changed | re-check step 2 and 4 |
| Sign-in returns 501 | `GOOGLE_CLIENT_ID` unset on the backend | set it in `backend/.env`, restart |
| Sign-in returns 401 `Invalid Google ID token` | `aud` mismatch — wrong client ID in `config.js` | use the web app's client ID |
| Generate returns 401 | not signed in; the DEBUG stub fallback no longer exists | sign in |
| **Grab from this page** fails | `chrome://`, Web Store, or PDF page | expected; try a normal page |
| Capture says permission was declined | the per-site Chrome prompt was dismissed | click it again and accept, or revoke/re-grant under `chrome://extensions` → Details → Site access |
| Panel is blank after edits | stale panel | close and reopen; reload the extension card |

## Do not

- **Do not hand-edit `"version"` in `extension/manifest.json`.** It is generated from the root
  `VERSION` file by `scripts/sync_versions.py`; use `make bump-patch` / `make bump-minor`.
- Do not add a bundler, transpiler, or `package.json` under `extension/` — it loads unpacked as-is.
- Do not commit `extension-key.pem`.
