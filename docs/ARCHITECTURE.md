# FinAuditPro System Architecture (v1.0.0)

## 1. Architectural Philosophy
FinAuditPro is an **Offline-First Desktop Statutory & Internal Audit Workstation** engineered for Indian Chartered Accountants (CAs). The system is built around the following core architectural invariants:

1. **Zero Outbound Client Data Transmission**: All database operations, OCR, deterministic analytics, full-text searches, and local vector retrieval execute strictly on the local machine.
2. **Deterministic Integer Math**: All monetary amounts are stored and calculated as exact 64-bit integer paise ($1\text{ INR} = 100\text{ paise}$) to avoid IEEE 754 floating-point rounding errors.
3. **Append-Only Cryptographic Audit Trail**: Every state mutation produces an immutable `audit_events` record with previous-hash SHA-256 chaining.
4. **Clean 4-Layer Domain-Driven Architecture (DDD)**:
   - **Domain Layer (`src/finauditpro/domain/`)**: Pure business logic, accounting invariants, value objects, and repository interfaces. Zero external framework dependencies.
   - **Application Layer (`src/finauditpro/application/`)**: Use-case coordinators, DTOs, security services, and transaction boundaries.
   - **Infrastructure Layer (`src/finauditpro/infrastructure/`)**: SQLite persistence (WAL mode), migrations 1..9, FAISS vector indexing, PyMuPDF/Tesseract OCR, and ReportLab PDF exporters.
   - **Presentation Layer (`src/finauditpro/ui/`)**: PySide6 (Qt 6.8+) desktop user interface, neutral dark theme, custom widgets, and background task workers.

---

## 2. Component Diagram
```
+-------------------------------------------------------------------------+
|                          Presentation Layer                             |
|       (PySide6 / Qt 6.8+ Desktop UI, Neutral Dark Theme, Dialogs)       |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                          Application Layer                              |
|   (AuthService, FinancialDataService, AuditMatrixService, DocumentSvc)  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                            Domain Layer                                 |
|  (Entities: Firm, Client, Engagement, WorkingPaper, Misstatement, Lead) |
|  (Value Objects: Money/Paise, AuditPeriod, Assertion, RiskLevel)        |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                        Infrastructure Layer                             |
|  (SQLite WAL ORM, Fernet/PBKDF2 Crypto, FTS5 Indexer, FAISS Vector DB)  |
+-------------------------------------------------------------------------+
```

---

## 3. Data Isolation and Tenancy
- **3-Tier Hierarchy**: `Firm` $\rightarrow$ `Client` $\rightarrow$ `Engagement`.
- **Query Scoping**: All relational repositories enforce mandatory `engagement_id` filtering.
- **Archive Sealing**: Sealed engagements enforce `PRAGMA query_only = ON` with SHA-256 seal verification.
