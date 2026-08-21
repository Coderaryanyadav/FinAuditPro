"""Factory helper constructing AIService instance for PySide6 UI without violating UI architectural purity."""

from pathlib import Path
from typing import Any

from finauditpro.application.services.ai_service import AIService
from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
from finauditpro.infrastructure.ai.lmstudio_provider import LMStudioProvider


def create_ai_service(db_manager: Any) -> AIService:
    """Factory creating AIService with LMStudioProvider and FAISSVectorStore."""
    provider = LMStudioProvider()
    storage_path = Path.home() / ".finauditpro" / "ai_indices"
    vector_store = FAISSVectorStore(storage_path)
    return AIService(db_manager, provider=provider, vector_store=vector_store)
