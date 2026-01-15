from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

def get_llm(provider: str, model_name: str, temperature: float = 0) -> BaseChatModel:
    """
    Factory function to create an LLM instance based on the provider.

    Args:
        provider: The model provider ('openai', 'google', 'gemini').
        model_name: The name of the model to use.
        temperature: The temperature for the model.

    Returns:
        BaseChatModel: The initialized chat model.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = provider.lower()
    
    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature)
    elif provider in ["google", "gemini"]:
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: openai, google, gemini")
