# Implementation Plan: Design System Pass — Web App + Extension Surfaces

**Feature Branch**: `ai-bd-assistant` · **Spec**: [spec.md](./spec.md) · **Date**: 2026-08-15

## Summary

Apply the `docs/design/` visual language to all four shipped surfaces, replacing the
legacy orange-on-GitHub-dark palette with the handoff's iris→violet→cyan gradient on near-black
navy. Establish one tracked token upstream with a drift check so the web and extension token files
can no longer diverge silently. Give the side panel a footer-placed close action that does not
collide with Chrome's own header X. Ship real logo artwork at 16/48/128 plus a web favicon, and
declare `action.default_icon` so the toolbar and panel header resolve it.

Three of these are cosmetic in effect but structural in cause: the tokens were duplicated by hand
with no upstream, the icons were never authored, and the manifest never pointed at them.

## Technical Context

| Aspect | Value |
|---|---|
| Web app | React 18 + TypeScript + Vite, `web/`, 9 components |
| Extension | MV3, vanilla JS/HTML/CSS, no build, classic scripts, `extension/` |
| Design source | `docs/design/` (tracked) — `styles.css` tokens, `README.md` spec |
| Token upstream (new) | `design/tokens.css`, synced by `scripts/sync_design_tokens.py` |
| Icon pipeline (new) | SVG source → headless Chrome `--screenshot` → committed PNGs |
| Fonts | Inter + JetBrains Mono, self-hosted variable woff2 |
| Verification | `puppeteer-core` in scratchpad against cached Chrome, + manual real-Chrome pass |
| Gates | `cd backend && pytest tests/` (77 passed), `cd web && npm run build` |

No NEEDS CLARIFICATION remain — all five unknowns were resolved in [research.md](./research.md), and
the four scope questions were answered by the requester before the spec was written.

## Architecture

### Token flow

```
docs/design/styles.css      (design source of truth, tracked)
                │  transcribed once, by hand, deliberately
                ▼
        design/tokens.css           (tracked upstream — the only place a token is edited)
                │
                │  scripts/sync_design_tokens.py   (inject between markers; --check fails on drift)
        ┌───────┴───────┐
        ▼               ▼
web/src/index.css   extension/tokens.css
        │                   │
        ▼                   ▼
   React app        sidepanel · popup · options
```

The upstream is a plain `:root { … }` block. The sync script rewrites only the region between
`/* >>> generated: design tokens */` and `/* <<< end generated */` in each consumer, leaving every
other rule in those files untouched. `--check` is what the gate runs; the write mode is what a
developer runs after editing the upstream.

**Why a transcription step**: the bundle is a design deliverable — prose plus prototypes — not a
machine-readable input. A separate committed upstream means the sync script parses one small file
with a known shape, and the drift check never depends on the prototype bundle's structure.

### Surface mapping

| Handoff design | Ships as | Treatment |
|---|---|---|
| In-page injected panel / rich popup | `sidepanel.html` | full brief presentation, tighter density |
| — | `popup.html` | stays a thin 320px launcher, restyled only |
| — | `options.html` | restyled to match |
| Web app shell + hero flow | `web/src/**` | restyled in place, sidebar shell replaces header nav |
| Onboarding, Billing | *not built* | out of scope |

### The data gap

The frozen contract returns `company_snapshot`, `personalized_opener`, and
`follow_ups[3]{title, description, due_in_days, rationale}`. The handoff's brief additionally depicts
a buying signal with source and date, a HIGH/MED/LOW confidence pill, a full outreach email with To
and Subject, a CRM field-mapping grid, a source count, and 5-step research progress.

Per the requester's decision, those sections render **in the designed visual language but visibly
inert** — present, styled, and explicitly labelled unavailable. No fabricated values, no derived
stand-ins, no confidence pill computed from nothing. This preserves `docs/UI_UX.md`'s "AI is visible
and trustworthy" principle while showing the full design intent.

Inert sections are marked up with a dedicated state class and an accessible label, so they read as
"not yet" rather than as a rendering failure.

## File plan

**New**

| Path | Purpose |
|---|---|
| `design/tokens.css` | tracked token upstream |
| `design/mark.svg` | logo mark vector source (bolt in gradient rounded square) |
| `scripts/sync_design_tokens.py` | inject tokens into both consumers; `--check` mode |
| `scripts/build_icons.py` | rasterize `design/mark.svg` → 16/48/128 PNG via headless Chrome |
| `extension/fonts/*.woff2` | self-hosted Inter + JetBrains Mono |
| `web/public/fonts/*.woff2` | same, for the web app |

**Modified**

| Path | Change |
|---|---|
| `web/src/index.css` | generated token region + restyled base/layout, sidebar shell |
| `web/src/App.css`, `web/src/components/*.tsx` | restyle in place; sidebar nav replaces header |
| `web/index.html`, `web/public/favicon.svg` | favicon swap to the real mark |
| `extension/tokens.css` | generated token region + component classes in new language |
| `extension/sidepanel.html` / `.js` | rich brief layout, inert sections, footer close action |
| `extension/popup.html` / `.js` | restyle only |
| `extension/options.html` / `.js` | restyle only |
| `extension/icons/{16,48,128}.png` | replaced with real artwork |
| `extension/manifest.json` | add `action.default_icon` — **only** that key |
| `Makefile` | add `sync-tokens`, `check-tokens`, `build-icons` targets |

**Untouched by contract**: `backend/**`, `extension/{auth,lead-api,capture,config,background}.js`
except where they set class names, `manifest.json`'s `version` and `key`.

## Constitution Check

No `.specify/memory/constitution.md` exists (the speckit install here is minimal — only
`feature.json`, no scripts, templates, or memory). The gates below are the repo's standing
conventions, taken from the spec's NFRs and from `Makefile`/`CHANGELOG` practice, consistent with
how `specs/007` framed the same table.

| Gate | Status | Evidence |
|---|---|---|
| Buildless extension preserved | PASS | icons and tokens are *committed artifacts*; generator scripts live in `scripts/`, run by a human, never at load time. No bundler, no `node_modules` in `extension/` |
| API contracts unchanged | PASS | no request/response shape touched; this feature reads the same preview object |
| Preview shape unchanged | PASS | `company_snapshot`, `personalized_opener`, `follow_ups[3]` consumed as-is; missing fields render inert rather than prompting a contract change |
| No XSS surface | PASS | `sidepanel.js` keeps `createElement`/`textContent`; restyling changes class names, never the construction method |
| Least privilege | PASS | zero new permissions (NFR-009) |
| Version not hand-edited | PASS | `manifest.json` `version` untouched; use `make bump-patch` |
| Extension ID stable | PASS | `key` untouched — OAuth redirect URI depends on it |
| 12px floor | PASS by design | explicit `body` font-size on every extension page; handoff's 11px chips rescaled up; asserted by harness |
| Backend tests / web build green | VERIFY | backend untouched so `pytest` should be unaffected; `web/` changes make `npm run build` a real gate, run at the end of each phase |

**Post-design re-evaluation**: unchanged. The design adds no backend dependency and no runtime
dependency of any kind. The two new scripts are dev-time only. The one gate that moves from "PASS by
construction" to "VERIFY" is the web build, because unlike 007 this feature does modify `web/`.

## Risks

| Risk | Mitigation |
|---|---|
| ~~`docs/design/` is untracked — one `git clean` from gone~~ | RESOLVED: bundle moved to `docs/design/` and committed; tokens also transcribed into `design/tokens.css` |
| ~~Chrome's panel header differs from documentation → close button collides~~ | RESOLVED 2026-08-15: confirmed in real Chrome, footer placement reads correctly, no collision |
| Restyling 9 React components regresses behavior | Restyle only — no logic edits; `npm run build` after each component group; visual pass in real browser |
| Glass surfaces (`rgba` on near-black) lose contrast at small sizes | Verify text contrast against the *composited* background, not the token alpha |
| Self-hosted fonts unobtainable | Documented fallback to system stack (R4); design structure holds either way |
| Panel horizontal overflow at narrow widths with the richer layout | Harness asserts `scrollWidth <= clientWidth` at several widths, not just the default |
| ~~Headless harness cannot see the real panel chrome~~ | RESOLVED 2026-08-15: manual unpacked-Chrome pass completed by the requester |

## Phases

- **Phase 0** — research → [research.md](./research.md) (complete)
- **Phase 1** — design → [data-model.md](./data-model.md), [contracts/](./contracts/),
  [quickstart.md](./quickstart.md) (complete)
- **Phase 2** — tasks → `tasks.md` via `/speckit-tasks`
- **Phase 3** — implement, sequenced by file overlap: tokens upstream → icons → extension surfaces →
  web surfaces → harness → manual pass

## Tasks

See `tasks.md` (generated by `/speckit-tasks`).
