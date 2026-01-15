import pytest
from backend.src.llm_factory import get_llm
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Set dummy keys for testing instantiation
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["GOOGLE_API_KEY"] = "dummy"

def test_get_llm_openai():
    llm = get_llm("openai", "gpt-4o")
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o"

def test_get_llm_google():
    llm = get_llm("google", "gemini-pro")
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model == "gemini-pro"

def test_get_llm_gemini_alias():
    llm = get_llm("gemini", "gemini-pro")
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model == "gemini-pro"

def test_get_llm_invalid_provider():
    with pytest.raises(ValueError):
        get_llm("invalid", "model")
