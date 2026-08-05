import requests
import json
import time
import logging
from typing import Dict, Any, Generator, Optional
from core.exceptions import FinAuditError

from core.config import config

logger = logging.getLogger(__name__)

class OllamaClientError(FinAuditError):
    pass

class OllamaClient:
    """
    Handles robust communication with the local Ollama daemon.
    Automatically detects installed local models (llama3.2, qwen2.5-coder, etc.).
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or config.ollama_host
        self.timeout = 120  # 2 minutes for deep audit reasoning
        self.model = model or self._auto_detect_model()

    def _auto_detect_model(self) -> str:
        """Find best installed Ollama model automatically."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if res.status_code == 200:
                models = [m.get("name", "") for m in res.json().get("models", [])]
                for preferred in ["llama3.2:latest", "llama3.2", "qwen2.5-coder:14b", "qwen3-coder:latest"]:
                    if preferred in models or any(preferred in m for m in models):
                        logger.info(f"Auto-selected Ollama model: {preferred}")
                        return preferred
                if models:
                    logger.info(f"Selected first available Ollama model: {models[0]}")
                    return models[0]
                logger.info("Ollama service active but 0 models downloaded.")
                return ""
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.warning(f"Failed to query Ollama models: {e}")
        return ""

    @staticmethod
    def is_available(base_url: Optional[str] = None) -> bool:
        """Quick check whether local Ollama daemon is reachable AND has installed models."""
        try:
            from core.config import config as _cfg
            url = base_url or _cfg.ollama_host
            res = requests.get(f"{url}/api/tags", timeout=3)
            if res.status_code == 200:
                models = res.json().get("models", [])
                return len(models) > 0
            return False
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False, retries: int = 3) -> str:
        """Synchronous generation with retries."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0  # Strict determinism for auditing
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        if json_mode:
            payload["format"] = "json"

        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                return response.json().get("response", "")
            except requests.RequestException as e:
                if attempt == retries - 1:
                    raise OllamaClientError(f"Ollama connection failed after {retries} attempts: {e}")
                time.sleep(2 ** attempt)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Helper alias for worker stream/sync execution."""
        return self.generate(prompt=prompt, system_prompt=system_prompt, json_mode=False)

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """Stream generation for UI responsiveness."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
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
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            raise OllamaClientError(f"Streaming failed: {e}")
