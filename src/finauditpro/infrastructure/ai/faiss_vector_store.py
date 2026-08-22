"""Engagement-partitioned FAISS Vector Store manager."""

from pathlib import Path

import faiss
import numpy as np


class FAISSVectorStore:
    """FAISS vector store maintaining strict per-engagement index isolation on disk."""

    def __init__(self, storage_dir: Path | str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_index_path(self, engagement_id: str) -> Path:
        """Return hard-isolated index path for an engagement."""
        safe_id = "".join(c for c in engagement_id if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"eng_{safe_id}.faiss"

    def build_index(
        self,
        engagement_id: str,
        chunk_embeddings: list[tuple[str, list[float]]],
    ) -> int:
        """Build and persist FAISS IndexFlatIP for an engagement."""
        if not chunk_embeddings:
            index_path = self._get_index_path(engagement_id)
            if index_path.exists():
                index_path.unlink()
            return 0

        dimension = len(chunk_embeddings[0][1])
        vectors = np.array([emb for _, emb in chunk_embeddings], dtype=np.float32)

        # Normalize vectors for cosine similarity via Inner Product
        faiss.normalize_L2(vectors)

        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)

        index_path = self._get_index_path(engagement_id)
        faiss.write_index(index, str(index_path))
        return index.ntotal

    def search(
        self,
        engagement_id: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """Search top_k nearest neighbor chunk positions in engagement's FAISS index."""
        index_path = self._get_index_path(engagement_id)
        if not index_path.exists():
            return []

        index = faiss.read_index(str(index_path))
        if index.ntotal == 0:
            return []

        q_arr = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_arr)

        scores, indices = index.search(q_arr, min(top_k, index.ntotal))

        results: list[tuple[int, float]] = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx != -1:
                results.append((int(idx), float(score)))

        return results


    def delete_index(self, engagement_id: str) -> None:
        """Delete an engagement's FAISS index file."""
        index_path = self._get_index_path(engagement_id)
        if index_path.exists():
            index_path.unlink()
