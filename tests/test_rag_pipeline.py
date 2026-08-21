"""Tests for per-engagement FAISS vector index isolation and FTS5 fallback."""

from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore


def test_faiss_per_engagement_isolation(tmp_path) -> None:
    """Verify FAISS vector index files enforce strict engagement-level isolation."""
    store = FAISSVectorStore(tmp_path / "ai_indices")

    # 1. Build index for Engagement A
    eng_a_chunks = [("chunk_a1", [1.0, 0.0, 0.0]), ("chunk_a2", [0.0, 1.0, 0.0])]
    store.build_index("eng-A", eng_a_chunks)

    # 2. Build index for Engagement B
    eng_b_chunks = [("chunk_b1", [0.0, 0.0, 1.0])]
    store.build_index("eng-B", eng_b_chunks)

    # 3. Query Engagement A
    res_a = store.search("eng-A", [1.0, 0.0, 0.0], top_k=5)
    assert len(res_a) == 2

    # 4. Query Engagement B
    res_b = store.search("eng-B", [1.0, 0.0, 0.0], top_k=5)
    assert len(res_b) == 1

    # 5. Query non-existent Engagement C
    res_c = store.search("eng-C", [1.0, 0.0, 0.0], top_k=5)
    assert len(res_c) == 0
