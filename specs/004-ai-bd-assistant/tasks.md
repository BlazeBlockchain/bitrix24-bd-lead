---

description: "Task list template for feature implementation"
---

# Tasks: AI-Native BD Lead Assistant

**Input**: Design documents from `/specs/004-ai-bd-assistant/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md (and the root docs/CONCEPT.md etc.)

**Organization**: Tasks grouped to enable independent slices (aligns with P1 stories in spec.md and FEATURES.md).

## Format: `[ID] [P?] [Story] Description`

## Phase 0 / Foundation

- [ ] **T001** Refactor current `src/client.ts` into `CrmClient` interface + `src/crm/bitrix24.ts` adapter (preserve behavior). Create TypeScript + Python interface definitions.
- [ ] **T002** [P] Implement `HubspotClient` adapter (createContact, createDeal with associations, createTask with hs_timestamp). Place in appropriate backend adapters dir per plan.md.
- [ ] **T003** Add provider selector / factory for CrmClient (Bitrix24 default for back-compat).

## Backend (US1 core)

- [ ] **T004** Set up FastAPI project skeleton (or extend existing) with Docker, Alembic, basic health endpoint. Mirror vanguard-game structure.
- [ ] **T005** Implement Google OAuth + JWT auth service (login, /me, protected dependency). Store minimal user record.
- [ ] **T006** Implement encrypted CRM token vault (envelope encryption) + connect endpoints for webhook (Bitrix) and OAuth (HubSpot).
- [x] **T007** LLM proxy service: Gemini 2.5 Flash primary with Haiku fallback, prompt builder that injects user memory context, structured JSON output, per-user budget guards + logging. (Implemented in backend/app/services/llm_service.py + integrated in lead_service + /enrich; mocks + budget + usage_ledger stub. See BUILD_COORDINATION + REVIEW_FOR_T007.md)
- [ ] **T008** Lead orchestration service that reuses/refactors logic from `src/tool.ts` (contact → deal → 3 tasks) using the CrmClient.
- [ ] **T009** Postgres models + migrations for User, Lead, CrmConnection, MemoryProfile, OutreachHistory (see data-model.md).
- [ ] **T010** [P] Basic REST API for enrich + push + history.

## Web App (US1 + US2)

- [ ] **T011** Scaffold React + Vite (or Next.js) app with auth interceptor (JWT), API client, protected routes. Mirror vanguard frontend patterns (Zustand, Layout).
- [ ] **T012** Connections page + flows (paste webhook + test, HubSpot OAuth button).
- [ ] **T013** Lead Composer page: form, "Generate with AI" (calls enrich), split preview pane showing snapshot/opener/tasks, Push button.
- [ ] **T014** History page: list + detail of past leads, "use similar" action.
- [ ] **T015** Basic Dashboard + usage display.

## Browser Extension (US2)

- [ ] **T016** MV3 extension scaffold (manifest, popup UI, service worker).
- [ ] **T017** Thin client: call backend enrich/push using stored JWT or token. Host detection for pre-fill (best effort).
- [ ] **T018** Options page linking to web dashboard.

## Cross-cutting & Verification

- [ ] **T019** Update MCP server (`src/index.ts` + tool) to use shared CrmClient/core (or proxy to new backend during transition).
- [ ] **T020** End-to-end smoke tests / scripts against Bitrix24 and HubSpot sandboxes (create 1 lead → verify 1 contact + 1 deal + 3 tasks).
- [ ] **T021** Docker Compose setup (db, redis, backend, web) + .env.example updates.
- [ ] **T022** Update root README with new flows + link to specs/004-ai-bd-assistant.
- [ ] **T023** Security note (token handling, LLM keys, budgets) + basic logging.

## Later / Polish (P2+)

- [ ] Memory profile editor / visible tone samples.
- [ ] Usage ledger + simple admin views.
- [ ] Full test coverage for adapters and orchestration.
- [ ] Extension store submission assets (screenshots, description).

See plan.md for sequencing and the original project_agents_tasks.md + approved session plan for more context.

**Next**: Run speckit-tasks (or manually refine), then begin with T001 (CrmClient refactor) using senior-architect + senior-backend.
  
  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure
- [ ] T009 Setup environment configuration management

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Entity1] model in src/models/[entity1].py
- [ ] T013 [P] [US1] Create [Entity2] model in src/models/[entity2].py
- [ ] T014 [US1] Implement [Service] in src/services/[service].py (depends on T012, T013)
- [ ] T015 [US1] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T016 [US1] Add validation and error handling
- [ ] T017 [US1] Add logging for user story 1 operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T021 [US2] Implement [Service] in src/services/[service].py
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T027 [US3] Implement [Service] in src/services/[service].py
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
