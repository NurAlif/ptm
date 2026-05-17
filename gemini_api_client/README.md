# Gemini API Client

A high-performance, robust, and unified API client library built for seamless integration with Google's Gemini LLMs. It supports direct connection to the Gemini API, smart fallbacks, comprehensive error handling, and structured JSON output parity.

## Features

- **Direct API Access**: Bypasses intermediate proxy endpoints to query the Gemini API directly.
- **Unified Client Interface**: Simple and intuitive interface for single or multiple prompt evaluations.
- **Structured Outputs**: Formats model output cleanly in exact JSON structures required by downstream tools.
- **Local Dev Mode Support**: Standard PEP-517 configuration for easy local installation and live hot-reloading during development.

---

## Installation

### 0  Setup Python and Nodejs Enviroment

#### Python
```bash
pip install -r requirements.txt
```

### 1. Standard Production Mode
To install the client as a regular package in your Python environment:
```bash
pip install .
```

### 2. Development Mode (Editable)
To install the package in **development / editable mode** (so any changes you make to the client source files are immediately active across your running servers without reinstalling):

Run from the root of this module's directory (`gemini_api_client`):
```bash
pip install -e .
```

Or install it directly from the backend directory using its relative path:
```bash
pip install -e ../gemini_api_client
```

---

## Usage Example

```python
from gemini_api_client import UnifiedGeminiClient

client = UnifiedGeminiClient(api_key="YOUR_GEMINI_API_KEY")

response = client.generate_content(
    prompt="Explain quantum computing in one sentence.",
    model="gemini-2.5-flash"
)

print(response)
```
