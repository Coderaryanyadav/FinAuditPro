# Changelog

All notable changes to FinAuditPro are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-05

### Added
- **Integer Paise Financial Engine:** Core 64-bit integer paise architecture for general ledger, trial balance, and adjustment accounting.
- **Standards on Auditing Workflows:** Complete workflow support for SA 230, SA 315, SA 320, SA 330, SA 450, SA 510, SA 560, SA 570, and SA 580.
- **Electronic Working Papers:** Scaffolding, indexing, evidence linking, and content hash provenance binding.
- **Maker-Checker Segregation of Duties:** Role-enforced review levels with preparer self-sign-off prevention.
- **Tamper-Evident Audit Trail:** Chained SHA-256 event log with monotonic SQLite `rowid` ordering and database triggers rejecting `UPDATE` and `DELETE` queries.
- **Passcode-Derived Key Wrapping:** Scrypt/PBKDF2 KDF + Fernet DEK key wrapping with passcode rotation support.
- **Multi-Layered Lockout Protection:** In-process counter + HMAC-SHA256 authenticated state + immutable SQLite ledger tracking surviving file deletions and restarts.
- **WAL-Safe Encrypted Backup & Restore:** `PRAGMA wal_checkpoint(TRUNCATE)` synchronization + atomic `sqlite3.Connection.backup()` restoration.
- **Formula Injection Defense:** Sanitization of dangerous formula characters in exported spreadsheets.
- **Local AI & Document Pipeline:** Local PDF vector/OCR text extraction, SQLite FTS5 search, and optional local LM Studio RAG integration.
- **GitHub Hardening & Governance:** Integrated CI/CD workflows, automated security scanning (Bandit & Ruff), issue templates, and PR template.

### Changed
- Converted all financial calculation modules to strict 64-bit integer paise.
- Enforced monotonic SQLite `rowid` ordering across all audit trail queries.

### Removed
- Removed legacy fallback encryption secret `"FinAuditPro-Local-Column-Secret-Key"`.
- Removed default administrator credentials in favor of mandatory first-run onboarding.
- Removed silent plaintext fallback on decryption errors.
