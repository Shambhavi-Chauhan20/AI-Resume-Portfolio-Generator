"""
gemini_client.py
Owns: environment/API key setup + the Gemini connection function.

Interface contract with Dev 2:
    get_gemini_response(prompt: str) -> str

Dev 2 builds a fake version of this (returns hardcoded sample JSON) to build
parsing/rendering without waiting on the real API. At integration time, swap
their fake for this real one — one import line change in app.py.
"""

import os
import time
from dotenv import load_dotenv
import google.genai as genai
from google.genai import errors

# Explicitly load .env from the root directory (parent of backend)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Fail loudly at startup if the key is missing — don't let the app silently
# break later when the first request comes in.
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Create a .env file (see .env.example) "
        "and set GEMINI_API_KEY=your_key_here before starting the app."
    )

_client = genai.Client(api_key=GEMINI_API_KEY)

# Use the latest stable flash model as requested by the API error.
MODEL_NAME = "gemini-3.6-flash"


class GeminiRequestError(Exception):
    """Raised when the Gemini API call fails in a way callers should handle
    gracefully (network issue, rate limit, API error) instead of crashing."""
    pass


def get_gemini_response(prompt: str) -> str:
    """
    Sends a prompt to Gemini, returns raw text response.

    Raises GeminiRequestError on any failure so app.py can catch one
    exception type and return a clean error to the frontend instead of
    crashing the request.
    """
    max_retries = 3
    base_delay = 1.0  # seconds
    for attempt in range(max_retries + 1):
        try:
            response = _client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiRequestError("Gemini returned an empty response.")
            return text
        except errors.APIError as e:
            # 503 (Unavailable) or 429 (Resource Exhausted) are transient
            is_transient = (e.code in (429, 503))
            if is_transient and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"Transient error {e.code} on attempt {attempt + 1}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            
            raise GeminiRequestError(f"Gemini API request failed: {e}") from e
        except Exception as e:
            raise GeminiRequestError(f"Gemini API request failed: {e}") from e


if __name__ == "__main__":
    # Quick manual test: run `python gemini_client.py` to confirm you're
    # getting a real response back before wiring this into the Flask app.
    try:
        result = get_gemini_response("Say hello in one short sentence.")
        print("Gemini response:", result)
    except GeminiRequestError as e:
        print("Gemini call failed:", e)
