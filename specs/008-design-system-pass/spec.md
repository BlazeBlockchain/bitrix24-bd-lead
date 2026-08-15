# Feature Specification: Design System Pass — Web App + Extension Surfaces

**Feature Branch**: `ai-bd-assistant`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User request — apply the bd-lead design handoff to the web app and all three extension
surfaces; give the side panel a way to dismiss itself; replace the blank/placeholder icon artwork.

## Problem

The product has a finished, high-fidelity visual design (the handoff bundle at
`docs/design/`) that has never been applied to the shipped surfaces. Three concrete
consequences:

1. **The shipped UI is a different product from the designed one.** The web app and the three
   extension pages use a legacy palette — orange accent on GitHub-dark, solid surfaces, a single
   corner radius, the system font stack. The design calls for an iris→violet→cyan gradient accent on
   near-black navy, translucent glass surfaces, a four-step radius ramp, and Inter + JetBrains Mono.
   Nothing about the current look is intentional; it predates the design.
2. **The design tokens are duplicated by hand.** `web/src/index.css` and `extension/tokens.css`
   carry the same values, typed twice, with no mechanism to detect divergence. Any restyle doubles
   the work and silently drifts. Neither file has an upstream.
3. **The side panel cannot be dismissed from inside it, and the extension has no artwork.** Users
   who open the panel have no in-panel way to close it. The three icon PNGs are valid files but
   essentially blank (128×128 RGBA is 428 bytes), the manifest's `action` entry declares no
   `default_icon` so the toolbar and panel header fall back to a generic mark, and the web favicon is
   still unmodified template art rather than the product's logo.

## User Story

As a business-development user, I want the web app and the extension to look like one deliberate,
finished product, so that the tool feels trustworthy enough to keep open next to a prospect's page
all day — and I want to close the panel when I am done with it without hunting for the browser's own
controls.

### Acceptance Scenarios

1. **One visual language** — Given the user moves between the web app, the side panel, the launcher
   popup, and the options page, when they compare any two surfaces, then the background, accent
   gradient, surface treatment, border weight, corner radii, and typography are drawn from the same
   token set, and no surface shows the retired legacy palette.

2. **Tokens cannot silently drift** — Given a developer changes a design token in the upstream
   source, when the token files are checked, then any divergence between the web token set and the
   extension token set is reported as a failure rather than discovered visually later.

3. **Dismissing the panel** — Given the side panel is open, when the user activates the panel's close
   control, then the panel closes, and the control does not duplicate or visually compete with any
   dismiss affordance the browser already renders in its own panel chrome.

4. **Real artwork resolves everywhere** — Given the extension is loaded, when the user looks at the
   browser toolbar, the extensions list, and the side panel's header, then the product's logo mark is
   visible and legible at each size; and when they open the web app, the browser tab shows the same
   mark rather than template art.

5. **Legible at 16 px** — Given the smallest icon size, when it is viewed at its native size, then
   the mark remains recognisable — it does not rely on text or on detail that disappears when scaled
   down.

6. **The panel stays usable when narrow** — Given the user drags the side panel to its narrowest
   width, when they work through the form and read a generated preview, then no content overflows
   horizontally, no text falls below the minimum body size, and controls remain reachable.

7. **Designed sections with no data are honest** — Given the design shows brief sections the backend
   does not populate, when the user views a generated preview, then those sections appear in the
   designed visual language but are plainly marked as not yet available, and never display invented
   or placeholder-as-real content.

### Edge Cases

- The user's session expires while the panel is open — the restyled error and signed-out states must
  remain visible and legible, not collapse into empty space.
- The web fonts fail to load (offline, or blocked) — every surface must fall back to a system stack
  without layout breakage or sub-minimum text.
- A generated preview returns fewer than three follow-ups — the restyled list must degrade the way
  the current implementation does, without empty designed cards.
- The panel is opened before the user has signed in — the restyled signed-out state must be the first
  thing the user sees, not a styled-but-inert form.
- A very long company name, opener, or follow-up title — must wrap rather than force horizontal
  scrolling at the narrowest panel width.
- The browser renders its own close control in the panel header — the in-panel control must not
  produce a second competing affordance in the same region.

## Requirements

### Functional

- **FR-001**: All four surfaces (web app, side panel, launcher popup, options page) MUST render using
  the design handoff's token set: surfaces, borders, text ramp, accent gradient, semantic colors,
  radius ramp, and type stack.
- **FR-002**: The legacy palette MUST be fully retired — no surface may retain the orange accent or
  the GitHub-dark background, including in focus rings, status colors, and hard-coded rgba values.
- **FR-003**: A single upstream MUST define the design tokens, with the web and extension token files
  derived from it, and an automated check MUST fail when the two derived files diverge.
- **FR-004**: The side panel MUST provide a control that closes the panel from within it.
- **FR-005**: Before the close control is placed, the browser's own side-panel chrome MUST be
  inspected, and the control's placement MUST be chosen so the user sees one dismiss affordance in
  any given region, not two.
- **FR-006**: The extension MUST ship non-blank 16, 48, and 128 px icons carrying the product's logo
  mark as specified by the design (a bolt glyph in a gradient rounded square).
- **FR-007**: The manifest's `action` entry MUST declare `default_icon` for all three sizes, in
  addition to the existing top-level `icons`.
- **FR-008**: The web app MUST ship a favicon carrying the same mark, replacing the template artwork.
- **FR-009**: The web app's existing screens MUST be restyled in place — login, dashboard, composer,
  preview, history, connections, memory profile, usage, changelog.
- **FR-010**: The side panel MUST adopt the design's rich brief presentation; the launcher popup MUST
  remain a thin launcher, restyled only; the options page MUST be restyled to match.
- **FR-011**: Brief sections the backend cannot populate MUST be rendered as designed but visibly
  inert, labelled as unavailable, and MUST NOT display fabricated values.
- **FR-012**: The web app MUST adopt the design's sidebar navigation shell in place of the current
  header navigation.

### Non-Functional

- **NFR-001**: The extension MUST remain buildless — plain HTML, CSS, and classic scripts loaded
  unpacked, with no bundler, transpiler, package manager, or ES modules in the extension directory.
- **NFR-002**: The lead enrichment and CRM push request and response contracts MUST be unchanged,
  including the preview shape consumed by the web app and covered by backend tests.
- **NFR-003**: All content originating from the API, from the page, or from user input MUST be
  rendered as text, never interpreted as markup.
- **NFR-004**: No text on any surface may compute below 12px. Extension pages MUST set an explicit
  body font size rather than inheriting, because the browser's user-agent stylesheet shrinks
  extension-page body text and an inherited size silently falls under the floor.
- **NFR-005**: The side panel MUST NOT scroll horizontally at any width the user can drag it to.
- **NFR-006**: Typography MUST NOT depend on a network fetch at render time; fonts MUST resolve
  locally, with a system fallback if unavailable.
- **NFR-007**: The extension's declared version MUST continue to be generated from the repository's
  single version source; it MUST NOT be hand-edited.
- **NFR-008**: The manifest's `key` MUST NOT change — it pins the extension ID that the OAuth
  redirect URI depends on.
- **NFR-009**: No new browser permissions may be requested for this feature.
- **NFR-010**: Existing backend tests and the web application build MUST remain passing.
- **NFR-011**: Entrance motion MUST NOT gate visibility on opacity, so content cannot become stuck
  invisible; and motion MUST respect a user's reduced-motion preference.

## Success Criteria

- **SC-001**: An observer shown any two of the four surfaces side by side identifies them as the same
  product, with no surface displaying the retired palette.
- **SC-002**: Changing a token in the upstream and regenerating updates both derived files; editing
  one derived file by hand causes the drift check to fail.
- **SC-003**: A user can dismiss the side panel from inside it, and the panel presents exactly one
  dismiss affordance per region of its chrome.
- **SC-004**: All three extension icons and the web favicon render the product mark; each icon file
  carries real artwork rather than near-empty output, and the mark is recognisable at 16 px.
- **SC-005**: Across all four surfaces, no rendered text computes below 12px and no surface scrolls
  horizontally at its narrowest supported width.
- **SC-006**: All four surfaces load with zero console errors.
- **SC-007**: The backend test suite and the web build both pass, unchanged in count.

## Key Entities

- **Design token set** — the named values (surfaces, lines, text ramp, brand gradient, semantic
  colors, radii, spacing density, type stack, shadows) that define the visual language. One upstream
  definition, two derived consumers.
- **Logo mark** — the product's identity glyph, rendered as vector source and exported to the fixed
  raster sizes the browser requires, plus a vector favicon.
- **Surface** — one of the four rendering contexts: web app, side panel, launcher popup, options
  page. Each consumes the token set; they differ in width constraints and available data.
- **Inert brief section** — a designed region of the lead brief for which no backing data exists,
  presented in the visual language but explicitly marked unavailable.

## Assumptions

- The design handoff at `docs/design/` is authoritative for the visual language; its
  `styles.css` is the token source of truth and its README is the written specification. The
  prototypes in that bundle are references, not shippable code.
- The handoff's brand accent supersedes the legacy orange. This was confirmed explicitly, and it
  inverts an earlier assumption that orange was the product accent.
- Where the handoff specifies chip text at roughly 11px, the project's 12px floor takes precedence
  and the type ramp is rescaled upward from 12px.
- The handoff's rich toolbar popup maps onto the shipped side panel, not onto the launcher popup; the
  handoff's in-page injected panel is not built, as the side panel already serves that role.
- Onboarding and billing screens described in the handoff are not built; only screens that exist
  today are restyled.
- Fonts are self-hosted rather than fetched from a font CDN, to satisfy the local-resolution
  requirement on extension pages and to keep the surfaces working offline.
- The design's density scale is adopted, with the panel using a tighter density than the web app
  given its constrained width.

## Out of Scope

- Onboarding and billing screens, plan selection, and payment UI.
- An in-page content-script panel injected over the user's tab.
- Any change to enrichment or push API contracts, or to the preview data shape.
- Making the backend return the additional brief fields the design depicts (buying signal with
  source and date, contact confidence, full outreach email, CRM field mapping, research step
  progress). These remain inert per FR-011.
- Converting the extension to a build pipeline or module system.
- Store listing assets and screenshots beyond the icons themselves.
- Mobile/responsive work on the web app beyond not regressing what exists.
