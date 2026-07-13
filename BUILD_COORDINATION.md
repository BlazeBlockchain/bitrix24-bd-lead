# AI-Native BD Lead Assistant - Agentic Build Coordination

**Feature Branch**: 004-ai-bd-assistant  
**Current Date**: 2026-07-14  
**Overall Goal**: Build backend (Python FastAPI + memory + LLM proxy), web app (React), browser extension (MV3), with shared CrmClient. Grounded in docs/CONCEPT.md, ARCHITECTURE.md, FEATURES.md, UI_UX.md and specs/004-ai-bd-assistant/.

**Speckit Status**: spec.md, plan.md, tasks.md, data-model.md, research.md, quickstart.md, contracts/ in place and committed.

## Current Focus / Active Task
**T001 (Foundation - P1)**: Refactor current `src/client.ts` into `CrmClient` interface + `src/crm/bitrix24.ts` adapter (preserve exact existing behavior for Bitrix24). Also create parallel TypeScript + Python interface definitions for future backend.

**Why first**: This is the contract that *all* future work (HubSpot adapter, backend orchestration, web, extension, MCP) will depend on. Breaking changes here will cascade. Must be stable before T002/T008 etc.

**Status**: Starting - Implementer agent dispatched.
**Files expected to change**:
- src/client.ts → split/move logic
- New: src/crm/types.ts (or contracts shared)
- New: src/crm/bitrix24.ts (adapter impl)
- Updates to src/tool.ts and src/index.ts (minimal, to use new interface)
- Possibly docs or tests if behavior verified

## Agent Roles & Current Assignments
- **Implementer Agent**: Writes code, follows plan + tasks + contracts exactly. Updates BUILD_COORDINATION.md with "What I built", "Files touched", "Decisions made", "Open questions for others". Works in isolated worktree when possible. Produces clean, documented changes.
- **Reviewer / Scrutinizer Agent**: Reviews Implementer's output (diffs, worktree, BUILD_COORDINATION updates). Checks for:
  - Breaking changes to existing MCP behavior
  - Violations of ARCHITECTURE (e.g. no client-side secrets, CrmClient abstraction correct)
  - Inconsistencies with data-model, contracts/crm-client.md
  - Future-proofing for Python backend and web/extension
  - Code quality, types, error handling
  Writes review notes + suggested patches back into a REVIEW_NOTES.md or directly comments in coordination. Gives concrete "changes to implement" back to Implementer.
- **Tester / Committer Agent**: Runs tests (unit, integration smoke if possible), verifies no breakage (e.g. existing Bitrix24 flow still works), runs builds, lints. If green, prepares commit message. Also maintains shared state. Uses check-work skill where possible.

**Information Sharing Rule (mandatory for all agents)**:
- Every agent **MUST** read BUILD_COORDINATION.md at start of its work.
- Every agent **MUST** append to BUILD_COORDINATION.md:
  - Timestamp + Agent role
  - Summary of what was done / reviewed / tested
  - Exact files modified + why
  - Any interfaces/contracts changed (with before/after)
  - Decisions made that affect others
  - Blockers or questions for other agents
- Use `resume_from` when continuing a previous agent's conversation.
- Never assume; always re-read current coordination + relevant specs before editing code.

## Key Decisions & Constraints (do not violate)
- Preserve 100% backward compat for current Bitrix24 MCP tool (src/tool.ts + client).
- CrmClient interface from contracts/crm-client.md is source of truth (start with TS version).
- No new heavy deps in the MCP src/ layer if possible.
- Backend will later duplicate interface in Python (FastAPI).
- All CRM calls go through CrmClient (no direct calls elsewhere).
- Memory/LLM/auth come later (after this foundation).
- Use native fetch where possible (current style).
- Follow vanguard patterns where applicable for new code.

## Build Loop Process
1. Implementer works on current task in worktree or main (documented).
2. Reviewer reviews, writes detailed feedback + exact change suggestions.
3. Implementer incorporates review feedback.
4. Tester runs verification, builds, basic tests. If pass → commit (or prepare PR).
5. Update coordination, pick next task (or continue loop on same if issues).
6. All agents stay in sync via this file + the specs/ docs.

## Task Progress
- [ ] T001: CrmClient refactor (current)
- [ ] T002: HubSpot adapter
- ... (see tasks.md)

**Last Updated**: 2026-07-14 (initial setup after commit of specs)

- **2026-07-14  [Coordinator / Main]** Committed Speckit artifacts. Created this BUILD_COORDINATION.md. Dispatched Implementer for T001. All future agents must read this file + specs/004-ai-bd-assistant/* before any code changes.

---
**Agents: Always append your work log below this line. Read everything above first.**
