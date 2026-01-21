# PRD: Sub-Agent Tabbed Interface

## Introduction

Refactor the frontend to display sub-agent activity in dedicated tabs instead of bloating the orchestrator's chat window. Currently, all thought events from multiple sub-agents (ACI, Infoblox, Palo Alto, Triage) are shown inline, making it difficult to follow the orchestrator's flow. This feature introduces a tabbed interface where:

- **Orchestrator view** shows only high-level status ("CALLING SUB-AGENT: ACI ✅")
- **Each sub-agent** gets its own tab with full detail (chain events, tool calls, outputs)
- **Tabs clear** when starting a new conversation

## Goals

- Declutter the orchestrator chat window by showing only sub-agent status indicators
- Provide detailed sub-agent visibility via dedicated tabs
- Show real-time updates as sub-agents execute
- Polish the UI with modern styling and smooth animations
- Improve user experience when debugging or monitoring agent behavior

## User Stories

### US-001: Add tab container component
**Description:** As a user, I want a tab container in the UI so I can switch between the orchestrator and individual sub-agent views.

**Acceptance Criteria:**
- [ ] Add a tab container using Streamlit's `st.tabs()` component
- [ ] Default tab is "Orchestrator" showing the main chat
- [ ] Tabs are created dynamically when sub-agents are called
- [ ] Tab order: Orchestrator, then sub-agents in order of first call
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-002: Create sub-agent tab on first call
**Description:** As a user, I want a new tab created automatically when a sub-agent is first called, so I can view its activity.

**Acceptance Criteria:**
- [ ] When `chain_start` event received for a new node, create a tab for it
- [ ] Tab label shows agent name (e.g., "ACI", "Infoblox", "Palo Alto", "Triage")
- [ ] Skip creating tabs for the orchestrator node itself
- [ ] Session state tracks which tabs have been created
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-003: Display sub-agent call status in orchestrator
**Description:** As a user, I want the orchestrator view to show minimal status when sub-agents are called, without full details.

**Acceptance Criteria:**
- [ ] On `chain_start` for sub-agent: display "🔄 CALLING SUB-AGENT: {name}"
- [ ] On `chain_end` for sub-agent: update to "✅ {name} Complete"
- [ ] Include clickable indicator or visual hint that tab exists
- [ ] Status updates appear inline in the thinking expander
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-004: Route thought events to correct tab
**Description:** As a user, I want each sub-agent's thought events routed to its corresponding tab.

**Acceptance Criteria:**
- [ ] Thought events (chain_start, tool_start, chain_end) for a sub-agent appear in its tab
- [ ] Each tab maintains its own scrollable log
- [ ] Events include status icons (🔄 start, 🔧 tool, ✅ end)
- [ ] Events show timestamps
- [ ] Tool events show tool name and input summary
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-005: Clear tabs on new conversation
**Description:** As a user, I want tabs to be cleared when I start a new conversation so the interface is fresh.

**Acceptance Criteria:**
- [ ] "Clear History" button also clears all sub-agent tabs
- [ ] New conversation starts with only "Orchestrator" tab visible
- [ ] Session state for tabs is properly reset
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-006: Add styling and animations
**Description:** As a user, I want the tab interface to look polished with modern styling and smooth transitions.

**Acceptance Criteria:**
- [ ] Custom CSS for tab styling (colors matching app theme)
- [ ] Loading animation/spinner in tab when sub-agent is active
- [ ] Smooth scroll for thought event logs
- [ ] Green dot indicator on tab when new activity occurs (no auto-focus)
- [ ] Responsive layout that works on different screen sizes
- [ ] Typecheck passes
- [ ] Verify in browser

---

### US-007: Update session state management
**Description:** As a developer, I want proper session state management for the tabbed architecture.

**Acceptance Criteria:**
- [ ] Add `st.session_state.agent_tabs` dict to track: `{agent_name: {created: bool, logs: list, status: str}}`
- [ ] Add `st.session_state.active_tab` to track currently selected tab
- [ ] Ensure state persists correctly during Streamlit reruns
- [ ] Handle edge cases (rapid events, missing agents)
- [ ] Typecheck passes

---

### US-008: Add unit tests for tab logic
**Description:** As a developer, I want tests that verify the tab creation and event routing logic.

**Acceptance Criteria:**
- [ ] Test: tab created on first chain_start for new agent
- [ ] Test: events routed to correct agent's log
- [ ] Test: orchestrator status shows correct format
- [ ] Test: clear history resets all tab state
- [ ] All tests pass
- [ ] Typecheck passes

## Functional Requirements

- FR-1: The UI must use Streamlit's `st.tabs()` for the tab container
- FR-2: When a sub-agent `chain_start` event is received, create a tab if it doesn't exist
- FR-3: The orchestrator tab must show only "CALLING SUB-AGENT: X" and "X Complete" messages
- FR-4: Each sub-agent tab must display all thought events (chain_start, tool_start, chain_end) with full details
- FR-5: Tab state must be stored in `st.session_state` and cleared on "Clear History"
- FR-6: Events must include timestamps, status icons, and tool input summaries
- FR-7: The UI must include custom CSS for modern styling
- FR-8: The interface must handle rapid sequential events without race conditions

## Non-Goals

- No persistent storage of sub-agent logs across browser sessions
- No export/download functionality for logs
- No backend changes to the SSE event format (use existing schema)
- No filtering or search within sub-agent tabs
- No separate page/route for sub-agents (all within same Streamlit page)

## Design Considerations

**Tab Layout (Streamlit Best Practices):**
- Use `st.tabs()` horizontal tab component at top of main content area
- Orchestrator tab contains the chat input and message history
- Sub-agent tabs contain scrollable log containers
- Consider `st.container()` with fixed height for log scrolling

**Visual Design:**
- Match existing dark/light theme of the app
- Use consistent iconography (🔄 🔧 ✅ for status)
- Subtle animation for "thinking" state
- Tab badges or highlights for new activity

## Technical Considerations

- Streamlit reruns the entire script on each interaction; state must be in `st.session_state`
- SSE events arrive asynchronously; use Streamlit's streaming patterns
- The existing `thought_expander` can be replaced with tab-based routing
- Consider using `st.empty()` containers for real-time updates within tabs
- May need CSS injection via `st.markdown()` for custom styling

## Success Metrics

- Orchestrator chat window shows < 5 lines per sub-agent call (vs current unbounded)
- User can view full sub-agent detail by clicking its tab
- No performance regression in SSE processing
- UI remains responsive during multi-agent workflows

## Resolved Design Decisions

- **Auto-focus:** Tabs do NOT auto-focus; instead, a green dot indicator appears on the tab when new activity occurs
- **Log display:** Show full log in each tab (no collapsed summary)
- **Max tabs:** No limit on number of tabs
