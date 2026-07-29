# FinAuditPro - Architecture Guide

## High-Level Architecture
FinAuditPro is built using a strict **Clean Architecture** paradigm. 
- **Presentation Layer**: PySide6 UI widgets.
- **Service Layer**: Orchestrates business logic and security.
- **Repository Layer**: Interfaces with the SQLite database via SQLAlchemy.
- **Core Entities**: Pure Python dataclasses representing business domain models.

## Security Architecture
The application runs entirely offline.
- **Database**: SQLite running in WAL mode with PRAGMA cache optimizations for ARM64/x86_64 concurrency.
- **Encryption**: Sensitive fields are encrypted using AES-256 (Fernet) via `AESCryptoEngine`. Keys are derived using PBKDF2 with salt and hardware-specific constants.
- **Audit Logging**: Every action generates a SHA-256 hash that links to the previous action, forming an immutable ledger.

## AI Pipeline
1. **Document Ingestion**: `ocr_engine.py` extracts text via PaddleOCR.
2. **Chunking & Embedding**: Text is chunked (500 tokens) and embedded using local Transformer models.
3. **Vector Search**: Embeddings are indexed using FAISS (`embedding_service.py`).
4. **LLM Inference**: The `OllamaService` queries local LLMs (e.g., Llama-3) by injecting relevant FAISS chunks into the context window (RAG).
5. **Rule Engine**: Deterministic rules (`AuditRuleEngine`) execute alongside the AI to flag hard numerical mismatches.
