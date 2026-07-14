# Feature Specification: Research Skill Versioning & Encryption

**Feature Branch**: `004-ai-bd-assistant` (continuous)  
**Created**: 2026-07-14  
**Status**: Implemented & Complete  
**Input**: Ship the BD Lead Research Engine as encrypted proprietary IP, version it with the app, and publicize it as a key differentiator.

## User Scenarios & Testing

### User Story 1 - Enterprise buyer sees proprietary research engine (Priority: P1)

As an enterprise buyer or investor evaluating the product, I visit the website and see that the research engine is proprietary, battle-tested, and kept as encrypted server-side IP. This is a clear differentiator from generic Claude/ChatGPT prompts. The fact that it's encrypted and never leaked to clients reassures me about IP protection.

**Why this priority**: Proprietary IP is the core selling point and switching cost. Non-technical buyers understand that versioning, encryption, and consistent methodology are hallmarks of mature products.

**Acceptance Scenarios**:
1. **Given** a prospect lands on the web app homepage or reads the docs, **When** they see the marketing copy, **Then** they understand the BD Lead Research Engine is proprietary, encrypted server-side, and never exposed.
2. **Given** the app is in production, **When** a new version is released, **Then** the version number is consistent across web footer, extension, backend API, CHANGELOG, and all components.
3. **Given** a developer deploying to production, **When** they follow the deployment guide, **Then** they re-encrypt the skill with the production encryption key and commit the artifact.

### User Story 2 - Changelog transparency (Priority: P1)

As an early user, I visit the `/changelog` page and see the full release history, including what changed in each version. This builds confidence in the product's stability and active maintenance.

**Why this priority**: Changelogs are standard practice for mature products. Builds trust.

### User Story 3 - Developer/Operator manages versioning workflow (Priority: P1)

As a developer or ops engineer, I use the Makefile to bump versions, encrypt the skill, and create releases without manual steps. The workflow is repeatable and error-proof.

**Why this priority**: Repeatable versioning reduces human error and supports CI/CD automation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST display the app version (from VERSION file) in the web app footer and via `/api/health` endpoint.
- **FR-002**: System MUST have a `/changelog` page in the web app that renders the root `CHANGELOG.md` file.
- **FR-003**: System MUST use a single source of truth (`VERSION` file) for versioning; all components (web, extension, backend) MUST be kept in lockstep.
- **FR-004**: System MUST provide a Makefile target `make bump-patch|minor|major` that updates VERSION, syncs all components, and stages CHANGELOG for editing.
- **FR-005**: System MUST provide a Makefile target `make release` that commits the version bump and creates a git tag.
- **FR-006**: System MUST encrypt the BD Lead Research skill methodology using Fernet (same `ENCRYPTION_KEK` as CRM tokens) and store only the `.enc` artifact in version control.
- **FR-007**: Plaintext skill source (`bd_lead_research.source.md`) MUST be git-ignored and never committed.
- **FR-008**: System MUST provide a `make encrypt-skill` target that re-encrypts the skill with the current `ENCRYPTION_KEK` (production deployment workflow).
- **FR-009**: System MUST inject the decrypted skill into the LLM prompt (server-side only) to shape the AI's reasoning.
- **FR-010**: The skill MUST never be returned to clients, never embedded in web/extension bundles, never in any API response.

### Non-Functional Requirements

- **NFR-001**: The Makefile workflow MUST complete in under 5 seconds (excluding git operations).
- **NFR-002**: Version numbers MUST follow Semantic Versioning (MAJOR.MINOR.PATCH).
- **NFR-003**: The CHANGELOG format MUST follow [Keep a Changelog](https://keepachangelog.com/).
- **NFR-004**: Production deployment MUST enforce setting a real `ENCRYPTION_KEK` before the skill is usable.
- **NFR-005**: If skill decryption fails, the app MUST remain operational (fallback to minimal instruction; LLM output is suboptimal but not broken).

## Success Criteria

- A new user can view the app version in the footer and changelog via `/changelog`.
- A developer can run `make bump-patch`, edit CHANGELOG, and `make release` to create a new version with zero manual version updates.
- All components (web package.json, extension manifest.json, backend config.py, VERSION file) stay in perfect sync.
- The skill is encrypted at rest; plaintext source is never committed.
- Production deployment includes re-encryption of the skill with the deployment key.
- Marketing copy describes the skill as proprietary and encrypted; no skill content is leaked.
- Smoke test: `/api/health` returns `app_version` matching VERSION file; web footer displays it.

## Scope

**In Scope (MVP slice)**:
- Single VERSION file as source of truth.
- Makefile targets: bump-patch/minor/major, release, encrypt-skill.
- CHANGELOG.md (Keep a Changelog format).
- Version sync to web/package.json, extension/manifest.json, backend/app/config.py.
- Encrypted skill artifact + git-ignore plaintext.
- Web footer version display + `/changelog` page.
- Marketing copy in README (proprietary BD Lead Research Engine).
- Production deployment checklist (SECURITY.md).

**Out of Scope (P2+)**:
- Automated CI/CD pipeline to publish releases to stores (Chrome Web Store, etc.).
- Rollback automation.
- A/B testing of skill versions (future T036+).
- Multi-language/region versioning.

## Data & Assumptions

- Skill source changes are rare (manual, curated improvements).
- Encryption key rotation is infrequent (annual or on compromise).
- Early users are tech-savvy (can handle git tags, env vars).
- Production deployments are manual or via custom CI/CD (not yet fully automated).
