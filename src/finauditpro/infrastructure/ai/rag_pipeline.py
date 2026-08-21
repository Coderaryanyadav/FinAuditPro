"""Retrieval-Augmented Generation (RAG) Vector Indexing and Context Assembly Pipeline."""

import math
from dataclasses import dataclass, field
from typing import Any

from finauditpro.infrastructure.ai.provider import BaseAIProvider


@dataclass
class DocumentChunk:
    chunk_id: str
    engagement_id: str
    document_id: str
    filename: str
    category: str
    page_number: int
    chunk_index: int
    text: str
    embedding: list[float] = field(default_factory=list)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two vector embeddings."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class LocalVectorStore:
    """Thread-safe vector index storing DocumentChunks with engagement isolation."""

    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []

    def clear_engagement(self, engagement_id: str) -> None:
        self.chunks = [c for c in self.chunks if c.engagement_id != engagement_id]

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.chunks.extend(chunks)

    def search(
        self, engagement_id: str, query_embedding: list[float], top_k: int = 3
    ) -> list[tuple[DocumentChunk, float]]:
        """Search top-k vector chunks strictly scoped to engagement_id."""
        results: list[tuple[DocumentChunk, float]] = []

        for chunk in self.chunks:
            if chunk.engagement_id != engagement_id:
                continue
            sim = cosine_similarity(query_embedding, chunk.embedding)
            results.append((chunk, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class RAGPipeline:
    """RAG pipeline managing document chunking, embedding, indexing, and retrieval."""

    def __init__(
        self, provider: BaseAIProvider, vector_store: LocalVectorStore | None = None
    ) -> None:
        self.provider = provider
        self.vector_store = vector_store or LocalVectorStore()

    def chunk_and_index_pages(
        self,
        engagement_id: str,
        document_id: str,
        filename: str,
        category: str,
        pages: list[dict[str, Any]],
        chunk_size: int = 400,
    ) -> list[DocumentChunk]:
        """Chunk page text into overlapping windows and compute embeddings."""
        new_chunks: list[DocumentChunk] = []

        for p_data in pages:
            page_num = int(p_data.get("page_number", 1))
            text = str(p_data.get("extracted_text", "")).strip()
            if not text:
                continue

            # Sliding window chunking
            start = 0
            chunk_idx = 1
            while start < len(text):
                end = min(len(text), start + chunk_size)
                chunk_str = text[start:end].strip()
                if chunk_str:
                    emb = self.provider.embed_text(chunk_str)
                    chk = DocumentChunk(
                        chunk_id=f"{document_id}_p{page_num}_c{chunk_idx}",
                        engagement_id=engagement_id,
                        document_id=document_id,
                        filename=filename,
                        category=category,
                        page_number=page_num,
                        chunk_index=chunk_idx,
                        text=chunk_str,
                        embedding=emb,
                    )
                    new_chunks.append(chk)
                    chunk_idx += 1
                start += chunk_size - 50  # 50-char overlap

        self.vector_store.add_chunks(new_chunks)
        return new_chunks

    def retrieve_context(
        self, engagement_id: str, query: str, top_k: int = 3
    ) -> list[tuple[DocumentChunk, float]]:
        """Retrieve top relevant document chunks for query."""
        query_emb = self.provider.embed_text(query)
        return self.vector_store.search(engagement_id, query_emb, top_k=top_k)
