# Local AI Copilot, RAG Pipeline & Prompt Defense

FinAuditPro incorporates an air-gapped local AI copilot running against local LLM instances (LM Studio).

---

## 1. Zero Cloud Dependency & Air-Gapped Operation

- **Local REST Endpoint**: Connects to LM Studio via HTTP REST API (`http://localhost:1234/v1`).
- **Models**:
  - Chat / Extraction Model: `deepseek-r1-distill-qwen-14b` (or other local GGUF models)
  - Embedding Model: `nomic-embed-text`
- **Degraded Fallback**: If LM Studio is not running, FinAuditPro operates seamlessly in air-gapped mode with full access to deterministic financial analytics and statutory checklists.

---

## 2. Air-Gapped RAG Pipeline

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

## 3. Human Auditor Override

All AI outputs are explicitly labeled as `[AI Generated]`. The AI copilot acts strictly as an advisory assistant and has zero authority to alter financial records or bypass statutory rules.
