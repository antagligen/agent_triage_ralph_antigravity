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


def main() -> None:
    """Main application entry point."""
    configure_page()
    render_header()
    
    # Placeholder for chat interface (US-002)
    st.info("💬 Chat interface coming soon...")
    
    # Display system status
    with st.container():
        st.subheader("System Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Backend", "Pending", help="Connection to backend API")
        with col2:
            st.metric("Model", "Not Selected", help="Currently selected AI model")
        with col3:
            st.metric("Sub-Agents", "0 Active", help="Number of active sub-agents")


if __name__ == "__main__":
    main()
