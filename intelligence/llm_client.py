import os
import time
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

class GeminiClient:
    # CLASS-LEVEL VARIABLES
    # These are shared across all instances of GeminiClient to enforce a global limit
    _last_call_time = 0
    _min_interval = 4.0  # Force 4 seconds between EVERY call (15 requests/min max)

    def __init__(self, model_name="gemini-2.0-flash"):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = model_name

    def _wait_for_slot(self):
        """
        Proactive Rate Limiting:
        Ensures we never call the API faster than _min_interval.
        """
        current_time = time.time()
        elapsed = current_time - GeminiClient._last_call_time
        
        if elapsed < GeminiClient._min_interval:
            wait_time = GeminiClient._min_interval - elapsed
            time.sleep(wait_time)
            
        GeminiClient._last_call_time = time.time()

    def _retry_on_limit(func):
        """
        Decorator to retry on 429 (Resource Exhausted) errors.
        Strategy: Exponential Backoff (10s -> 20s -> 40s -> 80s -> 160s)
        """
        def wrapper(self, *args, **kwargs):
            retries = 5 # Increased from 3
            delay = 10  # Start with 10s (Google resets usually take >5s)
            
            for attempt in range(retries):
                try:
                    # 1. Proactive Wait (Prevent hitting the limit)
                    self._wait_for_slot()
                    
                    # 2. Execute Request
                    return func(self, *args, **kwargs)
                    
                except Exception as e:
                    # 3. Reactive Wait (If we hit the limit anyway)
                    error_str = str(e).lower()
                    if "429" in error_str or "resource" in error_str or "quota" in error_str:
                        jitter = random.uniform(0, 2) # Randomness prevents "Thundering Herd"
                        wait_time = delay + jitter
                        print(f"      ⚠️ Rate limit hit (Attempt {attempt+1}/{retries}). Cooling down for {wait_time:.1f}s...")
                        
                        time.sleep(wait_time)
                        delay *= 2 # Double the wait for next time
                    else:
                        raise e  # Not a rate limit error, crash normally
                        
            raise Exception("CRITICAL: Max retries exceeded. API is fully saturated.")
        return wrapper

    @_retry_on_limit
    def generate_json(self, prompt: str) -> str:
        """Generates content expecting a JSON response."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return response.text

    @_retry_on_limit
    def generate_text(self, prompt: str) -> str:
        """Generates standard text content."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text

# --- COMPATIBILITY ADAPTER ---
class LLM_Client(GeminiClient):
    def __init__(self):
        super().__init__(model_name="gemini-2.0-flash")

    def generate(self, prompt: str) -> str:
        return self.generate_text(prompt)