"""
DeepSeek API Client
====================

A client for interacting with the DeepSeek API using OpenAI-compatible format.
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Any, Optional

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Constants ---
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_API_KEY = 'sk-c1113ea4fab04574977ded4be20873c8'

# DeepSeek models
MODEL_DEEPSEEK_CHAT = "deepseek-chat"  # DeepSeek V3 (non-thinking)
MODEL_DEEPSEEK_REASONER = "deepseek-reasoner"  # DeepSeek R1 (reasoning/thinking)


def extract_json_from_text(text: str):
    """Extract JSON from text, handling markdown code blocks."""
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"JSON in markdown block failed to parse: {e}")
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        obj_start = -1
        brace_start = text.find('{', idx)
        bracket_start = text.find('[', idx)
        if brace_start != -1 and bracket_start != -1:
            obj_start = min(brace_start, bracket_start)
        elif brace_start != -1:
            obj_start = brace_start
        elif bracket_start != -1:
            obj_start = bracket_start
        else:
            break
        try:
            result, _ = decoder.raw_decode(text, obj_start)
            return result
        except json.JSONDecodeError:
            idx = obj_start + 1
    logging.warning("Could not find any valid JSON object in the response text.")
    return None


def query_deepseek_api(
    prompt: str,
    model: str = MODEL_DEEPSEEK_CHAT,
    image: Optional[bytes] = None,
    max_retries: int = 1,
    initial_backoff: float = 1.0,
    timeout: int = 90,
    outjson: bool = True,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Posts a prompt to the DeepSeek API using OpenAI-compatible format.
    Handles retries with exponential backoff.

    Args:
        prompt: The prompt to send to the model.
        model: The model name to use (default: deepseek-chat for V3 non-thinking).
        image: The raw bytes of the image file (not supported by DeepSeek API, included for compatibility).
        max_retries: Maximum number of times to retry the request.
        initial_backoff: Initial wait time in seconds before the first retry.
        timeout: How many seconds to wait for the server to send data.
        outjson: Whether to parse the response as JSON.
        api_key: Optional API key override.

    Returns:
        The parsed response as a dictionary or text, or None if all retries fail.
    """
    backoff = initial_backoff
    key = api_key or DEEPSEEK_API_KEY

    if image:
        logging.warning("DeepSeek API does not support image input. Image will be ignored.")

    for attempt in range(max_retries):
        logging.info(f"[DeepSeek] Attempt {attempt + 1}/{max_retries} to query API for model {model}...")
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {key}'
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }

            response = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            response.raise_for_status()

            # Parse the OpenAI-compatible response format
            response_data = response.json()
            
            # Extract the content from the response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                message_content = response_data['choices'][0]['message']['content']
                
                if outjson:
                    parsed_data = extract_json_from_text(message_content)
                else:
                    parsed_data = message_content
                    
                if parsed_data:
                    logging.info("[DeepSeek] Successfully received and parsed API response.")
                    return parsed_data
                else:
                    raise ValueError("Response did not contain valid, extractable data.")
            else:
                raise ValueError("Unexpected response format from DeepSeek API.")

        except requests.exceptions.RequestException as e:
            logging.error(f"[DeepSeek] A network-related error occurred: {e}")
        except ValueError as e:
            logging.error(f"[DeepSeek] A data-related error occurred: {e}")

        if attempt < max_retries - 1:
            logging.info(f"[DeepSeek] Retrying in {backoff:.2f} seconds...")
            time.sleep(backoff)
            backoff *= 2
        else:
            logging.critical("[DeepSeek] All API query retries failed. Giving up.")

    return None
