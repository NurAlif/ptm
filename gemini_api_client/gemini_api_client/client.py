import requests
import json
import time
import re
import logging
import os
import base64
from typing import List, Dict, Any, Optional

# --- Configuration (remains the same) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Constants ---
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
MODEL_LITE = "gemini-2.5-flash-lite"
MODEL_FLASH = "gemini-2.5-flash"
MODEL_PRO = "gemini-2.5-pro"

# --- Helper Functions ---
def format_list_as_indexed_string(items: List[str]) -> str:
    return "\n".join(f"{i}. {info}" for i, info in enumerate(items))

def extract_json_from_text(text: str):
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

def resolve_api_key(api_key: Optional[str] = None) -> str:
    """Resolve the Gemini API key from parameters, env, or .env files."""
    if api_key:
        return api_key
    
    # Try system environment variables first
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
        
    # Search for a .env file to load the key from
    dirs_to_check = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'admin_back')
    ]
    
    for d in dirs_to_check:
        env_path = os.path.join(d, '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip().strip('"').strip("'")
                            v = v.strip().strip('"').strip("'")
                            if k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                                logging.info(f"Loaded {k} from .env at {env_path}")
                                return v
            except Exception as e:
                logging.debug(f"Failed to read .env at {env_path}: {e}")
                
    # Fallback default key from workspace .env
    return 'AIzaSyBppA4IcOys-MSfXHnZoG5wK8cGXel9k2I'

# --- Core API Interaction ---

def query_api_with_retries(
    prompt: str,
    model: str,
    image: Optional[bytes] = None, # Make sure 'image' is in bytes
    max_retries: int = 1,
    initial_backoff: float = 1.0,
    timeout: int = 90,
    outjson: bool = True,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Posts a prompt and an optional image to the Gemini REST API directly.
    Handles retries with exponential backoff.

    Args:
        prompt: The prompt to send to the model.
        model: The model name to use.
        image: The raw bytes of the image file to send.
        max_retries: Maximum number of times to retry the request.
        initial_backoff: Initial wait time in seconds before the first retry.
        timeout: How many seconds to wait for the server to send data.
        outjson: Whether to parse the response as JSON.
        api_key: Optional API key override.

    Returns:
        The parsed response as a dictionary or text, or None if all retries fail.
    """
    backoff = initial_backoff
    key = resolve_api_key(api_key)

    for attempt in range(max_retries):
        logging.info(f"[Gemini] Attempt {attempt + 1}/{max_retries} to query API for model {model}...")
        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': key
            }

            # Prepare the content parts (text and optional base64 inline image data)
            if image:
                logging.info("[Gemini] Image detected, encoding as base64.")
                mime_type = "image/jpeg"
                if image.startswith(b'\x89PNG'):
                    mime_type = "image/png"
                elif image.startswith(b'GIF87a') or image.startswith(b'GIF89a'):
                    mime_type = "image/gif"
                elif image.startswith(b'RIFF') and b'WEBP' in image[:15]:
                    mime_type = "image/webp"
                
                base64_image = base64.b64encode(image).decode('utf-8')
                parts = [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_image
                        }
                    }
                ]
            else:
                parts = [{"text": prompt}]

            payload = {
                "contents": [{"parts": parts}]
            }

            # Construct direct API URL
            direct_api_url = f"{API_URL}/{model}:generateContent"

            response = requests.post(
                direct_api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            response.raise_for_status()

            # Parse response
            response_data = response.json()
            
            # Extract content from candidates
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    message_content = candidate['content']['parts'][0].get('text', '')
                    
                    if outjson:
                        parsed_data = extract_json_from_text(message_content)
                    else:
                        parsed_data = message_content
                        
                    if parsed_data is not None:
                        logging.info("[Gemini] Successfully received and parsed API response.")
                        return parsed_data
                    else:
                        raise ValueError("Response did not contain valid, extractable data.")
                else:
                    finish_reason = candidate.get('finishReason', 'UNKNOWN')
                    raise ValueError(f"No content found in Gemini response candidate. Finish reason: {finish_reason}")
            elif 'error' in response_data:
                err_msg = response_data['error'].get('message', 'Unknown API error')
                raise ValueError(f"Gemini API returned error: {err_msg}")
            else:
                raise ValueError("Unexpected response format from Gemini API.")

        except requests.exceptions.RequestException as e:
            logging.error(f"[Gemini] A network-related error occurred: {e}")
        except ValueError as e:
            logging.error(f"[Gemini] A data-related error occurred: {e}")

        if attempt < max_retries - 1:
            logging.info(f"[Gemini] Retrying in {backoff:.2f} seconds...")
            time.sleep(backoff)
            backoff *= 2
        else:
            logging.critical("[Gemini] All API query retries failed. Giving up.")

    return None