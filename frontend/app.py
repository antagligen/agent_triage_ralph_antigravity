"""
AI Troubleshooting Agent - Streamlit Frontend
A chat interface for interacting with the AI troubleshooting agent.
"""

import streamlit as st
import requests
import json
from typing import Generator
import os

# Backend API configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/chat"


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
    """Initialize session state variables for chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat_history() -> None:
    """Render the chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def send_message_to_backend(message: str) -> tuple[bool, str]:
    """Send a message to the backend API and collect the response.
    
    Args:
        message: The user's message to send.
        
    Returns:
        A tuple of (success: bool, response_content: str).
        On success, response_content contains collected SSE data.
        On failure, response_content contains the error message.
    """
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"message": message},
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            return False, f"Backend returned status {response.status_code}: {response.text}"
        
        # Collect SSE events (US-004 will parse these properly)
        # For now, just collect all content for display
        collected_content = []
        buffer = ""
        
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # Parse SSE events (double newline separates events)
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    
                    # Extract data from event
                    for line in event_str.split("\n"):
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "content" in data:
                                    collected_content.append(data["content"])
                            except json.JSONDecodeError:
                                pass
        
        if collected_content:
            return True, "\n\n".join(collected_content)
        else:
            return True, "Response received but no content extracted."
            
    except requests.exceptions.ConnectionError:
        return False, "❌ **Connection Error:** Could not connect to the backend. Please ensure the backend service is running."
    except requests.exceptions.Timeout:
        return False, "❌ **Timeout:** The backend took too long to respond. Please try again."
    except requests.exceptions.RequestException as e:
        return False, f"❌ **Request Error:** {str(e)}"


def handle_user_input(user_input: str) -> None:
    """Handle user input and add to chat history.
    
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
    
    # Call the backend API with loading indicator
    with st.chat_message("assistant"):
        with st.spinner("🔄 Processing your request..."):
            success, response_content = send_message_to_backend(user_input)
        
        if success:
            st.markdown(response_content)
        else:
            st.error(response_content)
    
    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content
    })


def render_system_status() -> None:
    """Render the system status indicators in the sidebar."""
    with st.sidebar:
        st.subheader("System Status")
        st.metric("Backend", "Pending", help="Connection to backend API")
        st.metric("Model", "Not Selected", help="Currently selected AI model")
        st.metric("Sub-Agents", "0 Active", help="Number of active sub-agents")


def main() -> None:
    """Main application entry point."""
    configure_page()
    init_session_state()
    render_header()
    render_system_status()
    
    # Render existing chat history
    render_chat_history()
    
    # Chat input at the bottom of the page
    if user_input := st.chat_input("Ask a troubleshooting question..."):
        handle_user_input(user_input)


if __name__ == "__main__":
    main()
