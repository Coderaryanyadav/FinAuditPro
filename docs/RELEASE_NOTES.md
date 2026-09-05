# FinAuditPro v1.0.0 — Official Release Notes

**Release Version:** 1.0.0  
**Release Date:** 2026-09-05  
**Target Platform:** Desktop Workstations (macOS Apple Silicon & Intel, Windows x64, Linux x86_64)  
**License:** Proprietary / Commercial Statutory Software  

---

## 1. Product Overview

FinAuditPro is an **offline-first desktop statutory and internal audit intelligence operating system** engineered specifically for Indian Chartered Accountancy practices. It executes 100% locally on practitioner workstations without cloud dependencies or mandatory external network transmission.

---

## 2. Key Capabilities in v1.0.0

### A. Core Accounting & Invariant Engines
* **Integer Paise Arithmetic:** All financial computations execute in 64-bit integer paise (₹1.00 = 100 paise), preventing floating-point rounding drift.
* **Double-Entry Balancing:** Invariant validation rejecting imbalanced or one-sided journal entries at the domain boundary.
* **Trial Balance & General Ledger Ingestion:** Multi-format CSV/XLSX parser with automatic column classification, opening balance tie-out, and discrepancy detection.
* **Schedule III Financial Statement Mapping:** Direct classification and aggregation of trial balance balances into Division I / Division II balance sheets and statements of profit and loss.

### B. Audit Methodology & Professional Standards Support
* **SA 230 (Audit Documentation):** Electronic working paper scaffolding, hierarchical indexing, reviewer sign-offs, and content hash provenance.
* **SA 315 / SA 330 (Risk & Procedures):** Qualitative Risk of Material Misstatement (RoMM) matrix, assertion coverage mapping, and substantive audit procedure linking.
* **SA 320 (Materiality):** Benchmark-driven materiality calculation (Overall Materiality, Performance Materiality, Clearly Trivial Threshold) with auditor justification overrides.
* **SA 450 (Evaluation of Misstatements):** Aggregate uncorrected misstatement accumulation and materiality comparison.
* **SA 510 (Initial Engagements & Opening Balances):** Multi-year roll-forward tie-out comparing prior-year audited closing balances to current-year opening balances.
* **SA 560, SA 570 & SA 580 (Completion & Reporting):** Subsequent events tracking, Going Concern distress modeling, Management Representation Letter chronology checks, and finalization checklist gates.

### C. Security Architecture & Threat Defense
* **Passcode-Derived Key Wrapping:** Scrypt KDF (`N=16384`, `r=8`, `p=1`) derives Key Wrapping Keys (KWK) protecting a 256-bit Fernet Data Encryption Key (DEK). Zero hardcoded fallback secrets.
* **Multi-Layered Brute-Force Lockout:** In-process session tracking, HMAC-SHA256 authenticated integrity verification, and immutable SQLite `audit_events` ledger tracking. Lockout persists across application restarts and file deletions.
* **Cryptographic Audit Trail:** Chained SHA-256 event ledger with SQLite `BEFORE UPDATE` and `BEFORE DELETE` database triggers rejecting unauthorized modification. Monotonic physical `rowid` ordering prevents same-second collision ambiguities.
* **Maker-Checker Segregation of Duties:** Preparers cannot self-approve working papers. Partner final sign-offs require authenticated Partner roles.
* **WAL-Safe Encrypted Backups:** Automatic `PRAGMA wal_checkpoint(TRUNCATE)` before archiving, coupled with atomic `sqlite3.Connection.backup()` restoration and AES-128 archive encryption.
* **Export Sanitization:** Formula injection escaping (`'=...`) across all exported CSV and XLSX files.

---

## 3. Verified Release Metrics

* **Full Pytest Suite:** 307 passed, 0 failed, 0 skipped, 0 errors.
* **Clean-Room Acceptance:** 2 consecutive passes across 22 lifecycle steps in fresh environments.
* **Database Schema:** 80 tables managed via SQLite WAL migrations.

---

## 4. Known Limitations & Operating Boundaries

1. **Host-Level Root Access:** As with all client-side desktop software, users with OS-level root/debugger access can inspect process memory outside the application boundary.
2. **Local AI Model Integration:** Optional AI assistant features interface with a local LM Studio server running on `http://localhost:1234`. The UI gracefully degrades when LM Studio is offline.
