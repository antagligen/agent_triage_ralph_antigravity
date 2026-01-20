import pytest
from unittest.mock import patch, MagicMock
from backend.src.dynamic_tools import create_dynamic_tool, ACIToolConfig, generic_aci_runner
import json

@pytest.fixture
def mock_tool_config():
    return ACIToolConfig(
        base_url="https://apic.example.com",
        username="admin",
        password="password123",
        verify_ssl=False
    )

def test_generic_aci_runner_url_construction(mock_tool_config):
    """Test that the runner constructs the correct URL from parameters."""
    path = "/api/node/mo/uni/tn-{tenant}.json"
    method = "GET"
    
    with patch("requests.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"totalCount": "1"}
        mock_request.return_value = mock_response

        result = generic_aci_runner(path, method, tool_config=mock_tool_config, tenant="solar")
        
        # Verify call arguments
        # Expected URL: https://apic.example.com/api/node/mo/uni/tn-solar.json
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "https://apic.example.com/api/node/mo/uni/tn-solar.json"
        
        # Verify result contains the JSON output
        assert '"totalCount": "1"' in result

def test_generic_aci_runner_error_handling(mock_tool_config):
    """Test that the runner handles HTTP errors gracefully."""
    path = "/api/error"
    method = "GET"
    
    with patch("requests.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        result = generic_aci_runner(path, method, tool_config=mock_tool_config)
        
        assert "Error 404" in result
        assert "Not Found" in result

def test_create_dynamic_tool_integration(mock_tool_config):
    """Test creating a tool and invoking it (integration with mocked runner)."""
    endpoint_config = {
        "name": "get_tenant_health",
        "description": "Get health",
        "path": "/api/node/mo/uni/tn-{tenant}.json",
        "method": "GET",
        "parameters": [
            {"name": "tenant", "type": "str", "description": "Tenant Name"}
        ]
    }
    
    tool = create_dynamic_tool(endpoint_config, tool_config=mock_tool_config)
    
    with patch("requests.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"imdata": []}
        mock_request.return_value = mock_response
        
        # Invoke via LangChain tool interface
        result = tool.invoke({"tenant": "common"})
        
        mock_request.assert_called_once()
        assert "https://apic.example.com/api/node/mo/uni/tn-common.json" in mock_request.call_args[1]["url"]
        assert '"imdata": []' in result
