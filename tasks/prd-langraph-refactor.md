# PRD: AIOps Backend Refactor - LangGraph Orchestration

## 1. Introduction
Refactor the existing linear AIOps backend (FastAPI + Linear Chains) into a robust, event-driven architecture using **LangGraph**. The new system will utilize a **Supervisor-Worker pattern** to enable parallel tool execution, strict state management, and improved diagnosis accuracy.

The current linear approach is slow (sequential) and prone to context pollution. This refactor aims to decouple "Data Fetching" (Sub-Agents) from "Reasoning" (Orchestrator/Triage) to improve speed and reliability.

## 2. Goals
- **Reduce Latency:** Implement parallel execution for Sub-Agents (Cisco, Palo Alto, Infoblox) to cut wait times by ~50%.
- **Improve Accuracy:** Enforce strict Pydantic data contracts to prevent hallucinations and context pollution.
- **Resilience:** Handle partial tool failures gracefully without crashing the entire analysis pipeline.
- **Observability:** Persist full "Raw Data" logs to the database while only exposing "Summaries" to the LLM.

## 3. User Stories

### US-001: Orchestrator Validation & Planning
**Description:** As the System, I need to validate user inputs before calling expensive agents so that I don't waste resources on invalid queries.
**Acceptance Criteria:**
- [ ] Orchestrator analyzes initial request for critical fields (e.g., `source_ip`, `dest_ip`).
- [ ] If fields are missing, Orchestrator routes to `infoblox_agent` first.
- [ ] If fields are present, Orchestrator routes directly to Sub-Agents.
- [ ] Orchestrator outputs a structured `OrchestratorDecision` object.

### US-002: Parallel Agent Execution
**Description:** As a User, I want network checks (ACI, Palo Alto, ISE) to run simultaneously so that I get my answer faster.
**Acceptance Criteria:**
- [ ] Sub-Agents defined in `OrchestratorDecision.next_steps` execute in parallel (async).
- [ ] State graph supports "Fan-Out" (1 -> Many) and "Fan-In" (Many -> 1) flow.
- [ ] Total execution time is determined by the slowest agent, not the sum of all agents.

### US-003: Sub-Agent Data Hygiene
**Description:** As a Developer, I want agents to separate "Reasoning" from "Raw Logs" so that the context window doesn't overflow.
**Acceptance Criteria:**
- [ ] All Sub-Agents return a `SubAgentResult` Pydantic model.
- [ ] `raw_data` field contains the full JSON/Log output (saved to State, hidden from Supervisor).
- [ ] `summary` field contains a <50 word text summary (visible to Supervisor).
- [ ] `status` field clearly indicates SUCCESS, FAILURE, or PARTIAL.

### US-004: Triage Diagnosis
**Description:** As a User, I want a root cause analysis based on the aggregated data so that I know what to fix.
**Acceptance Criteria:**
- [ ] Triage Agent receives only the `summary` and `reasoning` from all Sub-Agents.
- [ ] Triage Agent generates a `TriageReport` containing: Root Cause, Technical Details, and Recommended Action.
- [ ] If partial failures occurred (e.g., Palo Alto failed), the report explicitly mentions data is incomplete.

### US-005: State Persistence
**Description:** As an SRE, I want to see the raw logs from a diagnosis later so that I can verify the AI's findings.
**Acceptance Criteria:**
- [ ] Full `IncidentState` (including `raw_data`) is persisted to the database upon completion.
- [ ] API response to Frontend includes the `TriageReport` text.

## 4. Functional Requirements

### FR-1: Supervisor Logic (Orchestrator)
- **FR-1.1:** Must use `ChatOpenAI(model="gpt-4o")` (or equivalent) with structured output.
- **FR-1.2:** Must implement a loop limit (recursion limit) of 10 to prevent infinite planning loops.
- **FR-1.3:** Must support an `escalate_to_human` decision path if validation fails 2+ times.

### FR-2: Agent Interfaces
- **FR-2.1:** All Sub-Agents must implement the `SubAgentResult` schema.
- **FR-2.2:** Sub-Agents must treat 4xx/5xx API errors as "Soft Failures" (Status: FAILURE, Summary: "API Unreachable") rather than raising exceptions.

### FR-3: Triage Synthesis
- **FR-3.1:** Triage Agent must not execute new tools; it is Read-Only.
- **FR-3.2:** Triage Agent must output a confidence score (1-10).

### FR-4: API Integration
- **FR-4.1:** The FastAPI endpoint must be asynchronous (`async def`).
- **FR-4.2:** The endpoint receives the user query and returns the final `TriageReport`.

## 5. Non-Goals
- **No Frontend Changes:** The existing UI will consume the new API response format without modification (or minimal mapping).
- **No Automatic Remediation:** The system will suggest fixes but will NOT execute write operations (e.g., `shut / no shut`) on network devices.
- **No Streaming:** The API will use a standard Request/Response model for V1.

## 6. Technical Considerations
- **Framework:** LangGraph (StateGraph).
- **Runtime:** Python 3.10+.
- **Validation:** Pydantic V2.
- **Concurrency:** `asyncio` for parallel node execution.
- **Mocking:** All external tool calls must be mockable via a `tests/mock_harness.py` for CI/CD.

## 7. Success Metrics
- **Performance:** P95 Latency for complex queries reduced by >40% compared to linear chain baseline.
- **Stability:** <1% rate of "Context Length Exceeded" errors.
- **Accuracy:** >90% of Triage Reports correctly identify the root cause in "Golden Set" test cases.

## 8. Open Questions
- Do we need a "Human in the loop" interrupt for the Supervisor if confidence is low? (Deferred to V2).
- How do we handle authentication refreshes for long-running Cisco sessions? (Assumed handled by tool implementation).
