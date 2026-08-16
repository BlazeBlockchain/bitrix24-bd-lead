# Deploying BD Lead AI

This describes the **team demo** deployment: a staging instance at
`https://bb.bbross.net/bd-lead-staging/`, joining the shared infrastructure that
`vanguard-game` already uses rather than standing up anything new.

> **This is a demo, not a production launch.** It is deliberately not hardened, not
> monitored, and not backed up. See [Not production](#not-production) for the specific
> things that must change before anyone points real customer data at it.

## Infrastructure it joins

| Piece | Value |
|---|---|
| Server | `digaut@vmi1325117` — Ubuntu 22.04 + Docker |
| Docker network | `bbspace_net` — **external**, created once, shared between projects |
| Reverse proxy | `~/docker/b8-shared` nginx stack, conf `data/nginx/bb.bbross.net.conf` |
| SSL | `b8labs.net` SAN cert covering the b8/bbross domains, Cloudflare DNS-01 |
| Repo on server | `~/docker/bitrix24-bd-lead-staging` |
| Compose project | `bdlead-staging` |
| URL | `https://bb.bbross.net/bd-lead-staging/` |

`DEPLOY_HOST` is the bare hostname `vmi1325117`, matching vanguard-game's Makefile. It
resolves only on machines with an ssh config entry or `/etc/hosts` line for it. `ssh:
Could not resolve hostname` means that entry is missing locally — it does not mean the
server is down.

## Why the path prefix works

`docker-compose.staging.yml` builds the web image with `VITE_BASE=/bd-lead-staging/`.
That single value drives two things:

1. Vite emits asset URLs under `/bd-lead-staging/`.
2. `web/src/api/client.ts` derives `API_BASE` from `import.meta.env.BASE_URL`, so the
   browser calls `/bd-lead-staging/api/…` rather than `/api/…`.
3. `App.tsx` passes the same `BASE_URL` to `<BrowserRouter basename=…>`. Without it
   every route falls through to the catch-all and the whole app renders "Page not
   found" behind a working nav bar — sign-in included, since `/login` 404s the same
   way. Note this failure is invisible to `curl`: nginx correctly returns 200 with
   `index.html` for any deep URL, and the router rejects the path afterwards, in the
   browser. **Only a rendered check catches it.**

Both then arrive at the shared proxy under the same prefix, the proxy strips it, and the
container sees `/` and `/api/` — which its own `web/nginx.conf` already handles. The
prefix must therefore agree in three places: `VITE_BASE`, the proxy `location`, and the
proxy's `rewrite`. If they disagree the SPA loads but 404s on a hard refresh of a deep
route, or every API call 404s.

### nginx location block

Add to `~/docker/b8-shared/data/nginx/bb.bbross.net.conf`, alongside the existing
`/vanguard/` block, then `docker compose exec <nginx-container> nginx -s reload`:

```nginx
location /bd-lead-staging/ {
    rewrite ^/bd-lead-staging/(.*)$ /$1 break;
    proxy_pass http://bdlead-staging-web:80;

    proxy_http_version 1.1;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # An enrichment takes ~22s mean, ~25s max, and runs as ONE request. The default
    # 60s is fine; anything at or below ~30s will cut real enrichments off mid-flight.
    proxy_connect_timeout 60s;
    proxy_send_timeout    60s;
    proxy_read_timeout    60s;
}
```

`bdlead-staging-web` is the `container_name` from `docker-compose.staging.yml`. The proxy
resolves it over `bbspace_net`, so both stacks must be attached to that network.

## How the deploy moves code

The deploy **pushes** a committed branch to a git repo on the server and rebuilds
there. It does not pull from GitHub, because the VPS has no credentials for this repo
and creating a deploy key needs GitHub admin rights that were not available.

Pushing preserves the property that mattered when rsync was dropped — the server runs
a **commit**, never the operator's uncommitted working tree — while putting no
credential on a shared host at all.

The server repo sets `receive.denyCurrentBranch=updateInstead`, so pushing to the
checked-out branch updates its working tree in place. That refuses the push if the
server tree is dirty, which is the behaviour you want: nothing should be editing files
there, and if something is, the deploy should stop rather than clobber it.

`STAGING_PATH` / `DEPLOY_PATH` must stay **absolute** — they are interpolated into
`ssh://` URLs, and `~` in an `ssh://` URL is sent as a literal path component rather
than expanded.

## First deploy

Nothing below is created by `make deploy-staging` — it only pushes and rebuilds.

```bash
# 1. On the server: create the push target
mkdir -p /home/digaut/docker/bitrix24-bd-lead-staging
cd /home/digaut/docker/bitrix24-bd-lead-staging
git init
git config receive.denyCurrentBranch updateInstead

# 2. From your machine: push the branch, then check it out on the server.
#    The checkout is needed ONCE — the first push lands on an unborn HEAD and so
#    creates the ref without updating the working tree.
git push ssh://digaut@95.111.225.43/home/digaut/docker/bitrix24-bd-lead-staging ai-bd-assistant
ssh digaut@95.111.225.43 "cd /home/digaut/docker/bitrix24-bd-lead-staging && git checkout ai-bd-assistant"

# 3. On the server: create .env.staging and fill it in. It is gitignored and is
#    NEVER transferred by any deploy target, so it must exist before the first up.
cp .env.staging.example .env.staging && chmod 600 .env.staging
$EDITOR .env.staging          # see the checklist below

# 4. Confirm the shared network exists (it should already)
docker network inspect bbspace_net >/dev/null || docker network create bbspace_net

# 5. Bring it up
docker compose --env-file .env.staging \
  -f docker-compose.yml -f docker-compose.staging.yml -p bdlead-staging \
  up --build -d --remove-orphans
```

Then add the nginx block above and reload the proxy.

Subsequent deploys are just `make deploy-staging`.

### Host ports must be free

The staging stack publishes its ports on `127.0.0.1` only, but they must still be
unused on the host or the deploy fails outright on a collision — a shared server is
already running other projects. `BACKEND_PORT` and `WEB_PORT` in `.env.staging` exist
for this; staging currently uses **8010** and **8090** because 8000 and 8080 were
taken.

The bindings cannot simply be removed for a deployment: dropping an inherited `ports`
entry needs compose v2.24's `!override`, and the server runs **v2.18.1**. Moving the
binding is what that version can express. Nothing is exposed either way — the demo is
served through the shared nginx stack over `bbspace_net`, and these ports exist only
for curling the services from the host shell.

### `--env-file` is not optional

`env_file:` in the compose override injects variables into a **running container**. It
does **not** feed `${VAR}` interpolation in `docker-compose.yml` — and the web image's
`VITE_GOOGLE_CLIENT_ID` is a **build arg** filled by interpolation. Without
`--env-file .env.staging`, that arg builds empty, the bundle ships with no client ID, and
the Google sign-in button does nothing with no error. `make deploy-staging` passes it.

### `.env.staging` checklist

| Variable | Consequence of getting it wrong |
|---|---|
| `GOOGLE_CLIENT_ID` | Empty → sign-in button dead (see above). Also needs the origin registered in Google Cloud Console. |
| `AUTH_EMAIL_ALLOWLIST` | **Empty → any Google account on the internet can sign in.** Set it. |
| `GEMINI_API_KEY` | Empty → every brief silently falls back to the deterministic mock, and a mock brief carries **no citation at all**. "No source links on any lead" is the symptom of a missing key. |
| `JWT_SECRET` | Left at the dev default → anyone can forge a token for this instance. |
| `ENCRYPTION_KEK` | Empty → falls back to a hardcoded dev key in `token_vault`. Survivable only while no real CRM tokens are stored. |
| `POSTGRES_PASSWORD` | Must match the one embedded in `DATABASE_URL` in the same file. |
| `CORS_ORIGINS` | Needed **only by the extension**, which calls the API from `chrome-extension://<id>` — a cross origin. An unset value is not permissive: `main.py` falls back to `["http://localhost:5173"]`, so every extension request is blocked by the browser before it reaches the backend. The web app is same-origin behind nginx and needs nothing here. |
| `BACKEND_PORT` / `WEB_PORT` | Must be free on the host, or the deploy fails on a port collision. |

`ANTHROPIC_API_KEY` is empty in practice, so the real fallback chain is **Gemini → mock**,
with no Haiku step. Both providers log why they were skipped — read the logs rather than
guessing.

## Google OAuth

Register in Google Cloud Console **before** first sign-in:

- Authorised JavaScript origin: `https://bb.bbross.net`
- Authorised redirect URI: as required by the flow in use

`VITE_GOOGLE_CLIENT_ID` is baked in at **image build** time. Changing the client ID means
`up --build`, never `restart`.

**Do not touch `extension/manifest.json`'s `key`.** It pins the extension ID
`kopmahhdddlcipdggmgldkofjpneeboa`, which the extension's own OAuth redirect URI depends
on. Changing it breaks extension sign-in.

### Isolating "OAuth is misconfigured" from "the app is broken"

Mint a token with the app's own helper and inject it, without touching Google:

```bash
cd backend && python -c "import sys;sys.path.insert(0,'.')
from app.api.auth import create_access_token
print(create_access_token('00000000-0000-0000-0000-000000000042','demo@x.net','Demo'))"
```

The store needs **both** localStorage keys or it stays on the sign-in screen:

```
bd_lead_jwt   = <token>
bd_lead_user  = {"id":"…","email":"…","display_name":"…"}
```

The token must be signed with the **deployed** `JWT_SECRET` to be accepted there. Use this
to prove the app works, then fix OAuth separately. **Do not demo on a minted token.**

## Outbound network requirements

Feature 010 made the backend call out to hosts it never used to. The container needs
**general outbound HTTPS egress**, not an allowlist of two Google domains:

| Host | Purpose |
|---|---|
| `generativelanguage.googleapis.com` | the grounded search call and the enrichment |
| `vertexaisearch.cloud.google.com` | resolving the grounding redirect |
| **arbitrary publisher domains** | the liveness probe `HEAD`s whatever the redirect resolves to |

If egress is restricted, **citations silently vanish** and briefs degrade to the 009
presentation with no error shown to the user. Verify from **inside** the container, not
from the host shell:

```bash
docker compose -p bdlead-staging exec bdlead-backend \
  python -c "import httpx; print(httpx.head('https://example.com', follow_redirects=True).status_code)"
```

`RETRIEVAL_ENABLED=false` is the one-flag kill switch if grounded search misbehaves
mid-demo. Briefs then degrade to 009 output — never to an error.

**Cost:** grounding is free under 1,500 requests/day, then $35/1,000 = 3.5 cents per
enrichment, roughly 4× the ~0.91 cents the enrichment itself costs. A team demo will not
approach the free tier.

## Database

`backend/entrypoint.sh` runs `alembic upgrade head` before starting uvicorn, so migrations
apply automatically on every container start. No separate step, and no empty-schema 500s
on first request.

The staging override uses its own `bdlead_db_staging_data` volume, isolated from any
prod volume.

## Verifying a deploy

Do all of these. The enrichment one is load-bearing, not a formality.

1. **Health from outside the VPS, over HTTPS, on the real URL:**
   `curl -i https://bb.bbross.net/bd-lead-staging/api/health`
2. **Sign in with Google in a fresh incognito window.** An already-authenticated browser
   hides exactly the failure you are looking for.
3. **Run one real enrichment through the deployed web UI.** Confirm the brief shows the
   buying signal, contact confidence pill, outreach email, CRM entry preview, and the 010
   payoff: one or more clickable source links, a "Search found:" line, and the Google
   Search Suggestions chips.
4. **Run the same lead in the side panel and compare field by field.** See below.
5. **Open a cited link** and confirm the page actually supports the claim.
6. **Run a lead that must produce no citation** — company `Notion`, signal `announced it
   is shutting down and filing for bankruptcy`. Correct behaviour is a summary with no
   link and **no error**.
7. **Check the logs for `RETRIEVAL:` lines** — `found`/`empty`/`timeout`/`error`. This is
   the fastest way to tell "found nothing" (correct) from "cannot reach the network"
   (broken egress).
8. **Hard-refresh a deep route** (e.g. `/bd-lead-staging/history`). This is where
   `VITE_BASE` mistakes surface.

### The two surfaces are separate render paths

The web app and the extension side panel render the brief through **completely separate
code**. They have diverged before and it failed silently: until commit `77dac07` the web
app awaited `/api/leads/enrich`, **discarded the response**, and rendered a form-derived
stub captioned "Preview generated via LLM enrichment", while the side panel rendered the
real brief correctly the whole time. Every 009 and 010 section was unreachable on web for
months and nothing errored.

**Checking one surface tells you nothing about the other.** Always run the same lead
through both and compare field by field.

## The extension against a deployed backend

Two separate things gate this, and fixing only one leaves the extension silently
unable to call the API.

**1. Host permission — committed.** MV3 blocks any request to a host absent from
`manifest.json`'s `host_permissions`, before CORS is ever consulted, so
`https://bb.bbross.net/*` is listed there permanently. It sits alongside the localhost
entry rather than replacing it, so local development is unaffected. Nothing needs doing
here.

**2. API base — a local, uncommitted edit.** `extension/config.js` hardcodes
`API_BASE = http://localhost:8000/api` and `WEB_BASE = http://localhost:8080`, and the
file **is tracked by git**, so committing a VPS value would repoint every developer's
local extension:

```js
const API_BASE = 'https://bb.bbross.net/bd-lead-staging/api';
const WEB_BASE = 'https://bb.bbross.net/bd-lead-staging';
```

Do not commit that. `git checkout extension/config.js` restores local development.

The asymmetry is deliberate: a host permission is additive and inert until something
actually calls that host, whereas `API_BASE` is a single value that must be either one
environment or the other. If the extension ever needs to target both routinely it needs
a real configuration mechanism (the options page + `chrome.storage.local` pattern
already used for `bd_google_client_id`) — a code change and a separate piece of work.

**3. `CORS_ORIGINS` on the server** must include `chrome-extension://<id>`, which is
already set on staging. See the `.env.staging` checklist above for why an unset value
is not permissive.

The extension is buildless MV3, loaded unpacked. Reloading rules: manifest changes need a
reload on the `chrome://extensions` card; panel/popup/options changes need the surface
**closed and reopened**, not just reloaded.

## Operational gotchas

- **`docker compose restart` does NOT pick up code changes.** `backend/` and `web/` are
  baked into their images with no bind mount. Use `up -d --build <service>`.
- **After rebuilding `bdlead-web`, nginx may 502 for a few seconds** until it re-resolves
  the backend. Wait and retry before debugging.
- **Enrichment takes ~22s with no progress indicator.** Warn whoever is demoing or they
  will assume it hung and click twice.
- **Web JWTs last 60 minutes.** A demo left open over lunch logs people out. If screens
  look empty, check the session first.
- **`bbspace_net` is external** — it must already exist or compose fails outright.
- The repo root and `backend/` have different pyenv versions. `cd backend` first; a bare
  `python` at the root fails with "command not found", and a failed `cd` in a compound
  command silently runs the rest in the wrong directory.
- `google.generativeai` is deprecated and cannot express the `google_search` tool.
  Retrieval deliberately uses REST via httpx. Do not "upgrade" it.

## Not production

This is the list that must be closed before this instance stops being a demo:

- **No rate limiting, monitoring, alerting, or backups.** The DB volume is not backed up.
- **`DEBUG: "true"`** is hardcoded in `docker-compose.yml`'s backend environment and is
  not overridden by the staging file.
- **`ENCRYPTION_KEK`** must be a real secret before any real CRM token is stored.
- **The allowlist is the only access control.** There is no role model, no audit log, and
  no per-user quota beyond `LLM_DAILY_BUDGET_CENTS`.
- **No CI/CD.** Deploys are manual `make deploy-staging`, and nothing verifies the gates
  ran first.
- **`usage_ledger.estimated_cost_cents` is an INTEGER**, so a sub-cent enrichment rounds
  to 0 in the row. Token counts are exact, so spend stays recomputable — but do not read
  the cost column as authoritative.

## Compliance note for anyone demoing this

`retrieval_service._resolve_publisher_url` resolves Google's grounding redirect to the
real publisher URL. This **knowingly deviates** from the Gemini API terms ("you will not
modify … the Grounded Results") and is **pending legal sign-off** — see `CLAUDE.md` and
`specs/010-verifiable-signal-source/plan.md`.

**Present the citation feature as pending review, not as shipped.** Do not change the
behaviour in either direction without asking the repo owner.
