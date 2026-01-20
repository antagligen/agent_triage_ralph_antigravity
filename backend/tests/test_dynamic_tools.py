import pytest
import tempfile
import json
import os
from pydantic import BaseModel
from backend.src.dynamic_tools import load_endpoints_config, create_dynamic_model, create_dynamic_tool

@pytest.fixture
def sample_config_file():
    data = [
        {
            "name": "test_tool",
            "description": "A test tool",
            "path": "/api/test/{id}",
            "method": "GET",
            "parameters": [
                {"name": "id", "type": "str", "description": "The ID"}
            ]
        }
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f)
        path = f.name

    yield path
    os.remove(path)

def test_load_endpoints_config(sample_config_file):
    config = load_endpoints_config(sample_config_file)
    assert len(config) == 1
    assert config[0]["name"] == "test_tool"

def test_create_dynamic_model():
    params = [
        {"name": "tenant_name", "type": "str", "description": "Tenant Name"},
        {"name": "count", "type": "int", "description": "Count"}
    ]
    Model = create_dynamic_model("test_tool", params)
    assert issubclass(Model, BaseModel)
    schema = Model.model_json_schema()
    props = schema["properties"]

    assert "tenant_name" in props
    assert props["tenant_name"]["type"] == "string"
    assert "count" in props
    assert props["count"]["type"] == "integer"

def test_create_dynamic_tool():
    config = {
        "name": "fetch_data",
        "description": "Fetches data",
        "path": "/api/data/{type}",
        "method": "GET",
        "parameters": [
            {"name": "type", "type": "str", "description": "Data type"}
        ]
    }

    tool = create_dynamic_tool(config)
    assert tool.name == "fetch_data"
    assert tool.description == "Fetches data"
    assert "type" in tool.args

    # Test execution
    result = tool.invoke({"type": "metrics"})
    assert "Executed GET on /api/data/metrics" in result
