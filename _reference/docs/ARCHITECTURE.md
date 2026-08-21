# FinAuditPro — System Architecture & Technical Specifications

> **System Version**: 1.0.0\
> **Target Audience**: Enterprise Architects, Security Auditors, Principal
> Engineers, Open-Source Maintainers\
> **Security Classification**: Internal / Public Technical Specifications

---

## 1. Executive Overview

**FinAuditPro** is an offline-first, air-gapped desktop application built for
statutory auditors, Chartered Accountants (CAs), and audit firms in India. It
automates financial document ingestion, statutory compliance rule evaluation
(ICAI Standards on Auditing SA 200–790, CARO 2020, Income Tax Act, Companies Act
2013), offline AI retrieval-augmented generation (RAG), working paper
generation, and tamper-evident audit report compilation.

### Key Architectural Characteristics

- **Zero External Telemetry**: Runs completely offline without external server
  dependencies or cloud data leakage.
- **Air-Gapped AI Pipeline**: Uses local LLM inference (Ollama with `llama3.2` /
  `deepseek-r1`) and local vector embeddings (FAISS + HuggingFace Transformers).
- **Strict Clean Architecture**: Enforces a database-outward pattern where UI
  components never interact directly with database models.
- **Cryptographic Audit Ledger**: Implements SHA-256 hash-chained immutable
  audit logging and digital signature verification for generated PDF/Excel audit
  packs.

---

## 2. System Philosophy & Core Design Principles

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION TIER (PySide6)                        │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ Event Signals & Data DTOs
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                         SERVICE TIER (Business Logic)                        │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ Repository Interfaces & Entities
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                        REPOSITORY TIER (SQLAlchemy ORM)                      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ SQL Queries (WAL Mode)
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                         DATA TIER (SQLite Database)                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

1. **Database-Outward Flow**: All financial state, compliance findings, document
   indexes, and audit trails originate from SQLite as the single source of
   truth.
2. **Deterministic-First Compliance**: Hard numerical rules (GSTIN checksums,
   PAN patterns, Section 40A(3) cash thresholds, Benford's Law distribution
   analysis) execute deterministically before probabilistic AI inferences.
3. **Decoupled Asynchronous Workers**: Heavy CPU/GPU workloads (OCR extraction,
   vector embedding, local LLM generation) execute on non-blocking background
   QThread workers.
4. **Defense-in-Depth Security**: PBKDF2-HMAC-SHA256 password hashing (100,000
   iterations), AES-256 Fernet data encryption at rest, role-based access
   control (RBAC), and session tampering prevention.

---

## 3. High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Client UI ["Desktop Application Tier (PySide6 / Qt6)"]
        DashboardUI["Dashboard View"]
        ClientUI["Client Management View"]
        DocUI["Document Intake View"]
        RuleUI["Rule Engine View"]
        AIChatUI["RAG AI Copilot View"]
        ReportUI["Reports View"]
    end

    subgraph ServiceLayer ["Service Layer (Business Logic & Security)"]
        AuthSvc["AuthService & SecurityManager"]
        ClientSvc["ClientService"]
        DocSvc["DocumentService"]
        FindingSvc["FindingService"]
        WPSvc["WorkingPaperService"]
        ReportSvc["ReportService"]
    end

    subgraph CoreEngine ["Processing & Intelligence Engines"]
        RuleEngine["AuditRuleEngine (7 Statutory Rules)"]
        OCREngine["Multi-Engine OCR (PyPDF / Paddle / Tesseract)"]
        EmbeddingSvc["SentenceTransformer (bge-small-en-v1.5)"]
        VectorStore["FAISS Vector Index (IndexFlatIP)"]
        OllamaClient["Ollama REST Client (Local Daemon)"]
        ReportEngine["ReportEngine (PDF / OpenPyXL / QR / Hash)"]
    end

    subgraph RepoLayer ["Data Access & Storage Tier"]
        Repos["Repositories (ClientRepo, DocRepo, WorkingPaperRepo, etc.)"]
        DB[(SQLite WAL Engine)]
    end

    DashboardUI --> ClientSvc
    DocUI --> DocSvc
    RuleUI --> RuleEngine
    AIChatUI --> OllamaClient
    AIChatUI --> VectorStore
    ReportUI --> ReportSvc

    ClientSvc --> Repos
    DocSvc --> OCREngine
    DocSvc --> EmbeddingSvc
    EmbeddingSvc --> VectorStore
    RuleEngine --> FindingSvc
    FindingSvc --> Repos
    ReportSvc --> ReportEngine
    AuthSvc --> Repos
    Repos --> DB
```

---

## 4. Clean Architecture Layer Specifications

FinAuditPro enforces strict boundary separation across four main project layers:

| Layer                     | Package Directory                                                                              | Responsibilities & Component Scope                                                                                                     | Dependencies                         |
| :------------------------ | :--------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| **Presentation**          | `src/ui/`                                                                                      | Qt6 GUI widgets, user input handlers, visual charts, signal/slot wiring, progress bars, background worker management (`OllamaWorker`). | Service Layer, Data DTOs             |
| **Services & Workflow**   | `src/services/`, `src/workflow/`                                                               | Business orchestrators, authentication flow, session tracking, audit trail logging, workflow state machine.                            | Repositories, Rule Engine, Reporting |
| **Domain & Core Engines** | `src/rule_engine/`, `src/document_intelligence/`, `src/ai/`, `src/security/`, `src/reporting/` | Pure business entities, statutory rules, OCR extraction, FAISS vector indexing, AES encryption, PDF/Excel compilation.                 | Core Config, Models, External Libs   |
| **Data Access & Storage** | `src/database/`                                                                                | SQLAlchemy 2.0 ORM models (`models.py`), repository DAOs (`repositories/`), SQLite WAL database engine (`database.py`).                | SQLAlchemy, SQLite                   |

```mermaid
classDiagram
    class PySide6_UI {
        +update_view()
        +on_user_action()
    }
    class Service_Layer {
        +process_engagement()
        +generate_findings()
    }
    class Repository_Layer {
        +get_by_id()
        +add()
        +commit()
    }
    class SQLAlchemy_ORM {
        +SQLite_WAL_DB
    }

    PySide6_UI --> Service_Layer : Invokes DTO Operations
    Service_Layer --> Repository_Layer : Delegates Data Access
    Repository_Layer --> SQLAlchemy_ORM : Executes SQL Transactions
```

---

## 5. Folder Structure & Component Mapping

```text
src/
├── main.py                          # Desktop Application Entry Point (PySide6 QApplication)
├── core/
│   ├── config.py                    # AppConfig (Pydantic environment settings & path resolving)
│   └── exceptions.py                # Enterprise Domain Exceptions (ValidationError, AuthError, etc.)
├── database/
│   ├── database.py                  # SQLite WAL connection pooling & SessionLocal generator
│   ├── models.py                    # 22 SQLAlchemy ORM Declarative Entity Models
│   └── repositories/                # Data Access Objects (ClientRepo, DocRepo, FindingRepo, etc.)
├── services/                        # Business Logic Controllers (Auth, Client, Document, Report)
├── security/                        # RBAC, PBKDF2 Hashing, AES-256 Crypto, SHA-256 Audit Trail
├── rule_engine/                     # Statutory Compliance Rules (GSTIN, Sec 40A(3), Benford, CARO)
├── document_intelligence/           # Document Ingestion, PyPDF, Multi-Engine OCR & Table Extraction
├── ai/                              # Ollama Local REST Client, VectorStore (FAISS), Worker Threads
├── reporting/                       # PDF Generator (ReportLab), Excel Exporter, Digital Signature, QR
├── analytics/                       # SQL Analytics Engine, KPI Aggregator, Forecast Engine
├── workflow/                        # Audit Lifecycle State Machine & Event Bus
└── ui/                              # PySide6 Desktop User Interface Components & QSS Themes
```

---

## 6. Detailed Request & Interaction Lifecycles

### 6.1 User Authentication & Session Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Auditor
    participant UI as LoginWidget (PySide6)
    participant Auth as AuthService
    participant Sec as SecurityManager
    participant Repo as UserRepository
    participant DB as SQLite WAL Database

    User->>UI: Input Username & Password
    UI->>Auth: authenticate_user(username, password)
    Auth->>Repo: get_by_username(username)
    Repo->>DB: SELECT * FROM users WHERE username = ?
    DB-->>Repo: User Record (Hash + Salt)
    Repo-->>Auth: User Entity
    Auth->>Sec: verify_password(plain, salt, hash)
    Sec-->>Auth: True / False
    alt Success
        Auth->>Sec: create_session(user_id, role)
        Sec-->>Auth: ActiveSession Token
        Auth-->>UI: Authentication Result (Success, Session)
        UI-->>User: Navigate to Executive Dashboard
    else Failure
        Auth-->>UI: Authentication Result (Invalid Credentials)
        UI-->>User: Display Error Banner
    end
```

### 6.2 Document Ingestion & RAG AI Query Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Auditor
    participant UI as AIAuditWidget
    participant Pipeline as DocumentPipeline
    participant OCR as OCREngine
    participant Embed as EmbeddingService
    participant FAISS as VectorStore (FAISS)
    participant Ollama as OllamaClient (Local REST)

    User->>UI: Drop PDF Document / Type Prompt
    UI->>Pipeline: process_document(file_path)
    Pipeline->>OCR: extract_text_and_tables(file_path)
    OCR-->>Pipeline: Clean Text + Extracted Tables
    Pipeline->>Embed: chunk_and_embed(clean_text)
    Embed->>FAISS: add_vectors(embeddings, metadata)
    FAISS-->>Pipeline: Vector Index Updated

    User->>UI: "Check inventory discrepancies under CARO 2020 Clause (ii)"
    UI->>FAISS: search_similar(query_vector, k=3)
    FAISS-->>UI: Top 3 Relevant Context Chunks
    UI->>Ollama: generate_response(prompt + context_chunks)
    Ollama-->>UI: Stream Tokens (Real-Time Output)
    UI-->>User: Display AI Compliance Analysis & Citations
```

---

## 7. Security Boundaries & Trust Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNTRUSTED INPUT BOUNDARY                            │
│   - External PDF Files, Client Excel Sheets, Scanned Images, User Prompts  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Input Sanitization & Validation
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         APPLICATION TRUST ZONE                              │
│   - AES-256 Encrypted Datastore (finauditpro.db)                            │
│   - Local Vector Database (FAISS Index)                                     │
│   - PBKDF2 Password Hashing & RBAC Authorization Gates                       │
│   - SHA-256 Hash-Chained Audit Ledger                                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Local REST (127.0.0.1:11434 Only)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         LOCAL ISOLATED AI DAEMON                            │
│   - Ollama Service (Air-Gapped Local LLM Inference Engine)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Trust Zone 1 (Local Input Boundary)**: External client uploads (PDFs, Excel
  workbooks, images) are parsed inside isolated memory buffers using defensive
  PyPDF and PaddleOCR handlers.
- **Trust Zone 2 (Core Application Storage)**: Database records, working papers,
  and user credentials are protected via AES-256 CBC encryption and SHA-256
  integrity checksums.
- **Trust Zone 3 (Local Daemon Interface)**: Communications with Ollama occur
  exclusively over localhost (`127.0.0.1:11434`). No network ports are exposed
  externally.

---

## 8. Database Architecture & Transaction Management

FinAuditPro utilizes SQLite 3 running in **Write-Ahead Logging (WAL)** mode for
concurrent read/write performance.

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> TransactionStarted : get_session()
    TransactionStarted --> QueryExecuted : SELECT / INSERT / UPDATE
    QueryExecuted --> ValidationPassed : Business Rules Verified
    ValidationPassed --> Committed : session.commit()
    QueryExecuted --> RolledBack : Exception Caught
    ValidationPassed --> RolledBack : Validation Exception
    Committed --> Idle : session.close()
    RolledBack --> Idle : session.close()
```

### PRAGMA Configuration

- `PRAGMA journal_mode=WAL;` — Enables concurrent reads while writing.
- `PRAGMA synchronous=NORMAL;` — Balances IO performance with safety against
  system crashes.
- `PRAGMA foreign_keys=ON;` — Strict referential integrity enforcement.
- `PRAGMA busy_timeout=5000;` — Handles transient database locks gracefully.

---

## 9. Design Patterns Used Across Codebase

| Design Pattern                 | Implementation Class / Module            | Purpose                                                                                         |
| :----------------------------- | :--------------------------------------- | :---------------------------------------------------------------------------------------------- |
| **Facade**                     | `ReportEngine`, `AuditRuleEngine`        | Provides unified interfaces over complex multi-step subsystems (PDF + Excel + Signatures).      |
| **Repository**                 | `ClientRepository`, `DocumentRepository` | Decouples ORM database queries from domain business logic.                                      |
| **Factory**                    | `ReportTemplateFactory`                  | Dynamically instantiates audit opinion templates based on finding severity.                     |
| **Singleton**                  | `AppConfig`, `SecurityManager`           | Ensures global configuration state and security session state remain unique.                    |
| **Strategy**                   | `OCREngine`                              | Automatically selects PyPDF, PaddleOCR, or Tesseract based on document layout and availability. |
| **Observer / Event Bus**       | `WorkflowManager`, `WorkflowEvents`      | Dispatches lifecycle events (e.g. `DOCUMENT_UPLOADED`, `FINDING_INGESTED`) across UI widgets.   |
| **Producer-Consumer / Worker** | `OllamaWorker`                           | Offloads blocking LLM HTTP streaming to PySide6 `QThread` workers.                              |

---

## 10. Future Architecture Roadmap

```mermaid
gantt
    title FinAuditPro Architecture Evolution Roadmap
    dateFormat  YYYY-MM
    section Core Infrastructure
    Async SQLAlchemy 2.0 Upgrade      :active, 2026-08, 2026-10
    SQLCipher Full Database Encryption: 2026-10, 2026-12
    section AI & Intelligence
    Local Quantized ONNX OCR Pipeline  : 2026-09, 2026-11
    Multi-Vector Collection Indexing  : 2026-11, 2027-01
    section Multi-User & Enterprise
    LAN Peer-to-Peer Audit Sync Engine: 2027-01, 2027-04
```

---

_FinAuditPro Technical Architecture Reference — FinAuditPro Open Source Team._
