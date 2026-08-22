# FinAuditPro — Security Architecture & Threat Defense Guide

FinAuditPro enforces a defense-in-depth security model tailored specifically for air-gapped statutory financial audit practice.

---

## 1. Fail-Closed Role-Based Access Control (RBAC)

Access control is enforced at the application service layer via `src/finauditpro/application/security/rbac.py`:

| Role | Firm / Client Admin | Engagement Config | Upload Documents | Sign-Off Working Papers | Archive / Reopen |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Partner** | Yes | Yes | Yes | Yes | Yes |
| **Manager** | No | Yes | Yes | No (Review Only) | No |
| **Senior Auditor** | No | No | Yes | No (Draft/Edit Only) | No |
| **Associate** | No | No | Yes | No (View Only) | No |

---

## 2. Multi-Tenant Engagement Isolation

All database tables partition sensitive records by `engagement_id`. Repositories mandate `engagement_id` parameters in every retrieval and modification query to prevent cross-engagement data leakage.

---

## 3. Cryptography & Column-Level Encryption

- Sensitive tokens and metadata at rest are protected via `cryptography.fernet.Fernet` with machine-local PBKDF2 salt derivation (`src/finauditpro/infrastructure/security/encryption.py`).
- Exported backup bundles are encrypted using PBKDF2 key derivation with 100,000 iterations and unique 16-byte salts.

---

## 4. Immutable Audit Trail

All critical security events (login, user creation, document upload, sign-off, archival, roll-forward) are logged to the `audit_events` ledger table with sequential SHA-256 block hashing for tamper evidence.

---

## 5. Threat Vectors & Adversarial Mitigations

| Threat Vector | Description | Technical Countermeasure |
| :--- | :--- | :--- |
| **Path Traversal / ZIP Slip** | Malicious document filename or backup entry attempting directory escape. | Strict sanitization via `document_security.py` and canonical path validation before write. |
| **Formula Injection** | Malicious cell values in CSV/XLSX exports executing shell commands. | Single-quote escaping (`'=...`) in `export_sanitizer.py` across all tabular export pipelines. |
| **Cross-Engagement Leakage** | Auditor querying documents or financial lines belonging to another client. | Strict `engagement_id` filtering enforced at repository and SQL layer. |
| **RAG Prompt Injection** | Embedded prompt manipulation payloads inside audited PDFs. | Delimiter sanitization, `<think>` token removal, and structured JSON output validation. |
| **Archive Tampering** | Post-archival modification of SQLite database files. | SHA-256 manifest hashing and SQLite connection lock via `PRAGMA query_only = ON`. |
| **Maker-Checker Bypass** | Single user authoring, reviewing, and signing off on their own working paper. | Segregation-of-duties validation and open review notes blocking in `WorkingPaperService`. |
