"""
AI Troubleshooting Agent - Streamlit Frontend
A chat interface for interacting with the AI troubleshooting agent.
"""

import streamlit as st


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
    
    # Placeholder for assistant response (US-003/US-004 will implement actual API call)
    with st.chat_message("assistant"):
        st.info("🔄 Backend integration coming in US-003...")
    
    # Add placeholder assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": "🔄 Backend integration coming in US-003..."
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
