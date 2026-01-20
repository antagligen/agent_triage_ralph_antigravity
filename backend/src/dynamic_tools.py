import json
from typing import List, Dict, Type, Any, Callable, Optional
from dataclasses import dataclass
from pydantic import BaseModel, create_model, Field
from langchain_core.tools import StructuredTool
import requests # type: ignore

@dataclass
class ACIToolConfig:
    """Configuration for ACI tool execution."""
    base_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = False

def load_endpoints_config(path: str) -> List[Dict]:
    """
    Loads list of tool configurations from a JSON file.
    """
    with open(path, 'r') as f:
        return json.load(f)

def create_dynamic_model(tool_name: str, params: List[Dict]) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model for tool arguments based on config.
    """
    fields = {}
    for param in params:
        p_name = param["name"]
        p_type_str = param.get("type", "str")
        p_desc = param.get("description", "")
        
        # Map string types to actual Python types
        # Basic support for now, can be expanded
        p_type: Type[Any] = str
        if p_type_str == "int":
            p_type = int
        elif p_type_str == "bool":
            p_type = bool
        elif p_type_str == "float":
            p_type = float
            
        fields[p_name] = (p_type, Field(description=p_desc))
    
    # Create the model dynamically
    model_name = f"{tool_name.replace('_', ' ').title().replace(' ', '')}Args"
    return create_model(model_name, **fields) # type: ignore

def generic_aci_runner(path: str, method: str, tool_config: Optional[ACIToolConfig] = None, **kwargs) -> str:
    """
    A generic runner that executes the API call.
    """
    # Basic path interpolation
    formatted_path = path
    for k, v in kwargs.items():
        formatted_path = formatted_path.replace(f"{{{k}}}", str(v))
        
    if not tool_config:
        return f"Executed {method} on {formatted_path}. [SIMULATION] Success. (No config provided)"

    url = f"{tool_config.base_url.rstrip('/')}{formatted_path}"
    
    try:
        # In a real environment, you'd likely handle auth tokens better (e.g. login first)
        # For this POC, we'll assume Basic Auth or just log the attempt if credentials aren't full.
        auth = None
        if tool_config.username and tool_config.password:
            # Note: ACI typically uses cookie/token auth, but this is a POC.
            # We'll stick to a placeholder "login" or just sending requests.
            # For simplicity in this generic runner, we won't implement full ACI login dance here
            # unless we make it stateful.
            pass

        # We are suppressing SSL warnings for the POC usually
        # requests.packages.urllib3.disable_warnings() # type: ignore

        response = requests.request(
            method=method,
            url=url,
            auth=auth,
            verify=tool_config.verify_ssl,
            timeout=10
        )
        
        # Return truncated response/status
        if response.status_code < 300:
            try:
                data = response.json()
                return json.dumps(data, indent=2)
            except:
                return response.text
        else:
            return f"Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"Failed to execute {method} on {url}: {str(e)}"

def create_dynamic_tool(config: Dict, tool_config: Optional[ACIToolConfig] = None) -> StructuredTool:
    """
    Creates a LangChain StructuredTool from a config dictionary.
    """
    name = config["name"]
    description = config["description"]
    path = config["path"]
    method = config["method"]
    params = config.get("parameters", [])
    
    # 1. Create the args schema
    args_schema = create_dynamic_model(name, params)
    
    # 2. Define the executable function
    # We need to bind the fixed path/method to the function so the agent just calls it with args
    def tool_func(**kwargs) -> str:
        return generic_aci_runner(path, method, tool_config=tool_config, **kwargs)
        
    # 3. Return the tool
    return StructuredTool.from_function(
        func=tool_func,
        name=name,
        description=description,
        args_schema=args_schema
    )
