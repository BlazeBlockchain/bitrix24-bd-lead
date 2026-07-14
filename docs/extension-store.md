# Chrome Web Store / Firefox Add-ons Submission Assets
# Extension: AI BD Lead Assistant (thin MV3 client)

**Task**: T027 - Polish: Extension store submission assets (screenshots, description)
**Status**: Assets + copy prepared (pre T016 scaffold; ready for integration)
**Date**: 2026-07-14
**Refs**: docs/CONCEPT.md, docs/UI_UX.md, docs/FEATURES.md, specs/004-ai-bd-assistant/{plan.md, spec.md, tasks.md}, README.md

---

## Store Listing Metadata (for submission form)

### Proposed Extension Name (Chrome/Firefox)
**BD Lead AI** (or "AI BD Lead Assistant" if space allows; max ~45 chars)

Alternative: "BD Lead – AI CRM Assistant"

### Short Description (max 132 characters for Chrome Web Store)
"Paste a signal. Get AI-enriched preview + 3 perfect follow-up tasks. Push to Bitrix24 or HubSpot in seconds."

(Count: 118 chars. Emphasizes non-technical flow per CONCEPT.)

### Detailed Description (paste into store; ~1500-3000 chars recommended)

Turn every buying signal into a ready-to-execute CRM record in under a minute.

**Paste signal → magic AI 3 tasks → CRM.**

As a non-technical BD rep, you no longer waste time on manual data entry or generic follow-ups. BD Lead uses AI (v1 feature) to generate a personalized company snapshot, tone-matched email opener, and exactly 3 follow-up tasks with timing rationale — then pushes them directly into your CRM as Contact + Deal + linked Tasks.

**How it works (the non-technical flow):**
1. Install the thin extension (or use the companion web app).
2. Connect Bitrix24 (paste webhook — one time) or HubSpot (OAuth).
3. While on LinkedIn, a prospect page, or your CRM: open the popup, paste or auto-detect the company + contact + signal.
4. Hit "Generate with AI" — instantly see:
   - One-paragraph company snapshot from public signals.
   - Personalized first-email opener matched to your style.
   - 3 concrete follow-ups (e.g. Check+Connect +4 days, Short Bump +9, Close the Loop +14) with "why this timing".
5. One click "Push to CRM" — Contact, Deal, and 3 dated Tasks appear correctly linked in Bitrix24 or HubSpot.
6. It gets smarter: memory of your tone, cadence, and past outcomes personalizes every future lead automatically.

**Why BD reps love it:**
- **AI generate is the core** — real enrichment + rationale, not just form filler.
- **Works where you work** — thin extension popup lives in your browser tabs (CRM or LinkedIn). No tab switching.
- **Multi-CRM, zero hassle** — Bitrix24 webhook or HubSpot. Correct associations, deadlines, and linking every time.
- **Memory compounds value** — "Personalized using your last 7 leads." The more you use it, the better the output feels like a smarter version of you.
- **Thin & fast** — No heavy UI. Paste → preview → push. Mobile-friendly web fallback always available.
- **Built for SMB BD** — Designed for non-technical reps in CEE, CIS, Africa and beyond who use Bitrix24 today and HubSpot as upgrade path.

**Perfect for:**
- Solo BD reps and SMB sales teams tired of repetitive CRM admin.
- Anyone who has ever manually created a contact + deal + 3 tasks and thought "there has to be a better way."

**Supported CRMs (v1):** Bitrix24 (webhook), HubSpot (OAuth). More coming via the same adapter contract.

**Companion surfaces:**
- Full web app at bdlead.app for onboarding, history, account & billing.
- MCP tool for power users (still works).

Privacy-first: Your CRM tokens are encrypted server-side. AI runs on cheap, efficient models. You own your data and memory profile.

Install once. Paste a name + signal today. Never go back to manual entry.

---

## Screenshot Descriptions & Instructions (for store assets; 1280x800 px recommended, PNG, 5 max)

**Required for submission. Take real screenshots once T016/T017/T018 delivered and UI finalized. Use dark theme, realistic data (fictional leads).**

1. **Popup - Composer with visible page data (extension hero shot)**
   - Caption: "Compact popup on LinkedIn or CRM tab. Auto-detects company/contact. Paste your signal and Generate with AI."
   - Visual: Small clean popup window showing form fields pre-filled (Company: "Acme Corp", Contact: "Jane Doe - VP Sales", Signal: "Series B funding announced last week"), "Generate with AI" primary button prominent. Subtle "Connected to your Bitrix24" status. Dark UI matching web.

2. **Composer UI with preview pane (after Generate)**
   - Caption: "See the magic instantly: AI snapshot, personalized opener, and 3 follow-up tasks with rationale. Ready to push."
   - Visual: Split or stacked preview in popup (or web modal for larger). Shows:
     - Company Snapshot paragraph.
     - Suggested Opener (with copy button).
     - Follow-up Plan: 3 cards/timeline items titled e.g. "Check+Connect", "Short Bump", "Close the Loop" + due dates + "Why this timing: leverage momentum from recent funding".
     - "Personalized using your memory from 4 prior leads" note.
     - Big "Push to CRM" button (enabled).
   - Emphasize non-technical delight: clean, scannable, no jargon.

3. **Connections connected state**
   - Caption: "One-time setup. Connect Bitrix24 or HubSpot — then it's paste → magic forever."
   - Visual: Extension Options page (or popup status) showing two cards:
     - Bitrix24: green "Connected" pill, masked webhook, last validated timestamp, Reconnect/Remove.
     - HubSpot: "Connected via OAuth".
     - "Open full web dashboard" link.
   - Matches UI_UX: forgiving, clear status.

4. **Push success + CRM confirmation hint (result screen)**
   - Caption: "One click and it's in your CRM. Contact + Deal + 3 Tasks created with perfect linking."
   - Visual: Success state in popup: "✅ Created Contact 1234, Deal 567, Tasks 89/90/91." Links or "View in Bitrix24" buttons. History item preview. Subtle memory note for next time.

5. **History / "use similar" on web or extension (optional 5th)**
   - Caption: "Review what worked. Use similar lead to compound your memory advantage."
   - Visual: List of past leads (company, date, CRM) + detail view with exact snapshot/opener/tasks pushed. "Create similar" button pre-fills composer.

**Instructions for real screenshots:**
- Use realistic but fictional data matching CONCEPT examples (Series B signal, +4/+9/+14 cadence).
- Show both Bitrix24 and HubSpot badges.
- Include the "Personalized using your..." memory callout.
- Mobile viewport + desktop popup.
- No login walls in shots; show logged-in happy states.
- Follow UI_UX dark theme tokens (bg #0d1117, accent orange etc. from web).
- After T016 scaffold + T017 thin client, capture from actual unpacked extension (chrome://extensions → Load unpacked).
- Name files: `screenshot-1-popup-composer.png`, etc.
- Alt text / store descriptions should repeat the non-tech flow: "paste signal -> magic AI 3 tasks -> CRM".

---

## Icon & Promo Assets (Manifest + Store)

### Icon Guidance
- Chrome Web Store requires:
  - 128×128 PNG (for listing + extension icon)
  - 48×48, 16×16 generated from it (or provide).
- Recommended: Simple, recognizable "lead rocket" or "AI sparkle + CRM checkmark" on dark bg.
- Colors: Dark navy/black + vibrant orange accent (#f97316 from UI) + white text.
- Text-free preferred for small sizes; "BD" monogram + magic sparkles.

### Placeholder SVG Icon (copy to extension/assets/icon.svg or web/public when T016 lands)
Use this simple scalable placeholder (or improve with designer). Save as 128x128 PNG export for store.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128" fill="none">
  <!-- Background -->
  <rect width="128" height="128" rx="24" fill="#0d1117"/>
  <!-- CRM card shape -->
  <rect x="20" y="28" width="88" height="72" rx="8" fill="#161b22" stroke="#30363d" stroke-width="4"/>
  <!-- Sparkle / AI magic -->
  <path d="M44 44 L48 56 L60 52 L48 60 L44 72 L40 60 L28 56 L40 52 Z" fill="#f97316"/>
  <!-- Check / push arrow into CRM -->
  <polyline points="72,68 80,76 96,56" stroke="#3fb950" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Small Bitrix/Hub logos hint (abstract) -->
  <circle cx="100" cy="40" r="6" fill="#58a6ff"/>
  <circle cx="108" cy="48" r="4" fill="#f97316"/>
</svg>
```

**Notes for manifest (when T016 creates extension/manifest.json):**
```json
{
  "name": "BD Lead AI",
  "short_name": "BD Lead",
  "description": "Paste a signal. Get AI-enriched preview + 3 perfect follow-up tasks. Push to Bitrix24 or HubSpot in seconds.",
  "version": "0.1.0",
  "manifest_version": 3,
  "icons": {
    "16": "assets/icon-16.png",
    "48": "assets/icon-48.png",
    "128": "assets/icon-128.png"
  },
  "action": { "default_popup": "popup.html" },
  "options_page": "options.html",
  ...
}
```
Update short_name/description to match above. No code change needed until scaffold.

**Promo tile / screenshots header image (optional 1400x560):** Hero from UI_UX landing + "Paste. AI. CRM." overlay text.

---

## Submission Checklist Notes

- **Category**: Productivity / Sales & CRM (or Search "sales" in store).
- **Language**: English (primary); add localized later if needed.
- **Privacy policy URL**: Link to (future) /privacy or GitHub note. Tokens encrypted server-side (see ARCHITECTURE).
- **Support email / website**: Use project contact or bdlead.app placeholder.
- **Demo video (strong rec)**: 30-60s GIF or MP4 of: open popup on LinkedIn → paste signal → Generate → preview → Push → success toast + record visible in Bitrix sandbox. Mirrors UI_UX "30s video".
- **Permissions justification** (MV3): storage (for thin JWT/token), activeTab / host permissions only for detected CRM/LinkedIn hosts (minimal).
- **No remote code**: Confirmed (thin client; all logic backend).
- **Testing notes**: Works unpacked on Chrome/Firefox. Test both providers.

---

## How These Assets Were Derived (for future maintainers)

- Core hook and flow language lifted directly from CONCEPT.md ("paste or trigger...", "3 concrete follow-up tasks", "Memory is the moat", "thin-client", non-technical user story) + UI_UX.md (exact popup/options, journey steps, "paste → magic → push", memory surface).
- "Store assets emphasize non-technical BD flow: paste signal -> magic AI 3 tasks -> CRM." (directive).
- Screenshots examples match UI_UX "Browser Extension Surfaces" and "Lead Composer" + "Connections".
- Messaging decisions: benefit + speed + AI visibility + memory + thin UX. Avoided all implementation details.
- See also: web/src/components/Composer.tsx + Preview.tsx (current preview shape for screenshot fidelity), ConnectionsForm.tsx.

When T016/T017 deliver the extension, move this file contents (or whole) to `extension/assets/store-description.md` or similar and regenerate final PNGs.

**Ready for store submission once extension is built and screenshots captured.**

---

*This document created as part of T027. See BUILD_COORDINATION.md for implementation log.*
