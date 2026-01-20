
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
import logging
from backend.src.config import load_system_prompt, DEFAULT_PROMPTS

# Test data
MOCK_AGENT_NAME = "test_agent"
MOCK_PROMPT_CONTENT = "This is a test prompt."


def test_load_system_prompt_success():
    """Test loading a system prompt from an existing file."""
    # We mock Path.read_text directly since the function uses it
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=MOCK_PROMPT_CONTENT):
            prompt = load_system_prompt(MOCK_AGENT_NAME)
            assert prompt == MOCK_PROMPT_CONTENT

def test_load_system_prompt_missing_file_with_default():
    """Test loading a system prompt when file is missing but default exists."""
    # Ensure the agent name is in DEFAULT_PROMPTS
    agent_name = "orchestrator"
    assert agent_name in DEFAULT_PROMPTS

    with patch("pathlib.Path.exists", return_value=False):
        # Patch the logger on the module where it is defined/used
        with patch("backend.src.config.logger.warning") as mock_log:
            prompt = load_system_prompt(agent_name)
            assert prompt == DEFAULT_PROMPTS[agent_name]
            mock_log.assert_called_once()
            # Verify the log message contains the path or "not found"
            assert "System prompt file not found" in mock_log.call_args[0][0]

def test_load_system_prompt_missing_file_no_default():
    """Test loading a system prompt when file is missing and no default exists."""
    unknown_agent = "unknown_agent"

    with patch("pathlib.Path.exists", return_value=False):
        prompt = load_system_prompt(unknown_agent)
        # Should return the generic fallback, not raise error
        assert prompt == f"You are a helpful {unknown_agent} agent."
