import requests
import json
import time
from typing import Dict, Any, Generator
from core.exceptions import FinAuditError

class OllamaClientError(FinAuditError):
    pass

class OllamaClient:
    """
    Handles robust communication with the local Ollama daemon.
    Never hardcodes endpoints or models.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self.timeout = 120  # 2 minutes for deep audit thinking

    def generate(self, prompt: str, system_prompt: str = None, retries: int = 3) -> str:
        """Synchronous generation with retries."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0 # Strict determinism for auditing
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        # Enforce JSON mode (supported by modern Ollama)
        payload["format"] = "json"

        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                return response.json().get("response", "")
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == retries - 1:
                    raise OllamaClientError(f"Ollama connection failed after {retries} attempts: {e}")
                time.sleep(2 ** attempt) # Exponential backoff

    def generate_stream(self, prompt: str, system_prompt: str = None) -> Generator[str, None, None]:
        """Stream generation for UI responsiveness (if needed)."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "format": "json",
            "options": {"temperature": 0.0}
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with requests.post(url, json=payload, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk.get("response", "")
        except Exception as e:
            raise OllamaClientError(f"Streaming failed: {e}")
