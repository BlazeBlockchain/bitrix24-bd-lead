# Quickstart: Design System Pass

How to work on and verify this feature. Commands run from the repo root unless stated.

## Editing a design token

Never edit `web/src/index.css` or `extension/tokens.css` token blocks directly — they are generated.

```bash
$EDITOR design/tokens.css     # the only place a token value changes
make sync-tokens              # rewrite both consumers
make check-tokens             # must exit 0
```

`make check-tokens` also fails if any retired legacy color (`#f97316`, `#0d1117`, …) reappears.

## Regenerating the icons

```bash
$EDITOR design/mark.svg
make build-icons              # → extension/icons/{16,48,128}.png
```

Under the hood this drives the already-cached Chrome binary; no npm, no ImageMagick:

```
~/.cache/puppeteer/chrome/linux-151.0.7922.77/chrome-linux64/chrome \
  --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --default-background-color=00000000 --force-device-scale-factor=1 \
  --screenshot=out.png --window-size=N,N shot.html
```

Notes that cost time if forgotten:
- `--force-device-scale-factor=1` is **required** or output comes back DPR-scaled.
- `--default-background-color=00000000` preserves transparency outside the rounded square.
- `dbus` errors on stderr under WSL are harmless noise — check the file, not the exit chatter.
- Sanity check: a real 128px mark is multiple kilobytes. If it is ~400 bytes, it is blank again.

## Reloading the extension

```bash
# chrome://extensions → BD Lead AI card → reload
```

- **manifest.json changes**: always require a reload.
- **sidepanel/popup/options changes**: require the surface to be **closed and reopened**, not just
  reloaded.
- Do **not** hand-edit `manifest.json`'s `version` — use `make bump-patch`. Do not touch `key`.

## Rebuilding the web app

`docker compose restart` does **not** pick up code changes — `backend/` and `web/` are baked into
their images with no bind mount:

```bash
docker compose up -d --build web       # or: backend
```

Stack runs at backend `:8000`, web `:8080`, plus postgres. `extension/config.js` points `WEB_BASE`
at `http://localhost:8080`.

If screens look empty, **check the session first** — web JWTs last 60 minutes. An expired token now
logs you out rather than rendering as empty data, but an expired session is still the likeliest
cause of an unexpectedly bare screen.

## Verification harness

Install `puppeteer-core` in the scratchpad — **not** in the repo, and never in `extension/`:

```bash
cd "$SCRATCH" && npm i puppeteer-core
```

Point `executablePath` at the cached Chrome, launch with:

```
--load-extension=<repo>/extension
--disable-extensions-except=<repo>/extension
```

then open each of:

```
chrome-extension://kopmahhdddlcipdggmgldkofjpneeboa/sidepanel.html
chrome-extension://kopmahhdddlcipdggmgldkofjpneeboa/popup.html
chrome-extension://kopmahhdddlcipdggmgldkofjpneeboa/options.html
```

and assert, per [contracts/surfaces.md](./contracts/surfaces.md): empty console-error log, no
horizontal overflow, no computed `font-size` under 12, tokens resolve, icons load with non-zero
natural dimensions. Run the side panel at **several widths** — it is user-resizable and default-width
success proves nothing about the narrow case.

## The manual pass is not optional

Headless Chrome renders extension *pages* but not the browser's side-panel *chrome*. The harness
therefore cannot see whether the in-panel close control collides with Chrome's own header X. Before
sign-off:

1. Load unpacked in a real Chrome (116+).
2. Open the side panel and **look at what Chrome renders in its header**.
3. Confirm the in-panel close action reads as a distinct, deliberate control — not a second X in the
   same corner. Footer placement is the planned answer.

## Gates

```bash
cd backend && pytest tests/     # 77 passed
cd web && npm run build
make check-tokens
```

All three must be green. The web build is a real gate for this feature — unlike 007, this one
modifies `web/`.
