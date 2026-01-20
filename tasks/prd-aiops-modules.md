# PRD: AIOps POC - Modular ACI Agent & Orchestration

## 1. Introduction
Develop a Proof of Concept (POC) for a modular AIOps pipeline using **LangGraph**. The system will feature an Orchestrator that routes tasks to a specialized **Cisco ACI Agent**, which uses dynamically generated tools based on an external JSON configuration. The workflow concludes with a Triage Agent synthesizing the findings.

This POC targets the "Configuration-Driven Tooling" architecture to decouple tool definitions from code.

## 2. Goals
- **Prove Modular Tooling:** Demonstrate runtime tool generation from `aci_endpoints.json`.
- **Decouple Configuration:** Store connectivity details and tool definitions externally (`config/devices.yaml`, `config/aci_endpoints.json`).
- **Valid Orchestration:** Correctly route between Orchestrator, ACI Agent, and Triage.
- **Resilient Execution:** Partial failures in tool execution should not halt the pipeline; errors must be captured and reported.
- **Success Definition:** Functional correctness of the pipeline (Orchestrator routes -> Tool executes -> Triage summarizes).

## 3. User Stories

### US-001: External Device Configuration
**Description:** As a DevOps Engineer, I want to define my ACI APIC credentials and URL in a config file so that I don't hardcode secrets or IPs.
**Acceptance Criteria:**
- [ ] System loads device details from `config/devices.yaml`.
- [ ] Authentication uses credentials from config to generate tokens.
- [ ] Typecheck passes.

### US-002: Dynamic Tool Generation
**Description:** As a Developer, I want to add a new ACI API endpoint by adding a JSON entry, so that the Agent immediately gains this capability without code deployments.
**Acceptance Criteria:**
- [ ] System reads `config/aci_endpoints.json` on startup.
- [ ] Factory function converts JSON entries into LangChain `StructuredTool` objects.
- [ ] Pydantic models for tool arguments are generated dynamically and correctly.
- [ ] Typecheck passes.

### US-003: Intelligent Agent Execution
**Description:** As a User, I want the ACI Agent to select the correct tool based on natural language queries.
**Acceptance Criteria:**
- [ ] Agent selects `get_tenant_health` tool for "Check tenant 'Production' health".
- [ ] Agent correctly extracts arguments (e.g., "Production").
- [ ] Generic runner executes the API call (GET only).
- [ ] Typecheck passes.
- [ ] Verify in browser using dev-browser skill (if UI is involved, otherwise verify logs/trace).

### US-004: Triage Synthesis with Error Handling
**Description:** As a User, I want a final summary of the technical data, including any tools that failed to execute.
**Acceptance Criteria:**
- [ ] ACI Agent catches tool execution errors, logs them, and returns a structured error result instead of crashing (Partial Failure).
- [ ] Triage Agent receives raw success data AND error reports.
- [ ] Triage Agent generates a text summary (Simple LLM summary) of findings.
- [ ] Triage output explicitly mentions any skipped/failed tools.
- [ ] Typecheck passes.

## 4. Functional Requirements

### FR-1: Configuration Management
- **FR-1.1:** Parse `config/devices.yaml` for `apic_url`, `username`, `password`/`private_key`.
- **FR-1.2:** Parse `config/aci_endpoints.json` for tool definitions.

### FR-2: Dynamic Tool Factory
- **FR-2.1:** `build_aci_tools(json_path)` returns list of tools.
- **FR-2.2:** Use `pydantic.create_model` for argument schemas.
- **FR-2.3:** Validate URL placeholders match argument names.

### FR-3: Generic API Runner
- **FR-3.1:** Single Python function for HTTP logic.
- **FR-3.2:** Handle Auth (login) automatically.
- **FR-3.3:** Support GET requests.

### FR-4: Orchestration & Error Handling
- **FR-4.1:** Flow: Orchestrator -> ACI Agent -> Triage.
- **FR-4.2:** ACI Agent must catch exceptions during tool execution.
- **FR-4.3:** if a tool fails, return a "Failed" status object; do not raise exception up to graph.
- **FR-4.4:** Triage Agent summarizes successes and lists failures.

## 5. Non-Goals
- POST/PUT/DELETE operations (Read-only for now).
- Complex heuristic-based triage (Simple LLM summary only).
- Retries on failed API calls (Fail fast and report).

## 6. Success Metrics
- **Functional Correctness:** The pipeline runs end-to-end without crashing on partial tool failures, and the final report accurately reflects both data extracted and errors encountered.
