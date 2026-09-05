# FinAuditPro — Security Architecture & Threat Defense Guide

FinAuditPro enforces a defense-in-depth security model tailored specifically for
offline-first statutory financial audit practice with zero outbound client data transmission.

---

## 1. Fail-Closed Role-Based Access Control (RBAC)

Access control is enforced at the application service layer via
`src/finauditpro/application/security/rbac.py`:

| Role               | Firm / Client Admin | Engagement Config | Upload Documents | Sign-Off Working Papers | Archive / Reopen |
| :----------------- | :-----------------: | :---------------: | :--------------: | :---------------------: | :--------------: |
| **Partner**        |         Yes         |        Yes        |       Yes        |           Yes           |       Yes        |
| **Manager**        |         No          |        Yes        |       Yes        |    No (Review Only)     |        No        |
| **Senior Auditor** |         No          |        No         |       Yes        |  No (Draft/Edit Only)   |        No        |
| **Associate**      |         No          |        No         |       Yes        |     No (View Only)      |        No        |

---

## 2. Multi-Tenant Engagement Isolation

All database tables partition sensitive records by `engagement_id`. Repositories
mandate `engagement_id` parameters in every retrieval and modification query to
prevent cross-engagement data leakage.

---

## 3. Cryptography & Column-Level Encryption

- Sensitive tokens and metadata at rest are protected via
  `cryptography.fernet.Fernet` with machine-local PBKDF2 salt derivation
  (`src/finauditpro/infrastructure/security/encryption.py`).
- Exported backup bundles are encrypted using PBKDF2 key derivation with 100,000
  iterations and unique 16-byte salts.

---

## 4. Immutable Audit Trail

All critical security events (login, user creation, document upload, sign-off,
archival, roll-forward) are logged to the `audit_events` ledger table with
sequential SHA-256 block hashing for tamper evidence.

---

## 5. Threat Vectors & Adversarial Mitigations

| Threat Vector                       | Description                                                                | Technical Countermeasure                                                                      |
| :---------------------------------- | :------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| **Path Traversal / ZIP Slip**       | Malicious document filename or backup entry attempting directory escape.   | Strict sanitization via `document_security.py` and canonical path validation before write.    |
| **Formula Injection**               | Malicious cell values in CSV/XLSX exports executing shell commands.        | Single-quote escaping (`'=...`) in `export_sanitizer.py` across all tabular export pipelines. |
| **Cross-Engagement Leakage**        | Auditor querying documents or financial lines belonging to another client. | Strict `engagement_id` filtering enforced at repository and SQL layer.                        |
| **Tampering with Audit Events**     | Adversary attempting to alter or delete recorded audit entries.            | SQLite triggers preventing `UPDATE` and `DELETE` on `audit_events`.                           |
| **Segregation of Duties Violation** | Preparer attempting to sign off on their own working paper.                | Strict runtime check in `WorkingPaperService` blocking self-sign-off.                         |

---

## 6. Authentication & Password Security

- **PBKDF2-HMAC-SHA256**: All user passwords are encrypted using 100,000 PBKDF2
  iterations with unique 16-byte random salts.
- **Constant-Time Verification**: Verification utilizes `secrets.compare_digest`
  to prevent timing analysis attacks.
- **Mandatory First-Login Password Change**: Pre-seeded administrator
  credentials must be replaced with a compliant master password (minimum 8
  characters, letters, and numbers/symbols) before workspace access is granted.
  | **RAG Prompt Injection** | Embedded prompt manipulation payloads inside
  audited PDFs. | Delimiter sanitization, `<think>` token removal, and
  structured JSON output validation. | | **Archive Tampering** | Post-archival
  modification of SQLite database files. | SHA-256 manifest hashing and SQLite
  connection lock via `PRAGMA query_only = ON`. | | **Maker-Checker Bypass** |
  Single user authoring, reviewing, and signing off on their own working paper.
  | Segregation-of-duties validation and open review notes blocking in
  `WorkingPaperService`. |
