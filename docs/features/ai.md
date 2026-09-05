# Local AI Copilot, RAG Pipeline & Prompt Defense

FinAuditPro incorporates an optional local AI assistant running against local LLM instances (via LM Studio) with zero outbound client data transmission.

---

## 1. Zero Cloud Dependency & Local Operation

- **Local REST Endpoint**: Interfaces with local LM Studio via loopback HTTP REST API (`http://localhost:1234/v1`).
- **Models**:
  - Chat / Extraction Model: `deepseek-r1-distill-qwen-14b` (or compatible local GGUF models)
  - Embedding Model: `nomic-embed-text`
- **Degraded Fallback**: If LM Studio is not running, FinAuditPro operates seamlessly with full access to deterministic financial analytics and statutory checklists while AI advisory features remain gracefully disabled.

---

## 2. Local RAG Pipeline

```text
Document Text Chunks
        ⬇
Local Embeddings (nomic-embed-text)
        ⬇
Engagement-Partitioned FAISS Vector Index
        ⬇
Top-k Vector Similarity Search (or SQLite FTS5 fallback)
        ⬇
Prompt Engine (Neutralizes <think> & injection tokens)
        ⬇
Local Chat Inference (LM Studio)
        ⬇
Pydantic Schema Validation & 1-Round Auto Repair
        ⬇
Auditor UI Output with [AI Generated] Disclaimer & Citations
```

---

## 3. Human Auditor Override & Statutory Notice

All AI outputs are explicitly labeled with `[AI Advisory]`. The local AI assistant acts strictly as an advisory tool and possesses zero authority to modify database state, compute official accounting balances, or bypass statutory review procedures.
