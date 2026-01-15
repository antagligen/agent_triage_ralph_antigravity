# PRD: Gemini API Support

## Introduction

Extend the current AI Troubleshooting Agent to support Google's Gemini models alongside OpenAI. This will provide users with flexibility in choosing their underlying LLM provider, potentially optimizing for cost, speed, or capability. The support will be global (Orchestrator and Sub-agents) and dynamically selectable via the UI.

## Goals

-   Support `GOOGLE_API_KEY` for authentication.
-   Enable dynamic switching between OpenAI and Gemini models via the Frontend UI.
-   Ensure all existing agent capabilities (tools, streaming, routing) work seamlessly with Gemini.
-   Allow configuration of specific Gemini model versions (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`).

## User Stories

### US-001: Add Gemini Configuration & Env Support
**Description:** As a developer, I need to configure the backend to accept Gemini API keys and model settings so that the application can authenticate with Google's services.

**Acceptance Criteria:**
- [ ] Add `GOOGLE_API_KEY` to `.env` and `.env.example`.
- [ ] Update configuration validation (Pydantic models) to allow `gemini` provider and model names.
- [ ] Ensure default config still works if `GOOGLE_API_KEY` is missing (optional) or fail gracefully.
- [ ] Typecheck passes.

### US-002: Implement Gemini Model Provider
**Description:** As a developer, I want a unified way to instantiate LLMs so that the code can switch between OpenAI and Gemini based on configuration.

**Acceptance Criteria:**
- [ ] create a factory or provider function that returns the correct LangChain chat model wrapper (`ChatOpenAI` or `ChatGoogleGenerativeAI`) based on input parameters.
- [ ] Verify that the Gemini wrapper supports the necessary features (streaming, tool calling).
- [ ] Typecheck passes.

### US-003: Update Backend to Accept Model Override
**Description:** As a user, I want the backend to respect the model choice sent from the frontend request, overriding the default configuration.

**Acceptance Criteria:**
- [ ] Update the API endpoint (e.g., `/chat`) to accept an optional `model` or `provider` parameter.
- [ ] Pass this parameter down to the graph/agent initialization.
- [ ] Ensure the correct model is used for the Orchestrator for that request.
- [ ] Typecheck passes.

### US-004: Frontend Model Selection UI
**Description:** As a user, I want to select which AI model to use from the interface so that I can dynamically choose the best model for my task.

**Acceptance Criteria:**
- [ ] Add a settings section (sidebar or expander) in Streamlit.
- [ ] Add a dropdown/radio button to select between configured OpenAI and Gemini models.
- [ ] The selection is preserved across chat messages in the session.
- [ ] Verify in browser using dev-browser skill.

### US-005: Global Model Propagation
**Description:** As a user, when I select a model, I want it to apply to sub-agents as well (where applicable) to ensure consistent performance.

**Acceptance Criteria:**
- [ ] Ensure the selected model is propagated to sub-agents initialized by the orchestrator.
- [ ] Verify that sub-agents are actually using the requested model (e.g., via logs or behavior).
- [ ] Typecheck passes.

## Functional Requirements
-   **FR-1:** System must support `gemini-1.5-flash` and `gemini-1.5-pro` at a minimum.
-   **FR-2:** API Key must be loaded from environment variables (`GOOGLE_API_KEY`).
-   **FR-3:** Frontend must send the selected model ID with the chat request.
-   **FR-4:** Streaming responses must work identically for both providers.

## Non-Goals
-   Per-agent model configuration in the UI (e.g., Orchestrator uses GPT-4, Network Agent uses Gemini). We will use a global setting for this iteration.
-   Billing/usage tracking integration.

## Technical Considerations
-   Use `langchain-google-genai` package.
-   Streamlit's `st.session_state` will manage the selected model in the frontend.

## Success Metrics
-   User can switch to Gemini Flash and get a response.
-   User can switch back to OpenAI and get a response.
