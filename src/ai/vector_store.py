"""
FAISS Vector Store Engine for FinAuditPro.
Provides offline vector indexing, semantic search, and document metadata mapping.
"""

from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class VectorStoreError(Exception):
    pass


class VectorStore:
    """
    Wraps FAISS for offline high-performance vector search.
    Supports metadata filtering, embedding computation, and persistence.
    """

    def __init__(self, index_path: str = "data/faiss_index.bin"):
        self.index_path = index_path
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self._next_id = 0
        self._embedding_service = None
        self._index = None
        self._dim = 384
        self._initialize_faiss()

    def _initialize_faiss(self):
        try:
            from document_intelligence.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
            self._dim = self._embedding_service.EMBEDDING_DIM
        except Exception as e:
            logger.warning(f"EmbeddingService initialization in VectorStore: {e}")

        try:
            import faiss
            self._index = faiss.IndexFlatL2(self._dim)
            logger.info("Initialized FAISS IndexFlatL2 for VectorStore.")
        except Exception as e:
            logger.warning(f"FAISS not available ({e}). Falling back to memory search.")
            self._index = None

    def add_document_chunk(self, text: str, metadata: Dict[str, Any], embedding: Optional[List[float]] = None) -> None:
        """Add a single document chunk with metadata and embedding to vector store."""
        self.add_texts([text], [metadata], embeddings=[embedding] if embedding else None)

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None) -> None:
        """Embeds text and adds vectors + metadata to FAISS index."""
        if len(texts) != len(metadatas):
            raise VectorStoreError("Texts and metadata lists must be same length.")
        if not texts:
            return

        if embeddings is None and self._embedding_service:
            try:
                embeddings = self._embedding_service.generate_embeddings_batch(texts)
            except Exception as e:
                logger.warning(f"Embedding batch generation fallback: {e}")

        if self._index is not None and embeddings:
            try:
                import numpy as np
                vecs = np.array(embeddings, dtype=np.float32)
                self._index.add(vecs)
            except Exception as e:
                logger.warning(f"Failed to add vectors to FAISS index: {e}")

        for i, meta in enumerate(metadatas):
            self.metadata[self._next_id] = {
                "text": texts[i],
                "embedding": embeddings[i] if (embeddings and i < len(embeddings)) else None,
                **meta
            }
            self._next_id += 1

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search vector database by semantic similarity query string."""
        if not self.metadata or not query:
            return []

        if self._embedding_service and self._index is not None and getattr(self._index, 'ntotal', 0) > 0:
            try:
                import numpy as np
                query_vector = self._embedding_service.generate_embedding(query)
                q_arr = np.array([query_vector], dtype=np.float32)
                distances, indices = self._index.search(q_arr, min(k, self._index.ntotal))

                results = []
                for dist, idx in zip(distances[0], indices[0]):
                    if idx in self.metadata:
                        item = self.metadata[idx].copy()
                        item["score"] = float(dist)
                        results.append(item)
                return results
            except Exception as e:
                logger.warning(f"FAISS search failed ({e}). Falling back to keyword matching.")

        # Fallback keyword match search
        query_lower = query.lower()
        matched = []
        for idx, item in self.metadata.items():
            text = item.get("text", "")
            if query_lower in text.lower():
                res = item.copy()
                res["score"] = 0.5
                matched.append(res)
                if len(matched) >= k:
                    break
        return matched

    def delete_by_document_id(self, document_id: int) -> None:
        """Remove all chunks associated with a specific document ID."""
        to_delete = [idx for idx, meta in self.metadata.items() if meta.get("document_id") == document_id]
        for idx in to_delete:
            del self.metadata[idx]
        logger.info(f"Removed {len(to_delete)} vector store chunks for Document ID {document_id}.")

