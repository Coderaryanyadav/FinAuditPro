<div align="center">
  # 🚀 FinAuditPro

  **The Next-Generation AI-Powered Executive Intelligence Platform for Audit Professionals.**

  [![Python Version](https://img.shields.io/badge/python-3.12%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![PySide6](https://img.shields.io/badge/PySide-6.8-41CD52.svg?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
  [![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
  [![Ollama](https://img.shields.io/badge/Ollama-Offline%20LLM-000000.svg?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=for-the-badge&logo=githubactions)](https://github.com/Coderaryanyadav/FinAuditPro)
  [![Platform Support](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg?style=for-the-badge)](https://github.com/Coderaryanyadav/FinAuditPro)
</div>

---

## 📖 Executive Overview

**FinAuditPro** is an offline-first desktop application engineered for Chartered Accountants (CAs), statutory auditors, and enterprise compliance teams. Combining local LLM execution (Ollama), multi-engine OCR, offline vector similarity search (FAISS), deterministic statutory rule checking, and zero-synthetic SQL analytics, FinAuditPro provides complete audit automation without ever transmitting sensitive client financial data to external cloud networks.

---

## ✨ Key Features

- 🔒 **100% Air-Gapped & Offline First**: Zero cloud calls; all AI embeddings (HuggingFace) and LLM inference (Ollama) run entirely on local host hardware.
- ⚡ **Pure Database-Outward Architecture**: Dynamic SQL aggregations across SQLite without synthetic mocks or static hardcoded metrics.
- 📄 **Multi-Engine Document Intelligence**: Digital text extraction via `PyPDF` with automatic OCR fallback (`PaddleOCR` / `Tesseract`) and password-protected PDF safety guards.
- 🧠 **Retrieval-Augmented Generation (RAG)**: Offline FAISS vector search (`IndexFlatL2`) indexing table-aware chunks for local LLM audit assistance.
- 🛡️ **Enterprise Security & Cryptography**: PBKDF2-HMAC-SHA256 password hashing (100k iterations), AES-256 encrypted database backup archives, and an immutable SHA-256 hash-chain audit ledger.
- 📋 **Deterministic Rule Engine**: Dynamic verification against statutory GSTIN, PAN, Section 40A(3) cash limits, and Benford's Law distribution.
- 📊 **Executive Deliverables**: Automated generation of ReportLab PDF audit packages complete with digital signatures and QR verification hashes.

---

## 🏛️ System Architecture

FinAuditPro enforces a strict database-outward layered pipeline:

```text
SQLite Data Store
   └── SQLAlchemy ORM (Models & Connection Pooling)
        └── Repositories (ClientRepo, EngagementRepo)
             └── Service Layer (ClientService, EngagementService)
                  └── Workflow Engine & Event Bus
                       ├── Deterministic Rule Engine
                       ├── Document Ingestion & Multi-Engine OCR
                       ├── Offline Embedding & FAISS Vector Indexing
                       ├── Local Ollama LLM Interface
                       └── PySide6 Desktop User Interface
```

---

## 📚 Documentation Index (`docs/` Directory)

Comprehensive technical documentation is available in the [`docs/`](docs/) directory:

- 🏛️ [**ARCHITECTURE.md**](docs/ARCHITECTURE.md): Database-Outward Pipeline & Engineering Design.
- 🛡️ [**SECURITY.md**](docs/SECURITY.md): Cryptography, Authentication, Audit Trail & RBAC Matrix.
- 🔌 [**API.md**](docs/API.md): Services, Repositories, Cryptography & Engine References.
- 🛠️ [**DEVELOPER_GUIDE.md**](docs/DEVELOPER_GUIDE.md): Developer Onboarding, Extension & Custom Rule Guide.
- 📖 [**USER_MANUAL.md**](docs/USER_MANUAL.md): Step-by-Step Desktop UI Operational Manual.
- 💾 [**INSTALLATION.md**](docs/INSTALLATION.md): Multi-Platform Installation & Installer Compilation.
- 🧪 [**TESTING.md**](docs/TESTING.md): Test Execution, Matrix & Coverage Standards.
- 📝 [**CHANGELOG.md**](docs/CHANGELOG.md): Semantic Version History.
- 🤝 [**CONTRIBUTING.md**](docs/CONTRIBUTING.md): Code Standards & Development Process.

---

## 🛠️ Technology Stack

- **Core Runtime**: Python 3.12
- **GUI Framework**: PySide6 (Qt for Python 6.8)
- **Database & ORM**: SQLite (WAL Mode), SQLAlchemy 2.0
- **Vector Search & Embeddings**: FAISS (`faiss-cpu`), HuggingFace Transformers
- **Local AI Inference**: Ollama REST API (`llama3.2`)
- **Document Processing**: PyPDF, pdfplumber, PaddleOCR, Pillow
- **Export Engines**: ReportLab (PDF), OpenPyXL (Excel)
- **Cryptography**: `cryptography` (Fernet AES-256), `hashlib` (PBKDF2, SHA-256)
- **Packaging**: PyInstaller, Inno Setup (Windows), DMG Canvas (macOS), AppImage (Linux)

---

## 💻 Installation & Quickstart

### System Requirements
- **OS**: Windows 10/11 (64-bit), macOS 12+, or Ubuntu 22.04 LTS
- **RAM**: 8 GB minimum (16 GB recommended for local LLM inference)
- **Disk Space**: 5 GB free space
- **Prerequisites**: Python 3.10 to 3.12, [Ollama](https://ollama.ai/) installed locally

### Step-by-Step Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/Coderaryanyadav/FinAuditPro.git
   cd FinAuditPro
   ```

2. **Establish Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize Local Ollama Model**:
   ```bash
   ollama pull llama3.2
   ```

5. **Launch Application**:
   ```bash
   python src/main.py
   ```

---

## 🧪 Testing

Run the full automated Pytest regression suite (45 unit and integration tests):

```bash
python -m pytest -o addopts="" tests/
```

---

## 📄 License & Credits

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.  
Developed by **Aryan Yadav**, **Jeet Shah**, and **Hitansh Jasani** ([Coderaryanyadav](https://github.com/Coderaryanyadav)).
