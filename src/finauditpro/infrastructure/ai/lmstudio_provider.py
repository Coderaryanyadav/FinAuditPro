"""LM Studio Provider implementation using raw httpx REST calls (OpenAI API compatible)."""

import json
import re
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from finauditpro.application.ai.llm_provider import LLMProvider, LLMResponse, ProviderStatus


class LMStudioProvider(LLMProvider):
    """Local AI Provider talking to LM Studio via raw httpx."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        chat_model_id: str = "deepseek/deepseek-r1-distill-qwen-14b",
        embedding_model_id: str = "text-embedding-nomic-embed-text-v1.5",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model_id = chat_model_id
        self.embedding_model_id = embedding_model_id
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def strip_reasoning(text: str) -> tuple[str, str | None]:
        """Strip <think>...</think> reasoning blocks from DeepSeek-R1 responses."""
        if not text:
            return "", None

        think_match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            clean_content = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return clean_content, reasoning if reasoning else None

        # Fallback for unclosed <think> tag
        if "<think>" in text:
            parts = text.split("<think>", 1)
            reasoning = parts[1].strip()
            return parts[0].strip(), reasoning if reasoning else None

        return text.strip(), None

    def available(self) -> ProviderStatus:
        """Check LM Studio health and status of loaded models."""
        try:
            # 1. Native API v0 check
            v0_url = f"{self.base_url.rsplit('/v1', 1)[0]}/api/v0/models"
            resp = httpx.get(v0_url, timeout=0.5)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    models = [m.get("id", "") for m in data if m.get("id")]
                    chat_match = next((m for m in models if "embed" not in m.lower()), models[0])
                    if chat_match:
                        self.chat_model_id = chat_match

                    chat_loaded = len(models) > 0
                    embed_loaded = (
                        any("embed" in m.lower() or "nomic" in m.lower() for m in models)
                        or self.embedding_model_id in models
                    )

                    return ProviderStatus(
                        is_server_up=True,
                        chat_model_loaded=chat_loaded,
                        embedding_model_loaded=embed_loaded,
                        chat_model_id=self.chat_model_id,
                        embedding_model_id=self.embedding_model_id,
                        details="LM Studio API v0 active",
                    )
        except Exception:
            pass

        # 2. Fallback OpenAI v1 /models endpoint check
        try:
            resp = httpx.get(f"{self.base_url}/models", timeout=0.5)

            if resp.status_code == 200:
                data = resp.json().get("data", [])
                models = [m.get("id", "") for m in data if m.get("id")]
                if models:
                    # Primary active model loaded in memory is always returned first
                    chat_match = next((m for m in models if "embed" not in m.lower()), models[0])
                    if chat_match:
                        self.chat_model_id = chat_match

                    chat_present = len(models) > 0
                    embed_present = (
                        any("embed" in m.lower() or "nomic" in m.lower() for m in models)
                        or self.embedding_model_id in models
                    )

                    return ProviderStatus(
                        is_server_up=True,
                        chat_model_loaded=chat_present,
                        embedding_model_loaded=embed_present,
                        chat_model_id=self.chat_model_id,
                        embedding_model_id=self.embedding_model_id,
                        details="LM Studio API v1 active",
                    )
        except Exception as ex:
            return ProviderStatus(
                is_server_up=False,
                chat_model_loaded=False,
                embedding_model_loaded=False,
                chat_model_id=self.chat_model_id,
                embedding_model_id=self.embedding_model_id,
                details=f"Unreachable: {ex}",
            )

        return ProviderStatus(
            is_server_up=False,
            chat_model_loaded=False,
            embedding_model_loaded=False,
            chat_model_id=self.chat_model_id,
            embedding_model_id=self.embedding_model_id,
            details="LM Studio endpoint returned non-200",
        )

    def list_models(self) -> list[str]:
        """List available model IDs on LM Studio."""
        try:
            resp = httpx.get(f"{self.base_url}/models", timeout=5.0)
            if resp.status_code == 200:
                return [m.get("id") for m in resp.json().get("data", []) if m.get("id")]
        except Exception:
            pass
        return []

    def _execute_chat_call(
        self,
        payload: dict[str, Any],
        on_token: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        """Execute single POST to /v1/chat/completions."""
        url = f"{self.base_url}/chat/completions"
        if on_token:
            payload["stream"] = True
            accumulated_chunks: list[str] = []
            with httpx.Client(timeout=self.timeout_seconds) as client:
                with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise RuntimeError(
                            f"LM Studio API returned HTTP {response.status_code}: {response.read().decode('utf-8')}"
                        )

                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    accumulated_chunks.append(token)
                                    on_token(token)
                            except Exception:
                                pass

            raw_text = "".join(accumulated_chunks)
            clean_content, reasoning = self.strip_reasoning(raw_text)
            return LLMResponse(
                content=clean_content,
                reasoning_text=reasoning,
                prompt_tokens_est=len(json.dumps(payload.get("messages", []))) // 4,
                completion_tokens_est=len(raw_text) // 4,
            )

        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"LM Studio API returned HTTP {resp.status_code}: {resp.text}")

            resp_data = resp.json()
            raw_text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            clean_content, reasoning = self.strip_reasoning(raw_text)
            return LLMResponse(
                content=clean_content,
                reasoning_text=reasoning,
                raw_response=resp_data,
                prompt_tokens_est=len(json.dumps(payload.get("messages", []))) // 4,
                completion_tokens_est=len(raw_text) // 4,
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        schema_class: type[BaseModel] | None = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        on_token: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        """Execute chat completion request with optional schema validation and token streaming."""
        # Auto-probe live server to sync model ID identifier
        status = self.available()
        if not status.is_server_up:
            raise RuntimeError("LM Studio server is offline or unreachable.")

        payload: dict[str, Any] = {
            "model": self.chat_model_id,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }

        if schema_class is not None and issubclass(schema_class, BaseModel):
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_class.__name__.lower(),
                    "strict": "true",
                    "schema": schema_class.model_json_schema(),
                },
            }

        try:
            return self._execute_chat_call(payload, on_token=on_token)
        except Exception:
            # Fallback: try fetching models and retry with first available model ID
            avail = self.list_models()
            if avail:
                fallback_model = next((m for m in avail if "embed" not in m.lower()), avail[0])
                payload["model"] = fallback_model
                self.chat_model_id = fallback_model
                return self._execute_chat_call(payload, on_token=on_token)
            raise

        if schema_class is not None and issubclass(schema_class, BaseModel):
            try:
                # Attempt to extract JSON from response content
                json_text = response.content.strip()
                if "```json" in json_text:
                    json_text = json_text.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in json_text:
                    json_text = json_text.split("```", 1)[1].split("```", 1)[0].strip()

                schema_class.model_validate_json(json_text)
                return response
            except (ValidationError, Exception) as err:
                # 1-Round Schema Repair Attempt
                repair_messages = list(messages) + [
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": f"YOUR PREVIOUS RESPONSE FAILED JSON VALIDATION: {err}. Return ONLY valid JSON adhering exactly to schema: {json.dumps(schema_class.model_json_schema())}",
                    },
                ]
                repair_payload = dict(payload)
                repair_payload["messages"] = repair_messages
                repair_response = self._execute_chat_call(repair_payload, on_token=None)

                repair_text = repair_response.content.strip()
                if "```json" in repair_text:
                    repair_text = repair_text.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in repair_text:
                    repair_text = repair_text.split("```", 1)[1].split("```", 1)[0].strip()

                schema_class.model_validate_json(repair_text)
                return repair_response

        return response

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via LM Studio /v1/embeddings endpoint."""
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.embedding_model_id,
            "input": texts,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"LM Studio Embeddings API error HTTP {resp.status_code}: {resp.text}"
                )

            data = resp.json().get("data", [])
            embeddings: list[list[float]] = []
            for item in data:
                embeddings.append(item.get("embedding", []))
            return embeddings
