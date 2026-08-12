# Feature Specification: Extension Side Panel Workspace

**Feature Branch**: `ai-bd-assistant`
**Created**: 2026-08-12
**Status**: Draft
**Input**: User request — "the popup is too cramped"; evaluate side panel vs content-script drawer vs expanded popup, recommend one.

## Problem

The extension's only surface is a toolbar dropdown popup constrained to a 500px-wide body. Chrome
caps such popups at roughly 800x600 and dismisses them on any click outside the popup. The result:

- The lead form and the AI preview (company snapshot, personalized opener, three follow-up tasks)
  compete for the same cramped column, forcing 10-11px type that is hard to read.
- The preview disappears the moment the user clicks back onto the prospect's page — precisely when
  they want to cross-reference what the AI produced against what they are reading.
- There is no way to keep the tool open while browsing, which is the core research workflow.

## User Story

As a business-development user researching a prospect in my browser, I want a roomy panel that stays
open beside the page while I browse, so that I can read a prospect's site and the AI-generated
preview side by side, capture context from the page without retyping it, and push a lead to my CRM
without losing my place.

### Acceptance Scenarios

1. **Persistent workspace** — Given the panel is open on a prospect's page, when the user clicks
   anywhere on the page, scrolls, or navigates to another page in the same tab, then the panel
   remains open and retains the form values and any generated preview.
2. **Quick entry point** — Given the user clicks the toolbar icon, when the launcher appears, then it
   offers a single obvious action to open the full workspace, plus links to settings and the web
   dashboard, and shows whether the backend is reachable and who is signed in.
3. **Readable preview** — Given a preview has been generated, when the user reads it in the panel,
   then the company snapshot, opener, and all three follow-up tasks are legible at normal body text
   size and each follow-up shows its title, description, due offset, and rationale.
4. **Capture from page** — Given the user is on a page describing a prospect and has optionally
   selected some text, when they invoke the capture action, then the form is prefilled with context
   drawn from that page (company name, signal, source URL) and every prefilled field remains editable.
5. **Real sign-in** — Given the user has never configured a token, when they choose to sign in, then
   they authenticate with their Google account and the extension stores a session it can use for
   subsequent requests without the user ever handling a raw token string.
6. **Session visibility** — Given a stored session has expired, when the user opens the panel, then
   they are told their session expired and are offered sign-in, rather than seeing an opaque
   authorization failure after clicking Generate.
7. **Unchanged results** — Given the same lead input, when the user generates a preview and pushes to
   a CRM from the new panel, then the request and response content is identical to what the previous
   popup produced and what the web dashboard produces.

### Edge Cases

- Panel opened on a browser-internal page (`chrome://`, the Web Store, a PDF viewer) where page
  capture is not permitted — capture must fail gracefully with an explanatory message, and every
  other panel function must continue to work.
- Capture invoked on a page with no usable context — the form must be left untouched rather than
  filled with noise, and the user told nothing was found.
- User is on a browser older than the one that introduced side panels — the extension must not appear
  broken; it must fall back to a usable surface and say why.
- The backend is unreachable, or is reachable but rejects the session — these are distinct conditions
  and must produce distinct messages.
- Push is attempted before a preview exists, or attempted twice in a row — the second push must not
  silently create duplicate CRM records.
- Panel is open in one tab and the user switches to another tab — behaviour must be defined and
  consistent (see Assumptions).

## Requirements

### Functional

- **FR-001**: The extension MUST provide a persistent workspace surface, docked to the side of the
  browser, that remains open while the user clicks, scrolls, and navigates within the page.
- **FR-002**: The workspace MUST be resizable by the user, and its layout MUST adapt to the resulting
  width without horizontal scrolling or clipped controls.
- **FR-003**: The workspace MUST contain the complete lead capture form (company, contact, role,
  signal, pain point, notes, CRM provider) and the complete AI preview.
- **FR-004**: The toolbar action MUST open a compact launcher offering a primary action to open the
  workspace, plus access to settings, the web dashboard, backend reachability, and session state.
- **FR-005**: The workspace MUST preserve in-progress form values and the generated preview across
  page navigation and tab switches within a browsing session.
- **FR-006**: The workspace MUST offer an action that captures context from the currently viewed page
  — at minimum the page title, the page URL, and any user-selected text — and maps it into the form.
- **FR-007**: Captured values MUST be presented as editable prefill, never committed automatically,
  and MUST NOT overwrite fields the user has already filled in without the user's consent.
- **FR-008**: The extension MUST let the user sign in with their Google account and MUST obtain its
  API session through the backend's existing Google sign-in exchange.
- **FR-009**: The extension MUST display who is currently signed in, and MUST offer sign-out that
  clears the stored session.
- **FR-010**: The extension MUST verify a stored session against the backend's identity endpoint and
  MUST surface expiry as a distinct, actionable state.
- **FR-011**: The manual token-paste path MUST be removed from the primary flow once sign-in works;
  no user-facing screen may require a user to obtain or paste a raw token.
- **FR-012**: The preview MUST render the company snapshot, the personalized opener, and exactly the
  three follow-up tasks with their title, description, due offset, and rationale.
- **FR-013**: Long preview content MUST be readable without the user losing access to the primary
  actions (generate, push), which must remain reachable at any scroll position.
- **FR-014**: The extension MUST report loading, success, and failure states for both generate and
  push, and failure messages MUST distinguish "cannot reach service", "not signed in / session
  expired", and "service rejected this input".
- **FR-015**: The visual design of every extension screen MUST be consistent with the web dashboard's
  established design language, and MUST use a shared set of design tokens rather than per-file copies.
- **FR-016**: Push MUST be unavailable until a preview exists, and MUST be disabled while a push is
  in flight.

### Non-Functional

- **NFR-001**: The extension MUST remain buildless — plain HTML, CSS, and JavaScript loaded unpacked,
  with no bundler, transpiler, package manager, or generated assets in the extension directory.
- **NFR-002**: The lead enrichment and CRM push request and response contracts MUST be unchanged,
  including the preview shape consumed by the web app and covered by backend tests.
- **NFR-003**: The extension MUST NOT expose, embed, or transmit BD Lead Research skill content to
  the client; that material stays server-side.
- **NFR-004**: The extension MUST request the narrowest set of browser permissions that satisfies the
  requirements, and each added permission MUST be justified in the plan.
- **NFR-005**: All content originating from the API, from the page, or from user input MUST be
  rendered as text, never interpreted as markup.
- **NFR-006**: Stored session material MUST live in extension-local storage only, MUST NOT be written
  to logs, and MUST NOT be readable by the pages the user visits.
- **NFR-007**: The extension's declared version MUST continue to be generated from the repository's
  single version source; it MUST NOT be hand-edited.
- **NFR-008**: Body text in the workspace MUST be at least the size used by the web dashboard; the
  10-11px type of the current popup is not acceptable.
- **NFR-009**: Existing backend tests and the web application build MUST remain passing.

## Success Criteria

- **SC-001**: A user can open the workspace, browse to three different pages in the same tab, and
  still see their in-progress form and generated preview — zero re-entry of data.
- **SC-002**: The full AI preview (snapshot, opener, three follow-ups with rationale) is readable in
  the workspace at its default width without truncation and without shrinking text below dashboard
  body size.
- **SC-003**: A user who has never configured anything can go from a fresh install to a successfully
  pushed lead without ever seeing, copying, or pasting a token.
- **SC-004**: From a prospect's page, a user can produce a complete, pushable lead with fewer manual
  field entries than before, because page context is captured rather than retyped.
- **SC-005**: Generating a preview and pushing a lead from the workspace produce results identical to
  the previous popup for the same input.
- **SC-006**: Driving the full flow produces no browser-console errors, including no cross-origin
  request failures.
- **SC-007**: Every extension screen presents the same palette, spacing, and component styling as the
  web dashboard, as judged against a side-by-side comparison.
- **SC-008**: Backend tests and the web build pass unchanged after the feature lands.

## Key Entities

- **Lead draft** — the user's in-progress capture: company, contact, role, signal, pain point, notes,
  and chosen CRM provider. Survives navigation; cleared after a successful push.
- **AI preview** — the generated company snapshot, personalized opener, and three follow-up tasks
  (title, description, due offset, rationale), plus provenance metadata. Bound to the lead draft.
- **Session** — the signed-in user's identity and the credential the extension presents to the API.
  Has a validity state: absent, valid, or expired.
- **Page context** — the transient title, URL, and selected text captured from the active tab and
  offered as prefill. Never persisted.

## Assumptions

- **A-001**: The target browser is Chrome (and Chromium-based browsers) at a version that supports
  docked side panels. Firefox is not a supported target for this feature; a non-supporting browser
  falls back to the existing popup with an explanatory notice.
- **A-002**: The launcher is retained rather than removed, per user decision, because a fast toolbar
  glance at connectivity and session state has value independent of the full workspace.
- **A-003**: One workspace instance serves the whole browser window; switching tabs re-points page
  capture at the newly active tab but does not discard the current lead draft. This favours the
  research workflow, where the user gathers context from several tabs into one lead.
- **A-004**: Page capture is best-effort heuristics over generic page metadata. It is not a
  site-specific scraper, and no per-site extraction rules are in scope.
- **A-005**: The backend's existing Google sign-in exchange and identity endpoint are used as-is; no
  backend changes are required by this feature beyond configuration needed to accept the extension as
  a client.
- **A-006**: Design tokens are already shared in substance between the extension and the web
  dashboard; the restyle consolidates them into one source rather than inventing a new palette.
- **A-007**: The workspace is a single-lead workspace. Managing a queue or history of multiple leads
  is out of scope.

## Out of Scope

- Any change to the enrichment or push API contracts, or to the preview shape.
- Backend or web dashboard feature work, beyond configuration to accept the extension as a sign-in
  client.
- Firefox or Safari support.
- A content-script overlay injected into page content.
- Multi-lead queues, saved drafts across browser restarts, or lead history in the extension.
- Site-specific prospect scrapers.
