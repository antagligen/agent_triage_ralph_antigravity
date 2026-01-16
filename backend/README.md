# Backend Service

The backend is a **FastAPI** microservice that runs the **LangGraph** orchestrator. It manages the agentic workflow, routes requests to sub-agents, and streams thoughts and responses back to the client.

## 🚀 Quick Start

Usually run via Docker Compose from the root, but for local development:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Start the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Reference

### 1. Chat (Streaming)
`POST /chat`

Initiates a chat with the orchestrator. This endpoint streams Server-Sent Events (SSE).

**Request Body:**
```json
{
  "message": "My internet is down",
  "model_name": "gemini-pro",     // Optional: Override default model
  "model_provider": "gemini"      // Optional: Override default provider
}
```

**Response (SSE Stream):**
The stream yields events of type `thought` or `routing`.

- **Event: `thought`**: Represents a step in the reasoning process or a final answer.
  ```json
  data: {
    "node": "orchestrator",
    "content": "I should check with the network specialist.",
    "type": "ai"
  }
  ```

- **Event: `routing`**: Indicates a transition in the graph.
  ```json
  data: {
    "routing": "network_specialist"
  }
  ```

### 2. Health Check
`GET /health`

Returns `{"status": "ok"}`. Used by Docker healthchecks.

### 3. Current Config
`GET /config`

Returns the currently loaded configuration (orchestrator model, active sub-agents).

## ⚙️ Configuration

Configuration is managed via `config.yaml` located in the `backend/` root (or `config.json`). It is loaded using Pydantic models for validation.

- **File**: `backend/config.yaml`
- **Loader**: `src.config.load_config`

### Structure
```yaml
orchestrator_model: "gpt-4-turbo"
orchestrator_provider: "openai"
system_prompt: "You are a helpful IT support orchestrator..."
sub_agents:
  - name: "network_specialist"
    description: "Expert in connectivity issues"
    tools: ["ping", "traceroute"]
```

### Environment Variables
Sensitive keys (like API keys) should be stored in a `.env` file in the `backend/` directory. The application loads this at startup using `python-dotenv`.

## 🏗️ Architecture (LangGraph)

The core logic resides in `src/orchestrator.py`.

1.  **State**: `AgentState` tracks `messages` (history) and `next_node` (routing decision).
2.  **Orchestrator Node**:
    - Receives user input.
    - prompting includes descriptions of all available sub-agents from `config.yaml`.
    - Decides whether to answer directly or route to a sub-agent.
3.  **Graph**:
    - The `StateGraph` connects the `orchestrator` to sub-agent nodes.
    - Conditional edges use the `router` function to determine the next step.

## 🔌 Extending the Backend

### Adding a New Sub-Agent

1.  **Implement the Node**:
    Create a new module in `src/sub_agents/` (e.g., `src/sub_agents/database.py`) that exports a LangGraph node function.

2.  **Register the Node**:
    In `src/orchestrator.py`, import your node and add it to the graph:
    ```python
    from .sub_agents.database import get_database_agent_node
    
    workflow.add_node("database_expert", get_database_agent_node(config))
    ```

3.  **Update Config**:
    Add the agent to `config.yaml` so the Orchestrator knows about it:
    ```yaml
    sub_agents:
      # ... existing agents
      - name: "database_expert"
        description: "Can query SQL logs and check DB status"
        tools: ["custom_tool"]
    ```

### Adding a New Tool
To add a tool to an existing agent:
1.  Define the tool (usually using `@tool` decorator or `StructuredTool`).
2.  Bind the tool to the agent's LLM in its specific node implementation.
