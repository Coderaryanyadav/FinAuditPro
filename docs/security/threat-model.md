# FinAuditPro Threat Model & Defense-in-Depth

This document details identified threat vectors and the technical countermeasures enforced by FinAuditPro.

---

## 1. Threat Vectors & Mitigations

| Threat Vector | Description | Technical Countermeasure |
| :--- | :--- | :--- |
| **Path Traversal / ZIP Slip** | Malicious document filename or backup entry attempting directory escape. | Strict sanitization via `document_security.py` and canonical path validation before write. |
| **Formula Injection** | Malicious cell values in CSV/XLSX exports executing shell commands. | Single-quote escaping (`'=...`) in `export_sanitizer.py` across all tabular export pipelines. |
| **Cross-Engagement Leakage** | Auditor querying documents or financial lines belonging to another client. | Strict `engagement_id` filtering enforced at repository and SQL level. |
| **RAG Prompt Injection** | Embedded prompt manipulation payloads inside audited PDFs. | Delimiter sanitization, `<think>` token removal, and structured JSON output validation. |
| **Archive Tampering** | Post-archival modification of SQLite database files. | SHA-256 manifest hashing and SQLite connection lock via `PRAGMA query_only = ON`. |
| **Maker-Checker Bypass** | Single user authoring, reviewing, and signing off on their own working paper. | Segregation-of-duties validation and open review notes blocking in `WorkingPaperService`. |
