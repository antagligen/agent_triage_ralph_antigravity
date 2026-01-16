# PRD: Backend Refactoring & Documentation

## Introduction
Refactor `backend/src/main.py` to act as a lightweight entrypoint by moving business logic (streaming handling, data models) to dedicated modules. Additionally, embed a visual representation of the LangGraph logic directly in the code for better maintainability and understanding.

## Goals
- Simplify `backend/src/main.py` to primarily handle routing and dependency injection.
- Modularize code by separating streaming logic and Pydantic schemas.
- Visualize the agentic decision tree within the codebase.

## User Stories

### US-001: Extract Streaming Logic
**Description:** As a developer, I want the SSE streaming logic moved out of `main.py` into a dedicated module so that `main.py` remains focused on routing.

**Acceptance Criteria:**
- [ ] Create `backend/src/streaming.py`.
- [ ] Move `stream_graph_events` function to `backend/src/streaming.py`.
- [ ] Ensure all necessary imports (json, asyncio, etc.) are present in the new file.
- [ ] Typecheck passes.

### US-002: Extract Schemas
**Description:** As a developer, I want request/response models in their own module to keep the entrypoint clean.

**Acceptance Criteria:**
- [ ] Create `backend/src/schemas.py`.
- [ ] Move `ChatRequest` class (and any future models) to `backend/src/schemas.py`.
- [ ] Update `main.py` to import `ChatRequest`.
- [ ] Typecheck passes.

### US-003: Refactor Main Entrypoint
**Description:** As a developer, I want `backend/src/main.py` to simply compose imports and define routes.

**Acceptance Criteria:**
- [ ] Refactor `/chat` endpoint in `main.py` to use the new `streaming.py` and `schemas.py` modules.
- [ ] Ensure `config` loading logic is clean (keep `get_config` dependency injection, but ensure it's minimal).
- [ ] Verify application startup works (`uvicorn src.main:app`).
- [ ] Verify `/chat` endpoint functions correctly with the frontend.
- [ ] Typecheck passes.

### US-004: Add Graph Diagram
**Description:** As a developer, I want a Mermaid diagram illustrating the LangGraph decision tree embedded in the code documentation.

**Acceptance Criteria:**
- [ ] Create a Mermaid state diagram representing the `orchestrator` -> `network_specialist` / `direct_response` flow.
- [ ] Add this diagram to the module-level docstring (or `build_graph` docstring) in `backend/src/orchestrator.py`.
- [ ] Ensure the diagram accurately reflects the logic in `backend/src/orchestrator.py`.

## Functional Requirements
- FR-1: `backend/src/main.py` must not contain the implementation of `stream_graph_events`.
- FR-2: `backend/src/main.py` must not contain the definition of `ChatRequest`.
- FR-3: The API contract (endpoints, request/response formats) must remain exactly the same.
- FR-4: Source code must contain a Mermaid diagram of the agent graph.

## Non-Goals
- Changing the actual behavior of the agent or orchestrator.
- Adding new features to the frontend.
- Changing the configuration file format.

## Technical Considerations
- Ensure circular imports are avoided when splitting files.
- The `streaming.py` module will need to import `json` and `langchain_core` related types.

## Open Questions
- None.
