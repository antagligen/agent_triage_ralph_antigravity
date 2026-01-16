import json
from typing import Any, AsyncGenerator, Dict

async def stream_graph_events(workflow: Any, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """
    Generator that creates SSE events from the LangGraph stream.
    """
    # Use .astream_events or .stream for detailed updates
    # simple .stream returns state updates
    async for event in workflow.astream(inputs, stream_mode="updates"):
        # Helper to format SSE
        # event is a dict of {node_name: state_update}
        
        for node_name, state_update in event.items():
            # We treat node updates as "thoughts" unless it's the final answer
            
            # If we have a new message
            if "messages" in state_update:
                messages = state_update["messages"]
                # For this simple graph, messages is usually a single message or list of messages
                if not isinstance(messages, list):
                    messages = [messages]
                
                for msg in messages:
                    # Construct valid JSON data
                    data = json.dumps({
                        "node": node_name,
                        "content": msg.content,
                        "type": msg.type
                    })
                    
                    if node_name == "orchestrator":
                        yield f"event: thought\ndata: {data}\n\n"
                    elif node_name == "network_specialist":
                         yield f"event: thought\ndata: {data}\n\n"
                    
                    # If it's a direct response from orchestrator (final answer)
                    # The logic in orchestrator returns END with a SystemMessage
                    # We might need to distinguish "final" better. 
                    # For now, let's assume the last message in the stream is the response, 
                    # BUT streaming doesn't know "last" easily until done.
                    # We'll just stream everything as thoughts and let the client decide, 
                    # OR we can refine this.
            
            # If we have next_node info (useful for debugging)
            if "next_node" in state_update:
                 data = json.dumps({"routing": state_update["next_node"]})
                 yield f"event: routing\ndata: {data}\n\n"
