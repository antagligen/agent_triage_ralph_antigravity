import pytest
import os
import yaml
from src.config import load_config, AppConfig

TEST_CONFIG_PATH = "test_config.yaml"

@pytest.fixture
def create_test_config():
    config_data = {
        "orchestrator_model": "test-gpt",
        "system_prompt": "Test Prompt",
        "sub_agents": [
            {
                "name": "test_agent",
                "description": "Test Agent Desc",
                "tools": ["tool1", "tool2"]
            }
        ]
    }
    with open(TEST_CONFIG_PATH, 'w') as f:
        yaml.dump(config_data, f)
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_CONFIG_PATH):
        os.remove(TEST_CONFIG_PATH)

def test_load_valid_config(create_test_config):
    config = load_config(TEST_CONFIG_PATH)
    assert isinstance(config, AppConfig)
    assert config.orchestrator_model == "test-gpt"
    assert len(config.sub_agents) == 1
    assert config.sub_agents[0].name == "test_agent"

def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.yaml")

def test_load_invalid_format():
    # Create a txt file
    with open("test.txt", 'w') as f:
        f.write("test")
        
    with pytest.raises(ValueError):
        load_config("test.txt")
        
    os.remove("test.txt")
