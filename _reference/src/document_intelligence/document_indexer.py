"""
Document Vector Indexing & Ingestion Service for FinAuditPro.
Indexes document chunks and vector embeddings into FAISS VectorStore with engagement metadata metadata.
"""

from typing import List, Dict, Any
import logging

from ai.vector_store import VectorStore
from .chunking_engine import DocumentChunk
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """Indexes document chunks and embeddings into the local RAG vector store."""

    def __init__(self, vector_store: VectorStore = None, embedding_service: EmbeddingService = None):
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()

    def index_document_chunks(
        self,
        document_id: int,
        engagement_id: int,
        client_id: int,
        chunks: List[DocumentChunk]
    ) -> int:
        """
        Indexes chunks into vector store with engagement metadata filters.
        Returns total number of chunks successfully indexed.
        """
        if not chunks:
            return 0

        indexed_count = 0
        texts = [c.text for c in chunks]

        # Generate embeddings in batch
        embeddings = self.embedding_service.generate_embeddings_batch(texts)

        for chunk, embedding in zip(chunks, embeddings):
            meta = chunk.metadata.copy()
            meta.update({
                "document_id": document_id,
                "engagement_id": engagement_id,
                "client_id": client_id,
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type,
                "page_number": chunk.page_number,
            })

            # Add to vector store index
            self.vector_store.add_document_chunk(
                text=chunk.text,
                metadata=meta,
                embedding=embedding
            )
            indexed_count += 1

        logger.info(f"Successfully indexed {indexed_count} chunks for Document ID {document_id} (Engagement {engagement_id}).")
        return indexed_count
