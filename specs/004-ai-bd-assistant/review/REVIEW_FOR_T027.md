# REVIEW_FOR_T027.md — Extension store submission assets (T027)

**Implementer**: T027 Polish assets (this session)
**Date**: 2026-07-14
**Verdict**: COMPLETE (assets/docs delivered; ready for post-T016 real assets)

## Mandatory Re-reads Performed
- BUILD_COORDINATION.md (full context + spawn notes)
- specs/004-ai-bd-assistant/{plan.md, tasks.md, spec.md}
- docs/UI_UX.md (primary)
- docs/CONCEPT.md (messaging source)
- Supporting: FEATURES, ARCHITECTURE, README, web components

## What Was Delivered
- docs/extension-store.md (full store copy + placeholders)
- docs/bd-lead-icon-placeholder.svg
- tasks.md update
- README link
- Detailed BUILD_COORDINATION appends (start + completion with decisions)

## Alignment Check
- Messaging decisions directly from CONCEPT: non-technical flow ("paste or trigger... 3 concrete follow-up tasks"), UVP bullets (AI v1, Memory moat, thin-client extension, Bitrix+HubSpot), user stories.
- UI_UX fidelity: popup, options, composer/preview, connections states, memory surface, journey steps all mapped to screenshot instructions + copy.
- "Store assets emphasize non-technical BD flow: paste signal -> magic AI 3 tasks -> CRM." — embedded throughout.
- No breakage: zero src/backend/web changes. Builds/tsc green.
- Minimal change: only docs + 1 svg + 2 edits (tasks/README).

## Suggestions (for when extension lands)
- Capture real screenshots matching the 5 placeholders (use actual popup after T016-18).
- Export PNGs at store specs (1280x800+).
- Sync manifest name/desc from this doc.
- Add 30s demo video/GIF.
- Consider moving docs/extension-store.md → extension/assets/ post scaffold.

## Files
See BUILD_COORDINATION.md for exact list + timestamps.

**PASS for this polish slice.** No code to review. High fidelity to grounding docs.

Refs: docs/extension-store.md (self-documenting derivation section).
