# FinAuditPro — Master Product & Engineering Roadmap

## 1. Development Timeline & Milestones
- [x] **Phase A:** Financial & Trial Balance Foundation (Integer-paise math, Schedule III).
- [x] **Phase B:** Core Audit Engine & Sampling (MUS, SA 530, risk models).
- [x] **Phase C:** Statutory Compliance (CARO 2020 21 clauses, Form 3CD 44 clauses).
- [x] **Phase D:** Review & Completion (Maker-checker sign-offs, review notes).
- [x] **Phase E:** Audit Reporting (ReportLab PDF pipeline, UDIN watermarking).
- [x] **Phase F:** Continuous Audit & AI Copilot (LM Studio local RAG, prompt defense).
- [x] **v1.2.0 GA Release:** 130+ passing tests, 1,000-run verification.

## 2. Architecture Decision Records (ADRs)

| ADR ID | Decision Title | Status | Rationale |
| :--- | :--- | :---: | :--- |
| **ADR-001** | SQLite WAL Mode Persistence | Approved | Embedded zero-daemon ACID storage with non-blocking reads. |
| **ADR-002** | Integer Paise Math (No Floats) | Approved | Eliminates floating-point precision loss in financial totals. |
| **ADR-003** | 4-Layer Domain-Driven Design | Approved | Pure Python domain core decoupled from UI and database. |
| **ADR-004** | Local LM Studio AI Integration | Approved | Zero cloud egress guaranteeing complete client confidentiality. |
| **ADR-005** | Trigger-Based Immutability | Approved | Database-level immutable audit trails for approved workpapers. |
| **ADR-006** | AES-128-CBC Database Encryption | Approved | Encryption at rest with PBKDF2 key derivation. |
| **ADR-007** | Monetary-Unit Sampling (MUS) | Approved | Industry standard statutory audit sampling under SA 530. |
| **ADR-008** | Formula Injection Escaping | Approved | Sanitizes dangerous CSV formula prefixes on export. |
| **ADR-009** | ReportLab PDF Assembly | Approved | Deterministic, reproducible statutory PDF report generation. |
| **ADR-010** | SQC 1 10-Year Archival Package | Approved | Encrypted `.fapz` bundle with SHA-256 tamper-evident manifest. |
