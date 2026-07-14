# Implementation Plan: Research Skill Versioning & Encryption

**Branch**: `004-ai-bd-assistant` (continuous)  
**Date**: 2026-07-14  
**Status**: COMPLETE (all T029-T035 shipped)

## Summary

Ship the proprietary BD Lead Research Engine as encrypted server-side IP (never exposed to clients), establish semantic versioning with a single source of truth (VERSION file), and make the encryption and versioning workflows repeatable via Makefile and CI/CD-friendly scripts.

**Approach**:
1. Store the skill methodology as an encrypted Fernet artifact (`bd_lead_research.md.enc`), using the same `ENCRYPTION_KEK` as CRM tokens (reuse token_vault infrastructure).
2. Decrypt on server startup, cache in memory, inject into LLM prompts (T007).
3. Git-ignore plaintext source (`bd_lead_research.source.md`); only commit the `.enc` artifact.
4. Establish VERSION file as single source of truth; sync all components (web/package.json, extension/manifest.json, backend/config.py) via Python script.
5. Provide Makefile targets: `bump-patch|minor|major`, `release` (commit + tag), `encrypt-skill` (re-encrypt with current KEK).
6. Add web footer version display (via `/api/health`), `/changelog` page, and marketing copy describing the engine as proprietary and encrypted.
7. Document production deployment (re-encrypt with prod KEK, set JWT_SECRET, enable HTTPS, etc.).

**Why this approach**:
- **Reuse existing vault**: Token_vault (T006) already does Fernet encryption with KEK; skill encryption uses the same pattern (consistency, no new crypto code).
- **Single file versioning**: VERSION file is simple, diff-friendly, and enables easy CI/CD integration.
- **Decryption fallback**: If key is missing/wrong, fallback instruction keeps the app running (graceful degradation).
- **Marketing first-class**: Skill IP protection is a selling point; document it prominently in README, ARCHITECTURE, and SECURITY docs.

## Technical Context

**Language/Dependencies**: Python (skill_loader, token_vault), TypeScript (web/extension for version display), Makefile (versioning orchestration), Fernet (cryptography).

**Key Files**:
- `backend/app/skills/bd_lead_research.md.enc` — encrypted skill artifact (committed).
- `backend/app/skills/bd_lead_research.source.md` — plaintext source (git-ignored).
- `backend/app/services/skill_loader.py` — load_skill, decrypt, cache, fallback.
- `backend/app/services/llm_service.py` — injects skill into prompt via _build_prompt.
- `scripts/encrypt_skill.py` — re-encrypt script (called by Makefile).
- `scripts/sync_versions.py` — sync VERSION to all components.
- `scripts/bump_version.py` — increment VERSION (patch/minor/major).
- `scripts/update_changelog.py` — stage CHANGELOG section for editing.
- `VERSION` — single source of truth (e.g., "0.1.0").
- `CHANGELOG.md` — Keep a Changelog format.
- `Makefile` — versioning targets (version, sync-versions, bump-patch/minor/major, release, encrypt-skill).
- `web/src/components/Changelog.tsx` — render CHANGELOG.md as page.
- `web/src/App.tsx` — add /changelog route, version footer.
- `README.md` — marketing section (proprietary encrypted engine).
- `SECURITY.md` — skill IP protection section.
- `docs/ARCHITECTURE.md` — BD Lead Research Engine subsection.

## Architecture

### Skill Encryption (T030)
```
plaintext: backend/app/skills/bd_lead_research.source.md (dev only, git-ignored)
    ↓ (scripts/encrypt_skill.py + ENCRYPTION_KEK from .env)
encrypted: backend/app/skills/bd_lead_research.md.enc (committed to git)
    ↓ (backend startup)
skill_loader.load_skill() calls decrypt_credentials(ciphertext)
    → _strip_yaml_frontmatter() → _strip_mcp_footer()
    → _cached_skill (module-level, one per process)
    ↓
llm_service._build_prompt() injects skill into system message
    ↓
LLM receives structured prompt (never returned to client)
```

### Versioning (T032)
```
VERSION file (e.g., "0.1.0") — single source
    ↓
make bump-patch: scripts/bump_version.py → VERSION updated + synced
    ↓
web/package.json version updated
extension/manifest.json version updated
backend/app/config.py APP_VERSION updated
    ↓
CHANGELOG.md staged for manual edit (new section under [Unreleased])
    ↓
make release: git commit + git tag vX.Y.Z + echo next steps
```

### Web Footer & Changelog (T033-T034)
```
/api/health endpoint returns {"status":"ok","app_version":"0.1.0"}
    ↓
web/src/components/Footer.tsx displays version
    ↓
web/src/components/Changelog.tsx fetches root CHANGELOG.md
    ↓
/changelog route renders full release history
```

### Marketing & Docs (T035)
```
README.md: "BD Lead Research Engine — proprietary, encrypted server-side IP"
    ↓
docs/ARCHITECTURE.md: subsection describing skill storage, decryption, fallback
    ↓
docs/SECURITY.md: §3 "Skill IP Protection" (encryption, never client-side, fallback)
    ↓
.env.example: note that ENCRYPTION_KEK also encrypts skill (+ re-encrypt guidance)
    ↓
SECURITY.md §8: Production checklist (set ENCRYPTION_KEK, run make encrypt-skill, commit .enc)
```

## Sequencing

### Phase 0: Setup (committed T029-T031)
- **T029**: Skill encryption backend (token_vault, skill_loader).
- **T030**: Encrypt skill artifact; git-ignore source.
- **T031**: Makefile versioning (bump, release, encrypt-skill).

### Phase 1: Frontend & Marketing (committed T032-T034)
- **T032**: SemVer versioning (VERSION file, Makefile, CHANGELOG).
- **T033-T034**: Web footer + /changelog page; marketing copy.

### Phase 2: Docs & Release (committed T035)
- **T035**: README section (proprietary engine + versioning), ARCHITECTURE subsection, SECURITY.md, .env.example note, specs/005-research-skill-versioning/ formalization.

## Success Definition

All T029-T035 tasks complete and committed:
- ✅ Skill encrypted at rest; plaintext never committed.
- ✅ VERSION file as single source; all components in sync.
- ✅ Makefile targets working (bump-patch, release, encrypt-skill).
- ✅ Web footer shows version; /changelog page renders CHANGELOG.md.
- ✅ Marketing copy accurately describes proprietary encrypted engine (no skill content leaked).
- ✅ SECURITY.md documents encryption, key rotation, fallback, production checklist.
- ✅ Docs/ARCHITECTURE updated with skill subsection.
- ✅ smoke test: `npm run build` clean, `python3 -c "import json; json.load(open('package.json'))"` passes, grep for skill content returns nothing.

---

**Next**: Release v0.1.0 and deploy to production (set real ENCRYPTION_KEK, re-encrypt skill, follow SECURITY.md §8 checklist).
