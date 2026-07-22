<div align="center">
  # 🚀 FinAuditPro

  **The Next-Generation AI-Powered Executive Intelligence Platform for Audit Professionals.**

  [![Python Version](https://img.shields.io/badge/python-3.11%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
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

- 🔒 **100% Air-Gapped & Offline First**: Zero cloud calls; all AI embeddings (SentenceTransformers) and LLM inference (Ollama) run entirely on local host hardware.
- ⚡ **Pure Database-Outward Architecture**: Dynamic SQL aggregations across SQLite without synthetic mocks or static hardcoded metrics.
- 📄 **Multi-Engine Document Intelligence**: Digital text extraction via `PyPDF` with automatic OCR fallback (`PaddleOCR` / `Tesseract`) and password-protected PDF safety guards.
- 🧠 **Retrieval-Augmented Generation (RAG)**: Offline FAISS vector search (`IndexFlatIP`) indexing table-aware chunks for local LLM audit assistance.
- 🛡️ **Enterprise Security & Cryptography**: PBKDF2-HMAC-SHA256 password hashing (100k iterations), AES-256 encrypted database backup archives, and an immutable SHA-256 hash-chain audit ledger.
- 📋 **Deterministic Rule Engine**: Dynamic verification against statutory GSTIN, PAN, Section 40A(3) cash limits, and Benford's Law distribution.
- 📊 **Executive Deliverables**: Automated generation of ReportLab PDF audit packages complete with digital signatures and QR verification hashes.

---

## 🏛️ System Architecture Diagrams

### 1. High-Level Subsystem Architecture

```mermaid
graph TD
    subgraph Presentation Tier ["Presentation Tier (PySide6 / Qt6)"]
        UI[Desktop GUI Views / Widgets]
        ST[Styles & Theme Tokens]
    end

    subgraph Service Tier ["Application Service Layer (Business Logic)"]
        AUTH_S[Auth & RBAC Service]
        CLIENT_S[Client & Engagement Service]
        DOC_S[Document Processing Service]
        AUDIT_S[Audit Engine Service]
        REPORT_S[Report Export Service]
    end

    subgraph Intelligence Tier ["Domain & Engine Layer"]
        RULE_E[Rule Engine & Severity Evaluator]
        WORKFLOW_E[Audit Workflow & State Machine]
        AI_E[RAG Engine & FAISS Vector Indexer]
        ANALYTICS_E[Financial Forecasting Engine]
    end

    subgraph Security & Data Tier ["Persistence & Security Layer"]
        REPO[Repository Layer]
        SEC[AES-256 Crypto & Hash-Chain Logger]
        ORM[SQLAlchemy 2.0 ORM]
        DB[(SQLite WAL Database)]
        VEC[(FAISS Local Vector Store)]
    end

    UI --> AUTH_S
    UI --> CLIENT_S
    UI --> DOC_S
    UI --> AUDIT_S
    UI --> REPORT_S

    AUTH_S --> SEC
    CLIENT_S --> REPO
    DOC_S --> AI_E
    AUDIT_S --> RULE_E
    AUDIT_S --> WORKFLOW_E
    REPORT_S --> ANALYTICS_E

    RULE_E --> REPO
    WORKFLOW_E --> REPO
    AI_E --> VEC
    REPO --> ORM
    ORM --> DB
    SEC --> DB
```

### 2. Local RAG & Document Intelligence Pipeline

```mermaid
flowchart LR
    subgraph Ingestion ["1. Document Ingestion"]
        PDF[PDF / Image Invoice] --> OCR[PDFPlumber / Tesseract OCR]
        OCR --> CLEAN[Text Cleaner & Sanitizer]
        CLEAN --> CHUNK[512-Token Sliding Window Chunker]
    end

    subgraph Vectorization ["2. Embeddings & Vector Index"]
        CHUNK --> EMBED[SentenceTransformer Vectorizer]
        EMBED --> FAISS[(FAISS Dense Vector Store)]
    end

    subgraph RAG Reasoning ["3. Local AI Reasoning"]
        QUERY[Auditor Query / Rule Trigger] --> Q_VEC[Generate Vector]
        Q_VEC --> FAISS
        FAISS -->|Top-K Context Chunks| PROMPT[Prompt Engine Builder]
        PROMPT --> OLLAMA[Ollama Local LLM Daemon]
        OLLAMA --> FINDINGS[Structured JSON Audit Findings]
    end
```

### 3. Cryptographic Audit Log Hash Chain

```mermaid
graph LR
    subgraph Ledger ["Immutable Security Ledger"]
        E1["Audit Entry #1<br/>Hash: 00000...a1f"] --> E2["Audit Entry #2<br/>Hash: SHA256(E1 + Action)"]
        E2 --> E3["Audit Entry #3<br/>Hash: SHA256(E2 + Action)"]
        E3 --> E4["Audit Entry #4<br/>Hash: SHA256(E3 + Action)"]
    end
```

---

## 📚 Documentation Index (`docs/` Directory)

Comprehensive technical documentation is available in the [`docs/`](docs/) directory:

- 🏛️ [**ARCHITECTURE_OVERVIEW.md**](docs/architecture/ARCHITECTURE_OVERVIEW.md): Master System Layered Topology & Pipeline Design.
- 🗄️ [**DATABASE_ARCHITECTURE.md**](docs/architecture/DATABASE_ARCHITECTURE.md): SQLite WAL Engine, Session Management & PostgreSQL Roadmap.
- 📊 [**ER_DIAGRAM.md**](docs/architecture/ER_DIAGRAM.md): Complete 18-Entity Schema Specification & Relationships.
- 🔒 [**SECURITY_ARCHITECTURE.md**](docs/architecture/SECURITY_ARCHITECTURE.md): Cryptography, PBKDF2, AES-256-GCM & SHA-256 Hash Chains.
- 🤖 [**AI_ARCHITECTURE.md**](docs/architecture/AI_ARCHITECTURE.md): Local RAG Subsystem, FAISS Vector Indexing & Ollama LLM.
- 📈 [**REPORT_ARCHITECTURE.md**](docs/architecture/REPORT_ARCHITECTURE.md): ReportLab PDF, Excel Exporter, Digital Signatures & QR Codes.
- 🛠️ [**DEVELOPER_GUIDE.md**](docs/developer/DEVELOPER_GUIDE.md): Developer Onboarding & Code Guidelines.
- 📖 [**USER_MANUAL.md**](docs/user/USER_MANUAL.md): Step-by-Step Desktop UI Operational Manual.
- 💾 [**INSTALLATION.md**](docs/developer/INSTALLATION.md): Multi-Platform Installation & Setup.
- 🧪 [**TEST_ARCHITECTURE.md**](docs/developer/TEST_ARCHITECTURE.md): Test Execution, Pyramid & Coverage Standards.

---

## 🛠️ Technology Stack

- **Core Runtime**: Python 3.11+
- **GUI Framework**: PySide6 (Qt for Python 6.8)
- **Database & ORM**: SQLite (WAL Mode), SQLAlchemy 2.0
- **Vector Search & Embeddings**: FAISS (`faiss-cpu`), SentenceTransformers
- **Local AI Inference**: Ollama REST API (`llama3`, `deepseek-r1`)
- **Document Processing**: PDFPlumber, PyPDF, Tesseract OCR, Pillow
- **Export Engines**: ReportLab (PDF), OpenPyXL (Excel)
- **Cryptography**: PyCryptodome (AES-256-GCM), hashlib (PBKDF2, SHA-256)
- **Packaging**: PyInstaller, Inno Setup / NSIS (Windows), DMG (macOS), AppImage (Linux)

---

## 💻 One-Click Auto-Installer & Quickstart

FinAuditPro includes a **universal auto-installer bootstrapper** that automatically detects your OS, checks runtime prerequisites, creates virtual environments, installs Python dependencies, and launches the app.

### ⚡ One-Click Run (Zero Configuration Required)

- **Windows**: Double-click `install.bat` or run in terminal:
  ```cmd
  install.bat
  ```

- **macOS & Linux**: Run in terminal:
  ```bash
  chmod +x install.sh
  ./install.sh
  ```

- **Manual Bootstrapper Execution**:
  ```bash
  python scripts/bootstrap_env.py
  ```

---

### Step-by-Step Manual Setup

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
   ollama pull llama3
   ```

5. **Launch Application**:
   ```bash
   python src/main.py
   ```

---

## 🧪 Testing

Run the automated Pytest regression suite:

```bash
python -m pytest -o addopts="" tests/
```

---

## 📄 License & Credits

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.  
Developed by **Aryan Yadav**, **Jeet Shah**, and **Hitansh Jasani** ([Coderaryanyadav](https://github.com/Coderaryanyadav)).

