<div align="center">
  # 🚀 FinAuditPro

  **The Next-Generation AI-Powered Executive Intelligence Platform for Audit Professionals.**

  [![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=for-the-badge&logo=githubactions)](https://github.com/Coderaryanyadav/FinAuditPro)

  ![Platform Support](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg?style=for-the-badge)
</div>

---

## 📖 Executive Overview

FinAuditPro is an enterprise-grade, offline-first desktop application designed for Chartered Accountants (CAs) and Fortune 500 financial audit teams. By combining local AI models (Ollama), Document Intelligence (OCR + Vector Search), and a strict Rule Engine, FinAuditPro automates financial verification while guaranteeing 100% data privacy.

### Key Architectural Standards
- 🔒 **Zero Synthetic / Mock Logic**: Every KPI, risk card, report table, and dashboard graph is computed dynamically via live SQL queries against SQLite.
- ⚡ **Pure Database-Outward Architecture**:
  $$\text{SQLite} \rightarrow \text{SQLAlchemy} \rightarrow \text{Repositories} \rightarrow \text{Services} \rightarrow \text{Business Logic} \rightarrow \text{Workflow} \rightarrow \text{Rule Engine} \rightarrow \text{OCR} \rightarrow \text{Embeddings} \rightarrow \text{FAISS} \rightarrow \text{LLM} \rightarrow \text{Report Engine} \rightarrow \text{Analytics} \rightarrow \text{PySide6 UI}$$
- 🛡️ **Enterprise Cryptography & Security**: PBKDF2-HMAC-SHA256 password hashing, AES-256 backup encryption, and immutable audit logs.

---

## 📚 Documentation Index (`docs/` Folder)

Detailed documentation is organized in the [`docs/`](docs/) directory:

- 🏛️ [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md): Database-Outward Pipeline & Engineering Design.
- 🛡️ [**docs/SECURITY.md**](docs/SECURITY.md): PBKDF2 Hashing, AES-256 Encryption, Audit Trail, and RBAC.
- 🤝 [**docs/CONTRIBUTING.md**](docs/CONTRIBUTING.md): Developer Setup, Code Standards, and Testing.
- 📝 [**docs/CHANGELOG.md**](docs/CHANGELOG.md): Version History and Architectural Refactoring Log.
- 🔌 [**docs/API.md**](docs/API.md): Service APIs, Database Repositories, and LLM Client Reference.

---

## 🏗️ Project Structure

```text
FinAuditPro/
├── docs/                       # Project documentation directory
│   ├── ARCHITECTURE.md         # Pure Database-Outward Architecture guide
│   ├── SECURITY.md             # Security policy & cryptography spec
│   ├── CONTRIBUTING.md         # Contribution standards & pytest workflow
│   ├── CHANGELOG.md            # Release history
│   └── API.md                  # Service & repository API reference
├── src/
│   ├── main.py                 # App entry point & initialization
│   ├── database/               # SQLAlchemy ORM models & database repositories
│   ├── services/               # Core business services & authentication
│   ├── workflow/               # Engagement workflow state engine
│   ├── rule_engine/            # Deterministic financial rule executor
│   ├── document_intelligence/  # Multi-engine OCR, Document Parser & HuggingFace Embeddings
│   ├── ai/                     # Local Ollama REST client & FAISS Vector Store
│   ├── reporting/              # ReportLab PDF & Excel pack exporters
│   ├── analytics/              # Dynamic SQL KPI, Trend, and Heatmap engines
│   ├── security/               # Cryptography, Auth, Audit Trail & RBAC
│   ├── deployment/             # DDL Migrations, Diagnostics, Logger
│   └── ui/                     # PySide6 desktop interface screens
├── tests/                      # Pytest integration test suite
├── pyproject.toml              # Build & dependency metadata
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd Audit

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database schema migrations
.venv/bin/python -c "from deployment.migration import DatabaseMigrator; DatabaseMigrator.migrate()"

# Launch application
.venv/bin/python src/main.py
```

---

## 📄 License & Author

- **License**: MIT License
- **Author**: Aryan Yadav ([Coderaryanyadav](https://github.com/Coderaryanyadav))