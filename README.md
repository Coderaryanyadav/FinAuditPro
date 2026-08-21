# FinAuditPro

FinAuditPro is a privacy-first, offline-first audit intelligence desktop operating system designed for Indian statutory audit practice. It provides audit firms with end-to-end engagement management, financial dataset import and deterministic analytics, document processing with OCR and SQLite FTS5 search, SA 320 materiality calculation engines, risk registers, working paper lifecycle control, local air-gapped AI assistance via LM Studio, and auditor-reviewed PDF/XLSX report exports.

---

## Key Capabilities

- **Offline-First & Air-Gapped Privacy**: Runs 100% locally on the auditor's workstation. Financial datasets, documents, SQLite databases, and local vector indices remain on-device.
- **Deterministic Analytics Engine**: Benford's 1st Law analysis, duplicate payment detection, high-value outlier detection, and round-number journal entry detection executed with mathematical precision (no LLM guesswork).
- **Audit Execution Core**: SA 320 materiality calculation engine, risk assessment matrix, structured audit procedure templates, and unified findings model with maker-checker review workflows.
- **Document Subsystem & FTS5**: Multi-format document ingestion (PDF, PNG, JPEG), PyMuPDF + Tesseract OCR extraction, full-text FTS5 search, and cryptographic document hashing.
- **Local AI Assistance (LM Studio)**: Air-gapped RAG pipeline against locally running models (`deepseek-r1-distill-qwen-14b`, `nomic-embed-text`) with citation links and strict auditor override disclaimers.
- **Working Papers & Sign-Off Control**: Maker-checker review workflow with automated blocking of sign-offs when unresolved review notes exist.
- **Engagement Archival & Roll-Forward**: SHA-256 sealed read-only archive creation, configurable retention rules (SA 230), and multi-year engagement roll-forwards with SA 510 opening balance tie-outs in paise.

---

## System Architecture

FinAuditPro enforces a clean 4-layer architecture with strict boundary protection enforced by automated AST enforcer unit tests:

```
                  ┌────────────────────────┐
                  │    PRESENTATION LAYER  │ (PySide6 Desktop UI)
                  └───────────┬────────────┘
                              │
                  ┌───────────▼────────────┐
                  │    APPLICATION LAYER   │ (Use Cases, DTOs, Services)
                  └───────────┬────────────┘
                              │
                  ┌───────────▼────────────┐
                  │      DOMAIN LAYER      │ (Pure Entities, Rules, Value Objects)
                  └───────────▲────────────┘
                              │
                  ┌───────────┴────────────┐
                  │  INFRASTRUCTURE LAYER  │ (SQLite ORM, Migrations, OCR, RAG)
                  └────────────────────────┘
```

---

## Quick Start & Installation

### Prerequisites
- Python 3.12 or higher (verified on Python 3.14.7)
- macOS (Apple Silicon arm64 / Intel) or Linux
- Tesseract OCR (`brew install tesseract` optional for OCR)

### Setup & Run
```bash
# Clone repository
git clone https://github.com/your-org/finauditpro.git
cd finauditpro

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode with OCR & AI optional dependencies
pip install -e .[ocr,ai]

# Run automated test suite
pytest -v tests

# Launch desktop application
finauditpro
```

---

## Technology Stack

- **Core Runtime**: Python 3.12+
- **Desktop UI**: PySide6 (Qt 6.8)
- **Database & Search**: SQLite 3 (WAL Mode, FTS5), SQLAlchemy 2.0 ORM
- **Document Processing**: PyMuPDF (fitz), Pillow, Tesseract OCR
- **Local AI & RAG**: httpx (LM Studio HTTP REST API), FAISS vector store
- **Export & Reporting**: ReportLab, OpenPyXL
- **Testing & Tooling**: Pytest, Ruff, MyPy, Hatchling

---

## Security & Privacy Posture

- **Fail-Closed RBAC**: Fine-grained role permissions (Partner, Manager, Senior, Staff) enforced at service layer.
- **Read-Only Archive Protection**: Sealed archives lock SQLite connections in `query_only=ON` mode with SHA-256 manifest verification.
- **Formula-Injection Escaping**: XLSX/CSV export pipeline sanitizes leading `=`, `+`, `-`, `@` triggers.
- **Zero Real Client Data**: Repository contains strictly synthetic test fixtures.

---

## Documentation Index

- [Architecture Guide](docs/architecture.md)
- [Development & Setup Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [AI Subsystem Guide](docs/ai.md)
- [Database Schema & Migrations](docs/database.md)
- [Testing Strategy](docs/testing.md)
- [Packaging & Distribution Guide](PACKAGING.md)
- [Architecture Review Report](ARCHITECTURE_REVIEW.md)

---

## License

FinAuditPro is licensed under the MIT License. See [LICENSE](LICENSE) for details.
