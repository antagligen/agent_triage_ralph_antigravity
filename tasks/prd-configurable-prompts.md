# PRD: Configurable System Prompts

## Introduction

Make all system prompts for sub-agents and orchestrator configurable via external files. Currently, prompts are hardcoded in Python files, making them difficult to modify without code changes. This feature extracts prompts to a dedicated `backend/system_prompts/` folder where each agent has its own prompt file.

## Goals

- Centralize all agent system prompts in `backend/system_prompts/`
- Allow prompt modification without code changes
- Provide sensible default prompts with warning logs if files are missing
- Maintain backward compatibility with existing functionality

## User Stories

### US-001: Create Prompt File Structure
**Description:** As a developer, I want a dedicated folder for system prompts so that I can easily find and edit them.

**Acceptance Criteria:**
- [ ] Create `backend/system_prompts/` directory
- [ ] Create prompt files: `orchestrator.txt`, `aci.txt`, `infoblox.txt`, `palo_alto.txt`, `triage.txt`
- [ ] Each file contains the current hardcoded prompt text
- [ ] Typecheck passes

---

### US-002: Implement Prompt Loading Utility
**Description:** As a developer, I want a utility function to load prompts from files so that agents can use external configurations.

**Acceptance Criteria:**
- [ ] Add `load_system_prompt(agent_name: str) -> str` function to `config.py`
- [ ] Function looks for `backend/system_prompts/{agent_name}.txt`
- [ ] If file not found, logs warning and returns hardcoded default
- [ ] Typecheck passes

---

### US-003: Update Orchestrator to Use Configurable Prompt
**Description:** As a developer, I want the orchestrator to load its prompt from config so that I can customize its behavior.

**Acceptance Criteria:**
- [ ] Orchestrator uses `load_system_prompt("orchestrator")`
- [ ] Falls back to current behavior if file missing
- [ ] Typecheck passes

---

### US-004: Update Sub-Agents with Configurable Prompts
**Description:** As a developer, I want sub-agents (ACI, Infoblox, Palo Alto) to use configurable system prompts.

**Acceptance Criteria:**
- [ ] Each sub-agent uses `load_system_prompt()` for its prompt
- [ ] Pass system prompt to `create_react_agent()` via `state_modifier` parameter
- [ ] Falls back to default if file missing
- [ ] Typecheck passes

---

### US-005: Update Triage Agent with Configurable Prompt
**Description:** As a developer, I want the triage agent to use a configurable system prompt.

**Acceptance Criteria:**
- [ ] Triage agent uses `load_system_prompt("triage")`
- [ ] Falls back to current hardcoded prompt if file missing
- [ ] Typecheck passes

---

### US-006: Add Unit Tests for Prompt Loading
**Description:** As a developer, I want tests to verify prompt loading behavior.

**Acceptance Criteria:**
- [ ] Test loading existing prompt file returns content
- [ ] Test loading missing file returns default and logs warning
- [ ] Typecheck passes

## Functional Requirements

- FR-1: System prompts stored in `backend/system_prompts/{agent_name}.txt`
- FR-2: `load_system_prompt()` reads file content as plain text
- FR-3: Missing files trigger warning log and return hardcoded default
- FR-4: Dynamic variables (like `{incident_data}`) remain in code, only static prompt text is configurable
- FR-5: Prompts are loaded at agent initialization time

## Non-Goals

- No runtime hot-reloading of prompts (requires restart)
- No Jinja2/templating for dynamic variables
- No web UI for editing prompts
- No versioning of prompts

## Technical Considerations

- Use Python's `logging` module for warnings
- Prompt files use `.txt` extension for simplicity
- Path resolution relative to `backend/` directory
- Consider Docker volume mounts for production customization

## Success Metrics

- All 5 agents use external prompt files
- Zero code changes required to modify prompt text
- No regression in existing functionality
- All tests pass

## Open Questions

- Should prompts be reloaded on each request or cached at startup? (Current: startup)
