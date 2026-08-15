# Phase 0 Research: Design System Pass

**Feature**: `specs/008-design-system-pass` · **Date**: 2026-08-15

Five unknowns blocked planning. Four are resolved empirically below; one is resolved by
documentation and carries a mandatory in-browser confirmation task.

---

## R1. How do we rasterize icon artwork with no build step and no image tooling?

**Decision**: Render SVG source through **headless Chrome's `--screenshot` CLI flag** from a
dev-time script in `scripts/`. Commit the resulting PNGs. The extension directory receives
finished binary assets, never a build.

**Verified, not assumed.** Probed the toolchain:

| Tool | Status |
|---|---|
| `rsvg-convert`, `inkscape`, `convert`, `magick` | all MISSING |
| `cairosvg`, `Pillow` | not importable |
| `sharp`, `puppeteer`, `playwright` npm packages | not installed |
| Chrome binary | **present** in `~/.cache/puppeteer/chrome/linux-151.0.7922.77/` (also two Playwright chromiums) |
| npm registry | reachable (HTTP 200) |

Then proved the approach end to end: rendered a gradient rounded-square bolt at 128×128 with

```
chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
       --default-background-color=00000000 --force-device-scale-factor=1 \
       --screenshot=out.png --window-size=128,128 shot.html
```

Result: a valid **128×128 PNG at 6330 bytes** that renders the mark correctly with a clean
gradient and antialiased edges — against the 428-byte near-blank file it replaces. Transparency
is preserved via `--default-background-color=00000000`; `--force-device-scale-factor=1` is
required or the output comes back at DPR-scaled dimensions.

**Rationale**: zero new dependencies, uses a binary already on the machine, and produces genuinely
antialiased output with real gradient support. The alternative of hand-writing PNG bytes in Python
via `zlib` can produce a valid file but not quality antialiasing on a diagonal glyph.

**Alternatives considered**: installing `sharp` or `cairosvg` (adds a dependency to a project that
deliberately has none in `extension/`); committing only SVG (Chrome extension icons require
raster — `manifest.icons` does not accept SVG); hand-rolled PNG encoder (poor edge quality).

**Caveat**: `dbus` connection errors appear on stderr under WSL. They are noise, not failures — the
file is written correctly. The script must not treat a non-empty stderr as an error.

---

## R2. What does Chrome already render in its own side-panel header?

**Decision**: Chrome's side panel supplies its **own header chrome, including a close control at the
top-right**, alongside a panel-switcher combobox. Therefore the in-panel close control **MUST NOT be
an X in the panel's own top-right corner** — that is precisely where Chrome's own X sits, and it
would produce the two competing affordances FR-005 forbids.

**Placement**: a labelled action in the **panel footer**, spatially separated from Chrome's chrome,
reading as an explicit "Close panel" action rather than a second window-dismiss X. Implemented with
`window.close()`, which is valid from an extension page.

**Confidence and follow-up**: when written, this was resolved from Chrome's documented side-panel UI
and **not** from an empirical check — headless Chrome renders extension pages but not the
browser-level side-panel chrome around them, so it could not be screenshot-verified in the harness.
It therefore carried a mandatory manual task.

**RESOLVED 2026-08-15**: confirmed by the requester in real Chrome — the footer close action reads
correctly alongside Chrome's own header controls, with no competing affordance. The decision stands
as made; no rework needed.

**Alternatives considered**: top-right X (rejected — collides with Chrome's own); no close control
at all (rejected — the user explicitly asked for one); a keyboard-only binding (rejected —
undiscoverable as the sole affordance).

---

## R3. How do two token files stay in sync with no build step?

**Decision**: A single tracked upstream, `design/tokens.css`, holding the token block. A dev-time
script `scripts/sync_design_tokens.py` injects that block between marker comments in both
`web/src/index.css` and `extension/tokens.css`. The script offers `--check`, which exits non-zero on
drift, and is wired into the test gate.

**Rationale**: marker-based injection preserves each consumer's own rules while making the token
region generated. It mirrors the convention this repo already uses for `version` via
`scripts/sync_versions.py` — one source, generated consumers, a check mode — so it needs no new
concepts. Committed CSS means `extension/` still loads unpacked with no build.

The handoff's `styles.css` is the *design* source of truth. It was untracked when this was written
(and has since been moved into `docs/design/` and committed), but it stays a design deliverable
rather than a build input; `design/tokens.css` is its committed transcription.

**Alternatives considered**: a shared CSS file referenced by both (impossible — an extension page
cannot `@import` across the web app's source tree); CSS-in-JS or a bundler for the extension
(violates NFR-001); manual discipline (this is the status quo that produced the drift).

---

## R4. How do Inter and JetBrains Mono resolve without a network fetch?

**Decision**: **Self-host** both as variable `woff2` files — `extension/fonts/` for the extension
pages, `web/public/fonts/` for the web app — declared via `@font-face` with a system-stack fallback
in the `font-family` chain.

**Rationale**: NFR-006 requires local resolution. Beyond that, a font CDN on an extension page is a
privacy leak (every panel open pings a third party), breaks offline use, and draws Chrome Web Store
review scrutiny. Variable woff2 keeps both families small enough to commit. Fonts are static files,
so this does not introduce a build step.

**Fallback**: if the font files cannot be obtained, the `font-family` chain degrades to
`system-ui`/`ui-monospace` and the design still holds its structure. This is a stated fallback, not a
silent one — NFR-006 requires the fallback path to work.

**Alternatives considered**: Google Fonts `<link>` (rejected per above); system stack only (rejected
— the handoff's typography is explicitly part of the design, and Inter's metrics differ enough from
the default UI stack to change the layout).

---

## R5. How is the verification harness driven?

**Decision**: `puppeteer-core` installed **in the scratchpad, not in the repo**, pointed at the
already-cached Chrome binary via `executablePath`. Launch with `--load-extension` plus
`--disable-extensions-except`, then open `chrome-extension://<id>/{sidepanel,popup,options}.html`.

**Why `puppeteer-core` and why scratchpad**: `puppeteer` proper would download a second Chrome
copy; `puppeteer-core` reuses the cached one. Keeping it out of the repo avoids adding a devDependency
for a one-off verification, and `extension/` must stay free of `node_modules` entirely.

**Assertions the harness must make** (mapping to SC-005, SC-006):
- zero entries in the console-error log per page
- `document.documentElement.scrollWidth <= clientWidth` at narrow widths (no horizontal overflow)
- every text-bearing element's computed `font-size` parses to `>= 12`
- each icon path returns a resource whose natural dimensions are non-zero
- the panel is exercised at multiple widths, since it is user-resizable

The extension ID is fixed at `kopmahhdddlcipdggmgldkofjpneeboa` by the manifest `key`, so the URLs
are stable and can be hard-coded in the harness.

**Known limitation**: headless Chrome cannot open the real side-panel surface or its browser chrome.
The harness validates the *page*; the panel *as a panel* still needs the manual pass from R2.

---

## Resolved constraints carried into the plan

- Icon PNGs are **generated artifacts committed to the repo**, produced by a script that a human runs
  — not produced at extension load time. `extension/` stays buildless (NFR-001).
- `extension/manifest.json` gains `action.default_icon`; `version` and `key` are untouched
  (NFR-007, NFR-008).
- The 12px floor overrides the handoff's ~11px chips (NFR-004), and `body` on every extension page
  keeps an explicit `font-size` rather than inheriting.
- No new permissions (NFR-009) — nothing in this feature needs one.
- Motion uses transform-only entrance animation and never gates visibility on opacity (NFR-011),
  matching the handoff's own stated rationale, plus a `prefers-reduced-motion` guard.
