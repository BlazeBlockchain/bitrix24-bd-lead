---
description: "Task list for research skill versioning and encryption"
---

# Tasks: Research Skill Versioning & Encryption (T029-T035)

**Input**: Design documents from `/specs/005-research-skill-versioning/`  
**Status**: All tasks complete and committed (2026-07-14)

**Organization**: Tasks grouped by phase (T029-T031 backend encryption, T032 SemVer, T033-T034 frontend/marketing, T035 docs formalization).

---

## Phase 0: Backend Encryption & Skill Loading

### T029 - Skill Encryption Infrastructure
- [x] **Implement Fernet-based encryption** for skill methodology using existing token_vault machinery (ENCRYPTION_KEK).
- [x] **Create backend/app/services/skill_loader.py**: load_skill(), decrypt, cache plaintext, strip YAML frontmatter + MCP footer, fallback instruction.
- [x] **Update llm_service._build_prompt()** to inject decrypted skill into system message.
- [x] **Test**: Skill is decrypted on startup, cached, never returned to clients; fallback works if key missing.
- [x] **Code references**: `backend/app/services/skill_loader.py`, `backend/app/services/llm_service.py`, `backend/app/config.py`
- **Commit**: `c2e419f`

### T030 - Skill Artifact Encryption & Git Ignore
- [x] **Encrypt plaintext source** (`backend/app/skills/bd_lead_research.source.md`) → `backend/app/skills/bd_lead_research.md.enc` using current ENCRYPTION_KEK.
- [x] **Create .gitignore entry** for plaintext sources: `backend/app/skills/*.source.md`.
- [x] **Commit the .enc artifact** as the authoritative version (never plaintext in git).
- [x] **Verify**: Plaintext source is git-ignored; only .enc is tracked.
- [x] **Code references**: `backend/app/skills/bd_lead_research.md.enc`, `.gitignore`
- **Commit**: `c2e419f`

### T031 - Skill Re-encryption Script & Makefile Target
- [x] **Create scripts/encrypt_skill.py**: reads plaintext source from disk, encrypts with current ENCRYPTION_KEK, writes .enc artifact.
- [x] **Add Makefile target `make encrypt-skill`** that calls scripts/encrypt_skill.py; documents re-encryption workflow for production.
- [x] **Document**: Production deployment must run `make encrypt-skill` after setting real ENCRYPTION_KEK (see SECURITY.md §8).
- [x] **Test**: Script runs successfully; .enc artifact is valid Fernet ciphertext; skill_loader can decrypt it.
- [x] **Code references**: `scripts/encrypt_skill.py`, `Makefile`
- **Commit**: `c2e419f` (scripts/encrypt_skill.py + prompt wiring) and `ea3bc9a` (Makefile `encrypt-skill` target)

---

## Phase 1: SemVer Versioning

### T032 - SemVer Tooling (VERSION File + Makefile)
- [x] **Create VERSION file** at repo root (initial: "0.1.0") as single source of truth.
- [x] **Create scripts/sync_versions.py**: reads VERSION, updates `web/package.json`, `extension/manifest.json`, `backend/app/config.py` APP_VERSION.
- [x] **Create scripts/bump_version.py**: increments VERSION (patch/minor/major), calls sync_versions.py, stages CHANGELOG.md for editing.
- [x] **Create scripts/update_changelog.py**: adds new section to CHANGELOG under [Unreleased] (human edits expected).
- [x] **Add Makefile targets**:
  - `make version`: print current version
  - `make sync-versions`: sync VERSION to all components
  - `make bump-patch|minor|major`: increment version + sync + stage CHANGELOG
  - `make release`: commit version bump + create git tag vX.Y.Z
  - `make encrypt-skill`: re-encrypt skill (T031)
- [x] **Verify**: All components stay in sync; VERSION is the single source.
- [x] **Code references**: `VERSION`, `scripts/sync_versions.py`, `scripts/bump_version.py`, `scripts/update_changelog.py`, `Makefile`, `CHANGELOG.md` (Keep a Changelog format)
- **Commit**: `ea3bc9a`

### T033 - Web Footer Version Display
- [x] **Add version field to `/api/health` response**: `{"status":"ok","app_version":"0.1.0",...}`
- [x] **Update web/src/components/Footer.tsx** (or create if missing): fetch /api/health on mount, display version in footer.
- [x] **Verify**: Version displays correctly in web app footer; matches VERSION file.
- [x] **Code references**: `backend/app/main.py` (health endpoint), `web/src/components/Footer.tsx`
- **Commit**: `54d3c6e`

### T034 - Changelog Page
- [x] **Create web/src/components/Changelog.tsx**: fetch and render root CHANGELOG.md as a page component.
- [x] **Add /changelog route** in web/src/App.tsx with link in navigation.
- [x] **Markdown rendering**: Parse CHANGELOG.md and display (version sections, bullet points, code blocks).
- [x] **Verify**: /changelog page renders correctly; all versions visible.
- [x] **Code references**: `web/src/components/Changelog.tsx`, `web/src/App.tsx`, root `CHANGELOG.md`
- **Commit**: `54d3c6e`

---

## Phase 2: Documentation & Formalization

### T035 - Documentation & Spec Kit Formalization
- [x] **README.md**:
  - Add "BD Lead Research Engine" section: describe as proprietary, encrypted server-side, battle-tested; never exposed to clients.
  - Add "Versioning & Releases" section: document Makefile workflow (VERSION, bump, release, changelog, encrypt-skill).
  - Note version visibility (footer, /changelog, CHANGELOG.md).
- [x] **docs/ARCHITECTURE.md**:
  - Add "BD Lead Research Engine" subsection: describe encryption (Fernet), skill_loader, caching, fallback, injection into LLM prompt.
  - Note never in client bundles; server-only IP.
- [x] **.env.example**:
  - Update ENCRYPTION_KEK comment: note it also encrypts skill; mention `make encrypt-skill` for production.
- [x] **Create docs/SECURITY.md** (new file):
  - §1: User Authentication (Google OAuth + JWT)
  - §2: CRM Token Security (envelope encryption, vault, key mgmt)
  - §3: Skill IP Protection (encrypted at rest, server-only decryption, injection, versioning, fallback)
  - §4: LLM Keys & API Secrets (server-side, budget guards, tracking)
  - §5: Data Handling & Logging (what's logged, what's never logged)
  - §6: Data Retention & Deletion
  - §7: Threat Model & Mitigations
  - §8: Production Deployment Checklist (set ENCRYPTION_KEK, re-encrypt skill, set JWT_SECRET, enable HTTPS, etc.)
  - §9: Security Issue Reporting
- [x] **src/tool.ts**:
  - Light touch: update comment to reference "proprietary BD Lead Research Engine" (no content change).
- [x] **package.json**:
  - Update description: "... for proprietary BD Lead Research Engine" (consistent wording; no version change).
- [x] **Create specs/005-research-skill-versioning/** (Spec Kit formalization):
  - `spec.md`: user stories, requirements, success criteria, scope.
  - `plan.md`: summary, approach, architecture, sequencing, success definition.
  - `tasks.md` (this file): all T029-T035 tasks with commit hashes and completion notes.
- [x] **Verification**:
  - `npm run build` clean (web).
  - `python3 -c "import json; json.load(open('package.json'))"` passes.
  - `grep -rniE "buying signal scan|WHY THIS BEATS CLAUDE PRO|AGENCY SETUP|bitrix24_create_bd_lead" README.md docs/ specs/005-research-skill-versioning/` returns NOTHING (no skill content leaked).
- **Code references**: `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md` (new), `.env.example`, `src/tool.ts`, `package.json`, `specs/005-research-skill-versioning/`
- **Commit**: T035 is documentation only (no code changes); incorporated into this session via cumulative edits (not a separate git commit).

---

## Completion Summary

| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| T029 | ✅ Complete | c2e419f | Skill encryption backend + skill_loader + llm injection |
| T030 | ✅ Complete | c2e419f | Encrypt artifact, git-ignore source |
| T031 | ✅ Complete | ea3bc9a | Re-encryption script + Makefile target |
| T032 | ✅ Complete | ea3bc9a | SemVer: VERSION file, sync scripts, bump/release targets |
| T033 | ✅ Complete | 54d3c6e | Web footer version display + /api/health |
| T034 | ✅ Complete | 54d3c6e | Changelog page + /changelog route |
| T035 | ✅ Complete | This session | Documentation: README, ARCHITECTURE, SECURITY, .env.example, Spec Kit formalization |

---

## Next Steps

1. **Release v0.1.0**: Edit CHANGELOG.md with final polish, run `make release`, push tags.
2. **Production Deployment**: Follow SECURITY.md §8 checklist:
   - Set real ENCRYPTION_KEK (32+ bytes).
   - Run `make encrypt-skill` to re-encrypt with prod key.
   - Set JWT_SECRET, GOOGLE_CLIENT_ID/SECRET, real LLM keys.
   - Enable HTTPS, configure logging, set DEBUG=false.
   - Run smoke tests (scripts/e2e_smoke_t020.py).
3. **User Communication**: Announce "proprietary BD Lead Research Engine" as core differentiator in marketing materials + docs.
