"""
Unified API Client
===================

A unified abstraction layer for querying different LLM providers (Gemini, DeepSeek).
Provides a consistent interface regardless of the backend used.
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from .client import (
    query_api_with_retries as query_gemini,
    MODEL_LITE,
    MODEL_FLASH,
    MODEL_PRO,
)
from .deepseek_client import (
    query_deepseek_api,
    MODEL_DEEPSEEK_CHAT,
    MODEL_DEEPSEEK_REASONER,
)

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class LLMProvider(Enum):
    """Available LLM providers."""
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


# Default provider
_default_provider = LLMProvider.GEMINI


def set_default_provider(provider: LLMProvider):
    """Set the default LLM provider globally."""
    global _default_provider
    _default_provider = provider
    logging.info(f"Default LLM provider set to: {provider.value}")


def get_default_provider() -> LLMProvider:
    """Get the current default LLM provider."""
    return _default_provider


def get_default_model(provider: LLMProvider) -> str:
    """Get the default model for a given provider."""
    if provider == LLMProvider.GEMINI:
        return MODEL_FLASH
    elif provider == LLMProvider.DEEPSEEK:
        return MODEL_DEEPSEEK_CHAT
    else:
        raise ValueError(f"Unknown provider: {provider}")


def query_llm(
    prompt: str,
    model: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    image: Optional[bytes] = None,
    max_retries: int = 1,
    initial_backoff: float = 1.0,
    timeout: int = 90,
    outjson: bool = True,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Unified function to query any supported LLM provider.
    
    This function provides a consistent interface for querying different LLM APIs.
    The output format is standardized regardless of which provider is used.

    Args:
        prompt: The prompt to send to the model.
        model: The model name to use. If None, uses the default for the provider.
        provider: The LLM provider to use. If None, uses the default provider.
        image: The raw bytes of the image file (only supported by Gemini).
        max_retries: Maximum number of times to retry the request.
        initial_backoff: Initial wait time in seconds before the first retry.
        timeout: How many seconds to wait for the server to send data.
        outjson: Whether to parse the response as JSON.
        **kwargs: Additional provider-specific arguments.

    Returns:
        The parsed response as a dictionary or text, or None if all retries fail.
        
    Example:
        # Using Gemini (default)
        result = query_llm("Hello, world!", model=MODEL_FLASH)
        
        # Using DeepSeek
        result = query_llm("Hello, world!", provider=LLMProvider.DEEPSEEK)
        
        # Using DeepSeek with specific model
        result = query_llm("Hello, world!", model=MODEL_DEEPSEEK_CHAT, provider=LLMProvider.DEEPSEEK)
    """
    # Determine provider
    active_provider = provider or _default_provider
    
    # Determine model
    active_model = model or get_default_model(active_provider)
    
    logging.info(f"Querying {active_provider.value} with model {active_model}")
    
    if active_provider == LLMProvider.GEMINI:
        return query_gemini(
            prompt=prompt,
            model=active_model,
            image=image,
            max_retries=max_retries,
            initial_backoff=initial_backoff,
            timeout=timeout,
            outjson=outjson,
            api_key=kwargs.get('api_key')
        )
    elif active_provider == LLMProvider.DEEPSEEK:
        return query_deepseek_api(
            prompt=prompt,
            model=active_model,
            image=image,
            max_retries=max_retries,
            initial_backoff=initial_backoff,
            timeout=timeout,
            outjson=outjson,
            api_key=kwargs.get('api_key')
        )
    else:
        raise ValueError(f"Unknown provider: {active_provider}")


# Convenience functions for specific providers
def query_gemini_llm(
    prompt: str,
    model: str = MODEL_FLASH,
    image: Optional[bytes] = None,
    max_retries: int = 1,
    initial_backoff: float = 1.0,
    timeout: int = 90,
    outjson: bool = True,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Query the Gemini API directly."""
    return query_llm(
        prompt=prompt,
        model=model,
        provider=LLMProvider.GEMINI,
        image=image,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        timeout=timeout,
        outjson=outjson,
        api_key=api_key
    )


def query_deepseek_llm(
    prompt: str,
    model: str = MODEL_DEEPSEEK_CHAT,
    max_retries: int = 1,
    initial_backoff: float = 1.0,
    timeout: int = 90,
    outjson: bool = True,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Query the DeepSeek API directly."""
    return query_llm(
        prompt=prompt,
        model=model,
        provider=LLMProvider.DEEPSEEK,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        timeout=timeout,
        outjson=outjson,
        api_key=api_key
    )
