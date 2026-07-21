# FinAuditPro System Architecture & Engineering Specifications

## 1. High-Level Architecture

FinAuditPro enforces a strict Clean Architecture pattern. Every metric, audit finding, report table, and dashboard visualization is driven strictly from the database outward:

$$\text{SQLite} \rightarrow \text{SQLAlchemy} \rightarrow \text{Repositories} \rightarrow \text{Services} \rightarrow \text{Business Logic} \rightarrow \text{Workflow} \rightarrow \text{Rule Engine} \rightarrow \text{OCR} \rightarrow \text{Embeddings} \rightarrow \text{FAISS} \rightarrow \text{LLM} \rightarrow \text{Report Engine} \rightarrow \text{Analytics} \rightarrow \text{PySide6 UI}$$

---

## 2. Layer Specifications

### Layer 1: Data Storage & ORM
- **Engine**: SQLite in WAL (Write-Ahead Logging) mode with foreign key enforcement.
- **ORM**: SQLAlchemy declarative models (`Client`, `AuditProject`, `Document`, `Finding`, `WorkingPaper`, `AuditLog`).

### Layer 2: Repositories & Services
- **Repositories**: Direct data access objects (`client_repo.py`, `document_repo.py`, `risk_repo.py`, `user_repo.py`).
- **Services**: Business logic controllers (`auth_service.py`, `client_service.py`, `document_service.py`, `risk_service.py`).

### Layer 3: Document Intelligence & AI
- **OCR Engine**: Multi-engine pipeline (`ocr_engine.py`) with digital PDF extraction and layout parsing.
- **Vector Store**: Local FAISS vector indexing with HuggingFace transformer embeddings (`embedding_service.py`).
- **LLM Integration**: Local Ollama REST client (`ollama_client.py`) connecting to local daemon on port `11434`.

### Layer 4: Presentation & Analytics
- **UI Framework**: PySide6 (Qt for Python) desktop widgets.
- **Analytics Engine**: Real-time SQL aggregations for KPIs, trends, and risk heatmaps.
