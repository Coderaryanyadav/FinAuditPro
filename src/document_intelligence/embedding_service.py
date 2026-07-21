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
        except Exception as e:
            logger.warning(f"SentenceTransformer not available ({e}). Using deterministic fallback embeddings.")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        if self._model:
            try:
                embedding = self._model.encode(text).tolist()
                return embedding
            except Exception as e:
                logger.error(f"Embedding encoding failed: {e}")

        # Deterministic feature hashing fallback vector
        return self._fallback_hash_embedding(text)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation for efficiency."""
        if self._model and texts:
            try:
                embeddings = self._model.encode(texts).tolist()
                return embeddings
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")

        return [self._fallback_hash_embedding(t) for t in texts]

    def _fallback_hash_embedding(self, text: str) -> List[float]:
        """Generates a deterministic normalized 384-dimensional vector from SHA-256 hash."""
        vec = []
        seed_bytes = text.encode("utf-8")
        for i in range(self.EMBEDDING_DIM):
            chunk_hash = hashlib.sha256(seed_bytes + str(i).encode("utf-8")).digest()
            val = (int.from_bytes(chunk_hash[:4], "big") / (2**32 - 1)) * 2.0 - 1.0
            vec.append(round(val, 6))
        return vec
