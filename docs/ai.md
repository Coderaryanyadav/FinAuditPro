# FinAuditPro — Local AI Subsystem & RAG Pipeline

FinAuditPro incorporates a provider-agnostic local AI subsystem operating strictly against local LLM servers (LM Studio).

---

## 1. Provider Abstraction Architecture

The AI layer is isolated behind clear abstractions:
- `LLMProvider`: Handles chat completions and structured JSON generation.
- `EmbeddingProvider`: Computes vector embeddings for document chunks.

```
UI Widget ➔ AIAssistantView
            ⬇
Application ➔ AIService
            ⬇
Infrastructure ➔ LMStudioProvider (HTTP REST API: http://localhost:1234)
```

---

## 2. Air-Gapped RAG Pipeline

1. **Document Chunking**: Ingested document text is chunked into overlapping text segments.
2. **Vector Indexing**: Segments embedded via `nomic-embed-text` and stored in engagement-partitioned FAISS indices.
3. **Retrieval Scoping**: Search queries strictly scoped by `engagement_id`.
4. **Auditor Control**: AI suggestions display clear `[AI Generated]` badges and source page citations. The auditor retains complete manual override authority.
