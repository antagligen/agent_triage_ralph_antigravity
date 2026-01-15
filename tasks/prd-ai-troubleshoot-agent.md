# PRD: AI Troubleshooting Agent Backend

## Introduction

Create a backend service using FastAPI that serves as an intelligent troubleshooting assistant. The system features an Orchestrator Agent that analyzes user prompts and routes them to specialized Sub-Agents (e.g., a Cisco ACI expert) to resolve queries. The architecture is designed to be highly configurable and observable, with streaming capabilities to expose the AI's thought process.

## Goals

-   **Orchestration:** Implement a main agent that uses an LLM to decide which sub-agent to invoke.
-   **Modular Sub-Agents:** Support a registry of specialized agents, implemented as LangGraph nodes.
-   **Full Configurability:** Control agent behavior (models, prompts, temperatures, active tools) via an external configuration file.
-   **Observability:** Stream the orchestrator's decision-making process and sub-agent responses to the client (enabling future frontend integration).

## User Stories

### US-001: Core API & Configuration Infrastructure
**Description:** As a developer, I want a FastAPI service that loads agent configurations from a file so I can adjust behavior without changing code.

**Acceptance Criteria:**
-   [ ] FastAPI project structure created.
-   [ ] Configuration loader implemented (supports YAML/JSON).
-   [ ] Configuration file defines:
    -   Orchestrator model & system prompt.
    -   List of Sub-Agents (enabled/disabled status, specific models, system prompts).
    -   Tool definitions for each agent.
-   [ ] Typecheck passes.

### US-002: Orchestrator Agent with LangGraph
**Description:** As a user, I want the system to understand my request and automatically select the correct expert agent.

**Acceptance Criteria:**
-   [ ] Orchestrator implemented as a LangGraph node.
-   [ ] Orchestrator analyzes user input and selects "Next Node" (Sub-Agent) or responds directly if no expert is needed.
-   [ ] Routing logic involves LLM decision making (not just regex).
-   [ ] Verify in browser (simulate API call).

### US-003: Cisco ACI Troubleshooting Sub-Agent
**Description:** As a network engineer, I want a specialized agent that can query and troubleshoot Cisco ACI structures.

**Acceptance Criteria:**
-   [ ] "Cisco ACI" sub-agent node implemented.
-   [ ] Agent has access to mocked/stubbed ACI tools (or real ones if credentials provided).
-   [ ] Agent receives context from Orchestrator and returns troubleshooting steps/data.
-   [ ] Configurable via the main config file (US-001).

### US-004: Streaming Thoughts and Responses
**Description:** As a user (or frontend developer), I want to see the "thoughts" of the agent in real-time to know it wasn't stuck.

**Acceptance Criteria:**
-   [ ] API endpoint returns a `StreamingResponse`.
-   [ ] Stream includes structured events: `{"type": "thought", "content": "..."}`, `{"type": "response", "content": "..."}`.
-   [ ] Orchestrator routing decisions are streamed.
-   [ ] Sub-agent tool executions/thoughts are streamed.

## Functional Requirements

-   **FR-1:** The service must utilize FastAPI.
-   **FR-2:** The architecture must use LangGraph for managing agent state and transitions.
-   **FR-3:** Agent Configuration must be decoupled from code (e.g., `agents_config.yaml`).
-   **FR-4:** The Orchestrator must support "handoffs" to sub-agents.
-   **FR-5:** The API must support Server-Sent Events (SSE) or line-delimited JSON for streaming.

## Non-Goals

-   Frontend UI implementation (this is a backend-only deliverable for now).
-   Production-ready Cisco ACI integration (mocks/stubs are acceptable for the initial framework verification).
-   User Authentication/Authorization (can be added later).

## Technical Considerations

-   **Framework:** FastAPI + Uvicorn.
-   **Agent Framework:** LangChain / LangGraph.
-   **Configuration:** Pydantic is recommended for validating the config file.
-   **Streaming:** Use Python's `async generator` pattern for the streaming response.

## Success Metrics

-   A user can change the Orchestrator's model from GPT-4o to GPT-3.5 via config file and see the change on restart.
-   Asking "Troubleshoot the tenant X on fabric Y" correctly routes to the Cisco ACI agent.
-   The stream output clearly shows: User Request -> Orchestrator Thought -> Route to ACI -> ACI Agent Thought -> Final Response.

## Open Questions

-   What specific "Tools" should the Cisco ACI agent start with? (Will assume a basic "query_tenant" and "check_health" tool for now).
