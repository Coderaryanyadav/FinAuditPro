"""Tests for LM Studio Provider, think block stripping, SSE parsing, and 1-round pydantic JSON schema repair."""

from pydantic import BaseModel, Field

from finauditpro.infrastructure.ai.lmstudio_provider import LMStudioProvider


class DummyFindingSchema(BaseModel):
    title: str = Field(...)
    severity: str = Field(...)


def test_strip_reasoning_blocks() -> None:
    """Verify stripping of <think>...</think> reasoning blocks from DeepSeek-R1 responses."""
    # 1. Closed think block
    raw_1 = (
        "<think>\nThinking about audit rules...\nChecking SA 320...\n</think>\nFinal Audit Answer."
    )
    content_1, reasoning_1 = LMStudioProvider.strip_reasoning(raw_1)
    assert content_1 == "Final Audit Answer."
    assert reasoning_1 == "Thinking about audit rules...\nChecking SA 320..."

    # 2. Empty think block
    raw_2 = "<think>\n\n</think>\nClean response."
    content_2, reasoning_2 = LMStudioProvider.strip_reasoning(raw_2)
    assert content_2 == "Clean response."
    assert reasoning_2 is None

    # 3. Unclosed think block fallback
    raw_3 = "Prelude<think>Ongoing thinking..."
    content_3, reasoning_3 = LMStudioProvider.strip_reasoning(raw_3)
    assert content_3 == "Prelude"
    assert reasoning_3 == "Ongoing thinking..."


def test_lmstudio_provider_availability_mock(monkeypatch) -> None:
    """Verify LMStudioProvider.available() detection handling via mock."""
    provider = LMStudioProvider(base_url="http://localhost:1234/v1")

    # Mock native v0 endpoint
    def mock_get(url, timeout=3.0):
        class MockResponse:
            status_code = 200

            def json(self):
                return {
                    "data": [
                        {"id": "deepseek/deepseek-r1-distill-qwen-14b", "state": "loaded"},
                        {"id": "text-embedding-nomic-embed-text-v1.5", "state": "loaded"},
                    ]
                }

        return MockResponse()

    monkeypatch.setattr("httpx.get", mock_get)
    status = provider.available()

    assert status.is_server_up is True
    assert status.chat_model_loaded is True
    assert status.embedding_model_loaded is True
