"""
Vector Embedding Service Module for FinAuditPro.
Generates high-dimensional vector embeddings for text chunks.
"""

from typing import List
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generates numerical vector embeddings for semantic document chunks."""

    EMBEDDING_DIM = 384  # Standard size for lightweight financial sentence-transformers

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"SentenceTransformer not available ({e}). Vector embedding capabilities disabled.")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        if self._model:
            try:
                embedding = self._model.encode(text).tolist()
                return embedding
            except (OSError, ValueError, RuntimeError) as e:
                logger.error(f"Embedding encoding failed: {e}")
                raise RuntimeError(f"Embedding encoding failed: {e}")

        raise RuntimeError("Vector embedding model is unavailable. Ingestion halted to prevent corrupt index state.")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation for efficiency."""
        if self._model and texts:
            try:
                embeddings = self._model.encode(texts).tolist()
                return embeddings
            except (OSError, ValueError, RuntimeError) as e:
                logger.error(f"Batch embedding failed: {e}")
                raise RuntimeError(f"Batch embedding failed: {e}")

        raise RuntimeError("Vector embedding model is unavailable. Ingestion halted to prevent corrupt index state.")
