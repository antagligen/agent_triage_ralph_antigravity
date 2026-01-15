# PRD: Frontend Streamlit Interface

## Introduction

Create a user-friendly frontend interface using Streamlit for the AI Troubleshooting Agent. This frontend will communicate with the backend via HTTP and provide a chat interface with real-time streaming of agent thoughts and responses. It will also include configuration management.

## Goals

- Provide a simple chat interface for users.
- Visualize the agent's thought process (streaming events).
- Allow configuration of available LLMs and sub-agents.
- Decouple frontend from backend using a microservices architecture.

## User Stories

### US-F001: Chat Interface with Streaming
**Description:** As a user, I want to type messages and see the agent's response stream in real-time, including internal thoughts.
**Acceptance Criteria:**
- [ ] Chat input field at the bottom.
- [ ] Chat history display.
- [ ] Real-time rendering of markdown responses.
- [ ] "Thought" expanders or distinct UI elements for `event: thought`.
- [ ] "Routing" indicators for `event: routing` (e.g., "Switching to Network Specialist...").

### US-F002: Configuration Management
**Description:** As a user, I want to configure the agent settings without editing files.
**Acceptance Criteria:**
- [ ] Sidebar or separate tab for settings.
- [ ] Dropdown to select Orchestrator Model (e.g., gpt-4, gpt-3.5).
- [ ] Toggle/Select for active Sub-Agents.
- [ ] Save button that updates the backend configuration (requires backend config update endpoint or re-init).
    *Note: If backend doesn't support dynamic config update yet, this might just be local session config or require backend restart - clarify in implementation.*

### US-F003: Sub-Agent Visualization
**Description:** As a user, I want to see which sub-agent is currently active.
**Acceptance Criteria:**
- [ ] Visual indicator of active agent in the chat stream.

## Functional Requirements

1.  **Communication**: Use `requests` or `aiohttp` to POST to `http://backend:8000/chat`.
2.  **Streaming**: Handle SSE (Server-Sent Events) from the backend.
3.  **State**: Maintain chat history in `st.session_state`.

## Tech Stack
-   **Framework**: Streamlit
-   **Containerization**: Docker

## Out of Scope
-   Authentication (for now).
-   Persistent database storage (chat history is session-only).
