"""Pure Protocol interface for LLM / Embedding providers in FinAuditPro."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderStatus:
    is_server_up: bool
    chat_model_loaded: bool
    embedding_model_loaded: bool
    chat_model_id: str
    embedding_model_id: str
    details: str = ""


@dataclass(frozen=True)
class LLMResponse:
    content: str
    reasoning_text: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)
    prompt_tokens_est: int = 0
    completion_tokens_est: int = 0


class LLMProvider(Protocol):
    """Protocol declaring abstract interface for local or remote AI providers."""

    chat_model_id: str
    embedding_model_id: str

    def available(self) -> ProviderStatus:
        """Check provider server health and loaded model status."""
        ...

    def chat(
        self,
        messages: list[dict[str, str]],
        schema_class: Any | None = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        on_token: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        """Execute chat completion request with optional schema validation and token streaming."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for input texts."""
        ...

    def list_models(self) -> list[str]:
        """List available model IDs."""
        ...
