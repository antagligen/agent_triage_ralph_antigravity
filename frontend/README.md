# Frontend Microservice

This directory contains the Streamlit-based frontend for the Ralph AI Troubleshooting Agent. It provides a chat interface for users to interact with the backend, visualizing the agent's thought process and routing decisions in real-time.

## Structure

- **`app.py`**: The main entry point for the Streamlit application. It handles the UI layout, state management, and API interactions.
- **`Dockerfile`**: Configuration for containerizing the frontend application.
- **`requirements.txt`**: Python dependencies (e.g., `streamlit`, `requests`).

## Configuration

The application uses `st.sidebar` to allow users to configure the AI model:
- **Model Provider**: Select between supported providers (e.g., OpenAI, Gemini).
- **Model Name**: Choose specific models based on the selected provider (e.g., `gpt-4o`, `gemini-1.5-pro`).

These settings are passed to the backend with every chat request.

## State Management

Streamlit reruns the entire script on every interaction. To maintain context, we use `st.session_state`:

- **`st.session_state.messages`**: A list of dictionaries storing the conversation history (`role` and `content`). This persists the chat across reruns.

## Server-Sent Events (SSE) Integration

The frontend communicates with the backend via a streaming API to provide a responsive experience.

1.  **Request**: `requests.post()` is called with `stream=True` to keep the connection open.
2.  **Parsing**: The response is processed line-by-line to parse standard SSE format:
    -   `event: [type]` (e.g., `thought`, `routing`)
    -   `data: [json_payload]`
3.  **Visualization**:
    -   **Thoughts & Routing**: Events of type `thought` or `routing` are displayed inside a collapsible `st.status("Thinking...")` container. This allows users to see the agent's internal logic without cluttering the main chat.
    -   **Final Response**: Content is accumulated and streamed into the main chat area using `st.empty()`.

## Development

To run the frontend locally:

```bash
cd frontend
streamlit run app.py
```

Ensure the backend is running and reachable (default: `http://localhost:8000`). You can configure the backend URL via the `BACKEND_URL` environment variable.
