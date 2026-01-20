# PRD: Bug Fixes and QA Improvements

## Introduction

The chat application is experiencing 500 errors due to a `TypeError` in `create_react_agent`. Additionally, the user wants to improve code quality by adding more tests and enforcing checks via pre-commit. This PRD outlines the plan to fix the critical bug and establish a robust QA foundation.

## Goals

- Fix the `create_react_agent` TypeError immediately.
- Prevent regression by adding pre-commit hooks.
- Improve test coverage with validation tests.

## User Stories

### US-001: Fix create_react_agent TypeError
**Description:** As a user, I want the chat to work without 500 errors, so I can use the agent.
**Acceptance Criteria:**
- [ ] Investigate valid arguments for `create_react_agent` in the installed version.
- [ ] Update `backend/src/sub_agents/infoblox.py` (and others) to pass the system prompt correctly.
- [ ] Manual test: Verify chat runs without TypeError.
- [ ] Typecheck passes.

### US-002: Add Pre-commit Hooks
**Description:** As a developer, I want pytest and mypy to run before commit, so I don't break the build.
**Acceptance Criteria:**
- [ ] Add `.pre-commit-config.yaml` with `pytest` and `mypy` hooks.
- [ ] Ensure `mypy` runs in strict mode or consistent with current usage.
- [ ] Verify `pre-commit run --all-files` passes (or fix existing issues).
- [ ] Typecheck passes.

### US-003: Add Agent Integration Tests
**Description:** As a developer, I want to confirm that agents load and respond correctly, so I can catch issues like the `TypeError` earlier.
**Acceptance Criteria:**
- [ ] Add integration tests in `backend/tests/test_agents.py`.
- [ ] Test instantiation of all agents (Orchestrator, ACI, Infoblox, Palo Alto, Triage).
- [ ] Mock LLM calls to verify agent graph structure and prompt loading.
- [ ] All tests pass.
- [ ] Typecheck passes.

## Functional Requirements

- FR-1: Chat must not crash with TypeError on instantiation.
- FR-2: `git commit` must trigger linting/testing.
- FR-3: Tests must validate agent graph construction.

## Non-Goals

- Refactoring the entire agent architecture.
- Adding new features to agents (just validation).

## Checklist
- [x] Asked clarifying questions (Implicitly answered by user request + error log)
- [x] User stories are small
- [x] Verifiable criteria
