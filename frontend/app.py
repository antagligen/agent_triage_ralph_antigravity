import streamlit as st
import requests
import json
import os

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_CHAT_URL = f"{BACKEND_URL}/chat"

st.set_page_config(
    page_title="Ralph - AI Troubleshooting Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Ralph - AI Troubleshooting Agent")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    st.write("Configuration options will go here (US-002).")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If we saved thoughts, we could display them here too, 
        # but for now let's focus on the conversation flow.

# --- Chat Input & Streaming Logic ---
if prompt := st.chat_input("How can I help you troubleshoot?"):
    # 1. Display User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Prepare for Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # We'll use an expander for "Thoughts" that updates in real-time
        thought_expander = st.status("Thinking...", expanded=True)
        thought_text = ""
        
        full_response = ""
        
        try:
            # 3. Call Backend API with Streaming
            response = requests.post(
                API_CHAT_URL, 
                json={"message": prompt}, 
                stream=True
            )
            
            if response.status_code == 200:
                # 4. Process SSE Stream
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        
                        if decoded_line.startswith("event:"):
                            event_type = decoded_line.split(":", 1)[1].strip()
                        elif decoded_line.startswith("data:"):
                            data_str = decoded_line.split(":", 1)[1].strip()
                            
                            try:
                                data = json.loads(data_str)
                                
                                if event_type == "thought":
                                    # Handle internal thought events
                                    node = data.get("node", "Unknown")
                                    content = data.get("content", "")
                                    
                                    # Append to the thought log
                                    new_thought = f"**[{node}]**: {content}\n\n"
                                    thought_text += new_thought
                                    thought_expander.markdown(thought_text)
                                    
                                elif event_type == "routing":
                                    # Handle routing events
                                    next_node = data.get("routing", "")
                                    thought_text += f"*Routing to: `{next_node}`*\n\n"
                                    thought_expander.markdown(thought_text)
                                
                                # We treat the actual message content as part of the thought stream 
                                # if it comes from nodes, but usually the 'final' response 
                                # comes differently or is just the accumulation of text.
                                # Based on current backend implementation, 'thought' events
                                # contain the content.
                                # Let's assume for now that if node is 'orchestrator' 
                                # and it's sending content, it might be the final answer?
                                # Actually the backend streams EVERYTHING as thoughts currently.
                                # We need to decide what constitutes the "Final Answer".
                                # For this pass, we'll append everything to full_response 
                                # AND show it in thoughts.
                                
                                # Refinement: Only show "Assistant" final text if we identify it.
                                # But per backend code:
                                # yield f"event: thought\ndata: {data}\n\n"
                                # It doesn't distinguish final answer well yet.
                                
                                # Strategy: Just accumulate content for the main display?
                                # Or if it is a specific node?
                                # Let's mirror the content to the main chat for now.
                                if data.get("content"):
                                    chunk = data.get("content")
                                    full_response += chunk
                                    message_placeholder.markdown(full_response + "▌")

                            except json.JSONDecodeError:
                                pass # formatting error or keepalive
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
                
            thought_expander.update(label="Finished Processing", state="complete", expanded=False)
            message_placeholder.markdown(full_response)
            
            # 5. Save valid response to history
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            st.error(f"Connection failed: {e}")
