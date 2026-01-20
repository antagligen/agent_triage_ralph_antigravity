# PRD: Sub-Agent Thought Streaming

## Introduction
Currently, the system only streams the orchestrator's initial decision and the final result. Users cannot see the internal progress of sub-agents (e.g., "Checking Infoblox", "Running Diagnostics"), making the system feel unresponsive during long operations. This feature aims to stream sub-agent life-cycle events and tool executions to the frontend to improve transparency.

## Goals
-   **Visibility**: Provide real-time (chunked) visibility into sub-agent activities.
-   **Granularity**: Emit events for Agent Entry, Tool Calls, and Agent Exit.
-   **UX**: Support an "Expandable Details" UI pattern by structuring data appropriately.
-   **Performance**: Use chunked updates (not token-by-token) to minimize overhead.

## User Stories

### US-001: Enable Deep Streaming in Backend
**Description**: As a developer, I want the LangGraph orchestrator to stream internal events from sub-agents so that the frontend can display progress.
**Acceptance Criteria**:
- [ ] Update `streaming.py` to use `astream_events` (or equivalent) to capture inner node execution.
- [ ] Filter events to capture:
    -   `on_chain_start` (entering a sub-agent node)
    -   `on_tool_start` (specific tool being called)
    -   `on_chain_end` (sub-agent finishing)
- [ ] Ensure events contain the Agent Name and relevant Status Message.
- [ ] Typecheck passes.

### US-002: Standardize SSE Event Format
**Description**: As a frontend developer, I need a consistent JSON structure for "thought" events to render them correctly.
**Acceptance Criteria**:
- [ ] Define JSON schema for `event: thought`:
    ```json
    {
      "node": "infoblox_agent",
      "status": "tool_start",
      "message": "Calling get_host_by_ip with ip=192.168.1.5",
      "timestamp": "..."
    }
    ```
- [ ] Update `streaming.py` to transform LangGraph events into this schema.
- [ ] Verify using `curl` or manual test script that events are emitted correctly.

### US-003: Update Frontend to Display Reasoning (Optional/Placeholder)
**Description**: As a user, I want to see a "Show Reasoning" toggle that lists the steps the agent is taking.
**Acceptance Criteria**:
- [ ] (If applicable to current scope) Parse new `thought` events.
- [ ] Render a collapsed-by-default detail view for each agent step.
- [ ] Update status indicator in real-time (e.g., "Infoblox: Running...").
- [ ] Verify in browser.

## Functional Requirements
-   **FR-1**: The backend MUST stream an event when a sub-agent node is entered.
-   **FR-2**: The backend MUST stream an event when a tool is invoked, including the tool name.
-   **FR-3**: The stream MUST NOT include raw sensitive data unless necessary (keep logs to "Status Only" level as requested).
-   **FR-4**: Updates should be chunked (per step), not streaming raw tokens.

## Technical Considerations
-   **LangGraph `astream_events`**: This is the standard way to get nested graph events. We need to ensure we filter out noise (internal LangChain events) and only emit high-level "logical" steps.
-   **Event filtering**: We only care about `node` transitions and `tool` executions.

## Success Metrics
-   User sees "Checking [Agent]..." immediately when the orchestrator hands off.
-   No "dead air" (silence) for more than 2 seconds during execution.
