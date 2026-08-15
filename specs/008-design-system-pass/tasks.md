# Tasks: Design System Pass — Web App + Extension Surfaces

**Feature**: `specs/008-design-system-pass` · **Branch**: `ai-bd-assistant` · **Date**: 2026-08-15
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

## User stories

Derived from the spec's acceptance scenarios and the requester's three stated problems.

| ID | Story | Scenarios | Independent test |
|---|---|---|---|
| **US1** | One visual language across all four surfaces | 1, 2, 6, 7 | Open any two surfaces side by side — same tokens, no legacy palette, no sub-12px text, no h-overflow |
| **US2** | Dismiss the side panel from inside it | 3 | Click the panel's close action; panel closes; exactly one dismiss affordance per region |
| **US3** | Real artwork resolves everywhere | 4, 5 | Toolbar, extensions list, panel header, and browser tab all show the mark; legible at 16px |

US1 is the MVP. US2 and US3 are independent of each other and both depend only on Phase 2.

---

## Phase 1: Setup

- [x] T001 Move the design bundle to `docs/design/` and track it, so the visual spec is no longer one `git clean` from gone
- [x] T002 Create `design/` directory and transcribe the handoff `:root` block into `design/tokens.css`, using the full token table in [data-model.md](./data-model.md) as the checklist
- [x] T003 [P] Author `design/mark.svg` — 128×128 viewBox, bolt glyph in white on a `--grad` rounded square (~23% corner radius), no text, legible when scaled to 16px
- [x] T004 [P] Fetch Inter and JetBrains Mono variable `woff2` into `extension/fonts/` and `web/public/fonts/`; if unobtainable, record the fallback-to-system-stack decision in research.md and skip the `@font-face` blocks

## Phase 2: Foundational — blocks every user story

- [x] T005 Write `scripts/sync_design_tokens.py` implementing the marker contract in [contracts/design-tokens.md](./contracts/design-tokens.md): region replacement between `/* >>> generated: design tokens */` and `/* <<< end generated */`, plus `--check` mode with a line-level diff on drift
- [x] T006 Add the retired-palette regression guard to `--check`: fail if `#f97316`, `#0d1117`, `#161b22`, `#30363d`, `#e6edf3`, `#8b949e`, `#38bdf8`, `#4ade80`, `#f87171`, or the `249, 115, 22` rgba triplet appears in either consumer
- [x] T007 Insert the generated markers into `web/src/index.css` and `extension/tokens.css`, then run the script to populate both token regions from `design/tokens.css`
- [x] T008 Add `sync-tokens`, `check-tokens`, and `build-icons` targets to `Makefile` and list them under the help text
- [x] T009 Verify `python3 scripts/sync_design_tokens.py --check` exits 0 when synced and non-zero after a deliberate hand-edit to a consumer's token region

**Checkpoint**: tokens have one upstream and drift is detectable. US1, US2, US3 may now proceed.

---

## Phase 3: US1 — One visual language

**Goal**: all four surfaces render the handoff's design language.
**Independent test**: open web app, panel, popup, options; confirm shared tokens, no legacy palette, no sub-12px text, no horizontal overflow at narrow widths.

### Extension surfaces

- [x] T010 [US1] Rewrite the component classes in `extension/tokens.css` in the new language — glass panels (`--panel`), hairline borders, radius ramp, `--grad` primary buttons, `--font-ui`/`--font-mono`, and the rescaled 12px-floor type ramp from [data-model.md](./data-model.md)
- [x] T011 [US1] Keep the explicit `body { font-size }` rule in `extension/tokens.css` and its comment — Chrome's UA stylesheet shrinks extension-page body to `0.75em`, so inheriting silently yields 11.25px (NFR-004)
- [x] T012 [US1] Add `@font-face` declarations for the self-hosted fonts in `extension/tokens.css` with a system-stack fallback in every `font-family` chain
- [x] T013 [US1] Restyle `extension/sidepanel.html` — replace the inline `<style>` block's legacy values, adopt compact density, and remove the hard-coded `rgba(249, 115, 22, 0.1)` focus ring
- [x] T014 [US1] Rebuild the side panel's brief layout in the handoff's richer presentation (identity header, sectioned brief, follow-up rows with day chips) in `extension/sidepanel.html` + `extension/sidepanel.js`
- [x] T015 [US1] Add the `inert` brief sections per [data-model.md](./data-model.md) — buying signal, contact confidence, outreach email, CRM mapping, source count, research steps — designed but muted, explicitly labelled unavailable, no spinner or skeleton, no fabricated values
- [x] T016 [US1] Preserve `createElement`/`textContent` construction throughout `extension/sidepanel.js`; restyling changes class names only, never the construction method (NFR-003)
- [x] T017 [P] [US1] Restyle `extension/popup.html` + `popup.js` — thin 320px launcher only; do not add brief rendering
- [x] T018 [P] [US1] Restyle `extension/options.html` + `options.js` — keep sign-in, client ID, redirect URI, and provider fields intact
- [x] T019 [US1] Verify no horizontal overflow in the panel at its narrowest width; collapse the `field-row` grid and footer grid as needed

### Web app

- [x] T020 [US1] Restyle base layout and typography in `web/src/index.css` outside the generated token region — background, text ramp, focus rings, form controls
- [x] T021 [US1] Add `@font-face` for the self-hosted fonts in `web/src/index.css` with system fallback
- [x] T022 [US1] Replace the header navigation with the handoff's 232px sidebar shell in `web/src/App.tsx` and `web/src/App.css` (FR-012)
- [x] T023 [P] [US1] Restyle `web/src/components/LoginPage.tsx` and `GoogleLoginButton.tsx`
- [x] T024 [P] [US1] Restyle `web/src/components/Dashboard.tsx` and `UsageView.tsx`
- [x] T025 [P] [US1] Restyle `web/src/components/Composer.tsx`
- [x] T026 [US1] Restyle `web/src/components/Preview.tsx` to match the panel's brief presentation, including the same `inert` sections
- [x] T027 [P] [US1] Restyle `web/src/components/HistoryList.tsx`, `ConnectionsForm.tsx`, `MemoryProfile.tsx`, `Changelog.tsx`
- [x] T028 [US1] Add transform-only `risein` entrance motion that never gates visibility on opacity, guarded by `prefers-reduced-motion` (NFR-011)
- [x] T029 [US1] Run `cd web && npm run build` and fix any breakage

**Checkpoint**: US1 independently testable.

---

## Phase 4: US2 — Dismiss the side panel

**Goal**: the panel can be closed from inside it, without competing with Chrome's own chrome.
**Independent test**: activate the close action; panel closes; one dismiss affordance per region.

- [x] T030 [US2] Load unpacked in real Chrome and **look at what Chrome renders in its side-panel header** — record the actual controls before placing anything (FR-005, research R2) — **confirmed 2026-08-15: footer placement reads correctly against Chrome's own header**
- [x] T031 [US2] Add a labelled close action to the panel **footer** in `extension/sidepanel.html` — not an X in the top-right, where Chrome's own close control sits
- [x] T032 [US2] Wire the control to `window.close()` in `extension/sidepanel.js`, with an accessible label
- [x] T033 [US2] Confirm the footer control does not break the footer's grid at the narrowest panel width

**Checkpoint**: US2 independently testable.

---

## Phase 5: US3 — Real artwork

**Goal**: the product mark resolves in the toolbar, extensions list, panel header, and browser tab.
**Independent test**: all four locations show the mark; the 16px raster is recognisable.

- [x] T034 [US3] Write `scripts/build_icons.py` — rasterize `design/mark.svg` to 16/48/128 PNG via headless Chrome `--screenshot`, using `--force-device-scale-factor=1` and `--default-background-color=00000000`, and ignoring the WSL `dbus` stderr noise (research R1)
- [x] T035 [US3] Generate `extension/icons/{16,48,128}.png` and assert each decodes at its declared size with a file size far above the 428/175/95-byte blanks it replaces
- [x] T036 [US3] Visually check the 16px raster — if the bolt is illegible at that size, thicken the glyph and increase its share of the square, then regenerate
- [x] T037 [US3] Add `action.default_icon` for all three sizes to `extension/manifest.json` (FR-007). Change **only** that key — never `version`, never `key`
- [x] T038 [P] [US3] Replace `web/public/favicon.svg` with the mark and confirm `web/index.html` references it
- [x] T039 [P] [US3] Update `docs/extension-store.md` to point at the real artwork instead of the placeholder SVG

**Checkpoint**: US3 independently testable.

---

## Phase 6: Polish & verification

- [x] T040 Install `puppeteer-core` in the scratchpad (not the repo) and point `executablePath` at the cached Chrome at `~/.cache/puppeteer/chrome/linux-151.0.7922.77/chrome-linux64/chrome`
- [x] T041 Write the harness: launch with `--load-extension` + `--disable-extensions-except`, open `chrome-extension://kopmahhdddlcipdggmgldkofjpneeboa/{sidepanel,popup,options}.html`
- [x] T042 Assert per [contracts/surfaces.md](./contracts/surfaces.md): empty console-error log, `scrollWidth <= clientWidth`, every computed `font-size >= 12`, tokens resolve, icons load with non-zero natural dimensions
- [x] T043 Run the panel assertions at **several widths**, not just the default — it is user-resizable and default-width success proves nothing about the narrow case
- [x] T044 Check text contrast against the **composited** background, not the token alpha — glass surfaces over near-black can lose contrast at small sizes
- [x] T045 Rebuild and eyeball the web app: `docker compose up -d --build web` (note: `docker compose restart` does **not** pick up code changes), then load `http://localhost:8080`
- [x] T046 Manual pass in real Chrome: load unpacked, open all three surfaces, confirm the design, the close action, and the icons — the harness cannot see the browser's panel chrome — **confirmed 2026-08-15**
- [x] T047 Run gates: `cd backend && pytest tests/` (expect 77 passed) and `cd web && npm run build` and `make check-tokens`
- [x] T048 Update `CHANGELOG.md` and cut the release — shipped as **v0.2.0** via `make bump-minor`; no version field hand-edited

---

## Dependencies

```
Phase 1 (T001–T004)
      ↓
Phase 2 (T005–T009)  ← blocks everything
      ↓
   ┌──────────────┬──────────────┐
   ▼              ▼              ▼
 US1 (T010–T029) US2 (T030–T033) US3 (T034–T039)
   └──────────────┴──────────────┘
                  ▼
          Phase 6 (T040–T048)
```

- US1, US2, US3 are mutually independent once Phase 2 is done.
- T014 → T015 → T016 are strictly sequential (same file, `sidepanel.js`).
- T013 → T014 sequential (same file, `sidepanel.html`); T031 also touches it, so US2 should follow T013 or be merged carefully.
- T030 must precede T031 — placement depends on what Chrome actually renders.
- T034 → T035 → T036 sequential; T036 may loop back to T003.

## Parallel opportunities

| Group | Tasks |
|---|---|
| Setup | T003, T004 |
| Extension restyle | T017, T018 after T010–T012 |
| Web components | T023, T024, T025, T027 after T020–T022 |
| Artwork tail | T038, T039 after T035 |

## Implementation strategy

**MVP = Phase 1 + Phase 2 + US1.** That delivers the actual ask — the product looks like the design
— and the token upstream makes every later change cheap. US2 (4 tasks) and US3 (6 tasks) are small
and can land in the same session.

Ship order: tokens first so nothing is restyled twice, then the extension (self-contained, no build),
then the web app (where `npm run build` is a real gate), then verification.

**Total**: 48 tasks — Setup 4, Foundational 5, US1 20, US2 4, US3 6, Polish 9.
