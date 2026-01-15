"""
AI Troubleshooting Agent - Streamlit Frontend
A chat interface for interacting with the AI troubleshooting agent.
"""

import streamlit as st
import requests
import json
from typing import Generator
import os
from dataclasses import dataclass

# Backend API configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/chat"


@dataclass
class SSEEvent:
    """Represents a parsed SSE event."""
    event_type: str  # "thought", "routing", "response"
    data: dict


def configure_page() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="AI Troubleshooting Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_header() -> None:
    """Render the application header."""
    st.title("🤖 AI Troubleshooting Agent")
    st.caption("An intelligent assistant for network and infrastructure troubleshooting")
    st.divider()


def init_session_state() -> None:
    """Initialize session state variables for chat history and model config."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_provider" not in st.session_state:
        st.session_state.model_provider = "openai"
    if "model_name" not in st.session_state:
        st.session_state.model_name = "gpt-4o"


def render_chat_history() -> None:
    """Render the chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Render thoughts in an expander if present
            if "thoughts" in message and message["thoughts"]:
                with st.expander("💭 Agent Thoughts", expanded=False):
                    for thought in message["thoughts"]:
                        node = thought.get("node", "unknown")
                        content = thought.get("content", "")
                        st.markdown(f"**{node}:** {content}")
            # Render routing info if present
            if "routing" in message and message["routing"]:
                for route in message["routing"]:
                    st.info(f"🔀 Switching to: **{route}**")
            # Render main content
            st.markdown(message["content"])


def parse_sse_event(event_str: str) -> SSEEvent | None:
    """Parse a single SSE event string into an SSEEvent object.
    
    Args:
        event_str: Raw SSE event string (may contain 'event:' and 'data:' lines)
        
    Returns:
        SSEEvent object or None if parsing fails
    """
    event_type = "message"  # default SSE event type
    data_str = None
    
    for line in event_str.split("\n"):
        line = line.strip()
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
    
    if data_str is None:
        return None
    
    try:
        data = json.loads(data_str)
        return SSEEvent(event_type=event_type, data=data)
    except json.JSONDecodeError:
        return None


def stream_sse_events(
    message: str,
    provider: str | None = None,
    model: str | None = None
) -> Generator[SSEEvent, None, None]:
    """Stream SSE events from the backend.
    
    Args:
        message: The user's message to send.
        provider: Optional model provider override (e.g., "openai", "gemini")
        model: Optional model name override (e.g., "gpt-4o", "gemini-2.0-flash")
        
    Yields:
        SSEEvent objects as they arrive from the backend.
    """
    # Build request payload with optional model overrides
    payload: dict[str, str] = {"message": message}
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            stream=True,
            timeout=120
        )
        
        if response.status_code != 200:
            yield SSEEvent(
                event_type="error",
                data={"content": f"Backend returned status {response.status_code}: {response.text}"}
            )
            return
        
        buffer = ""
        
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # Parse SSE events (double newline separates events)
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    event = parse_sse_event(event_str)
                    if event:
                        yield event
                        
    except requests.exceptions.ConnectionError:
        yield SSEEvent(
            event_type="error",
            data={"content": "❌ **Connection Error:** Could not connect to the backend. Please ensure the backend service is running."}
        )
    except requests.exceptions.Timeout:
        yield SSEEvent(
            event_type="error",
            data={"content": "❌ **Timeout:** The backend took too long to respond. Please try again."}
        )
    except requests.exceptions.RequestException as e:
        yield SSEEvent(
            event_type="error",
            data={"content": f"❌ **Request Error:** {str(e)}"}
        )


def handle_user_input(user_input: str) -> None:
    """Handle user input with real-time SSE streaming display.
    
    Args:
        user_input: The user's message text.
    """
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Process streaming response
    with st.chat_message("assistant"):
        # Containers for dynamic content
        thoughts_container = st.container()
        routing_container = st.container()
        response_container = st.container()
        
        # Collect events for history
        thoughts: list[dict] = []
        routing_events: list[str] = []
        response_chunks: list[str] = []
        error_message: str | None = None
        
        # Active expander for thoughts (shown during streaming)
        with thoughts_container:
            thoughts_expander = st.expander("💭 Agent Thoughts", expanded=True)
        
        # Response placeholder for real-time updates
        with response_container:
            response_placeholder = st.empty()
        
        # Stream and display events with model config
        for event in stream_sse_events(
            user_input,
            provider=st.session_state.model_provider,
            model=st.session_state.model_name
        ):
            if event.event_type == "thought":
                node = event.data.get("node", "unknown")
                content = event.data.get("content", "")
                thoughts.append({"node": node, "content": content})
                
                with thoughts_expander:
                    st.markdown(f"**{node}:** {content}")
                
                # Also add to response if it's from orchestrator (final answer)
                # The backend sends the final response as a 'thought' from orchestrator
                if node == "orchestrator" or node == "network_specialist":
                    response_chunks.append(content)
                    # Update response in real-time
                    with response_placeholder:
                        st.markdown("\n\n".join(response_chunks))
            
            elif event.event_type == "routing":
                # Display routing indicator
                target = event.data.get("routing", "unknown")
                routing_events.append(target)
                with routing_container:
                    st.info(f"🔀 Switching to: **{target}**")
            
            elif event.event_type == "response":
                # Direct response event (if backend sends it)
                content = event.data.get("content", "")
                response_chunks.append(content)
                with response_placeholder:
                    st.markdown("\n\n".join(response_chunks))
            
            elif event.event_type == "error":
                error_message = event.data.get("content", "Unknown error")
                st.error(error_message)
        
        # If no response chunks but we have thoughts, use the last thought as response
        final_response = "\n\n".join(response_chunks) if response_chunks else "No response received."
        if error_message:
            final_response = error_message
    
    # Add assistant response to history with thoughts and routing
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_response,
        "thoughts": thoughts,
        "routing": routing_events
    })


# Model presets for each provider
MODEL_PRESETS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "gemini": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
}


def render_sidebar() -> None:
    """Render the sidebar with model configuration and system status."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model Provider Selection
        provider_options = ["openai", "gemini"]
        current_provider_index = provider_options.index(
            st.session_state.model_provider
        ) if st.session_state.model_provider in provider_options else 0
        
        selected_provider = st.selectbox(
            "Model Provider",
            options=provider_options,
            index=current_provider_index,
            help="Select the AI model provider"
        )
        # Update session state if changed
        if selected_provider and selected_provider != st.session_state.model_provider:
            st.session_state.model_provider = selected_provider
            # Reset to first preset model for new provider
            st.session_state.model_name = MODEL_PRESETS.get(
                selected_provider, ["gpt-4o"]
            )[0]
            st.rerun()
        
        # Model Name Selection (dropdown with presets + custom option)
        model_options = MODEL_PRESETS.get(
            str(st.session_state.model_provider), ["gpt-4o"]
        )
        current_model = str(st.session_state.model_name)
        
        # Check if current model is in presets, otherwise use custom
        if current_model in model_options:
            current_model_index = model_options.index(current_model)
            use_custom = False
        else:
            current_model_index = 0
            use_custom = True
        
        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=current_model_index,
            help="Select a model or use custom input below"
        )
        
        # Custom model input
        custom_model = st.text_input(
            "Custom Model (optional)",
            value=current_model if use_custom else "",
            help="Enter a custom model name to override the dropdown"
        )
        
        # Determine final model name
        final_model = custom_model.strip() if custom_model.strip() else selected_model
        if final_model and final_model != st.session_state.model_name:
            st.session_state.model_name = final_model
        
        st.divider()
        
        # Display current configuration
        st.subheader("Current Config")
        st.caption(f"**Provider:** {st.session_state.model_provider}")
        st.caption(f"**Model:** {st.session_state.model_name}")
        
        st.divider()
        
        # System Status
        st.subheader("System Status")
        st.metric("Backend", "Pending", help="Connection to backend API")
        st.metric("Sub-Agents", "0 Active", help="Number of active sub-agents")


def main() -> None:
    """Main application entry point."""
    configure_page()
    init_session_state()
    render_header()
    render_sidebar()
    
    # Render existing chat history
    render_chat_history()
    
    # Chat input at the bottom of the page
    if user_input := st.chat_input("Ask a troubleshooting question..."):
        handle_user_input(user_input)


if __name__ == "__main__":
    main()
