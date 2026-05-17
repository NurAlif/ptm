"""
Gemini API Client
=================

A simple and reliable client for interacting with a local Gemini API endpoint.
Now with support for multiple LLM providers including DeepSeek.
"""

__version__ = "0.2.0"

# Import the core functions and constants to make them easily accessible
# from the top-level package.
# e.g., `import gemini_api_client`
# `gemini_api_client.query_api_with_retries(...)`
from .client import (
    query_api_with_retries,
    format_list_as_indexed_string,
    extract_json_from_text,
    MODEL_LITE,
    MODEL_FLASH,
    MODEL_PRO,
    API_URL
)

# DeepSeek client
from .deepseek_client import (
    query_deepseek_api,
    MODEL_DEEPSEEK_CHAT,
    MODEL_DEEPSEEK_REASONER,
    DEEPSEEK_API_URL,
)

# Unified client abstraction
from .unified_client import (
    query_llm,
    query_gemini_llm,
    query_deepseek_llm,
    LLMProvider,
    set_default_provider,
    get_default_provider,
    get_default_model,
)
