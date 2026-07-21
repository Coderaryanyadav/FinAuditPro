from typing import List, Dict, Any
from .vector_store import VectorStore
from core.exceptions import FinAuditError

class SecurityViolationError(FinAuditError):
    """Raised when cross-engagement retrieval is detected."""
    pass

class ContextRetriever:
    """
    Secures the RAG pipeline.
    Enforces strict metadata filtering by engagement_id.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve_context(self, query: str, engagement_id: int, client_id: int = None, k: int = 5) -> str:
        """
        Retrieves top K chunks, strictly filtering out any chunks 
        that do not belong to the active engagement_id.
        """
        if not engagement_id:
            raise SecurityViolationError("Context retrieval attempted without an active engagement_id!")

        raw_results = self.vector_store.search(query, k=k*3) # Fetch more to allow for filtering
        
        filtered_results = []
        for res in raw_results:
            if res.get("engagement_id") == engagement_id:
                if client_id and res.get("client_id") != client_id:
                    continue
                filtered_results.append(res)
                if len(filtered_results) >= k:
                    break

        if not filtered_results:
            return "No relevant context found in the uploaded documents."

        # Compile context string
        context_str = ""
        for i, res in enumerate(filtered_results):
            doc_name = res.get("document_name", "Unknown")
            page = res.get("page", "?")
            text = res.get("text", "")
            context_str += f"\n--- Document: {doc_name} (Page {page}) ---\n{text}\n"

        return context_str
