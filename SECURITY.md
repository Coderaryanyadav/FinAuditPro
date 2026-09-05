# FinAuditPro — Security Policy & Threat Model

**Version:** 1.0.0  
**Status:** Active Production Security Policy  

---

## 1. Security Architecture & Threat Model

FinAuditPro is designed as an **offline-first local desktop audit operating system**. It processes all client accounting data, document OCR, evidence files, and report generation locally on the practitioner's machine.

---

## 2. Implemented Security Controls

### A. Authentication & Brute-Force Defense
* **Mandatory Custom Onboarding:** No default accounts or hardcoded credentials exist. On first launch, the Administrator Setup Wizard prompts the user to configure custom credentials.
* **Password Hashing:** Passwords are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user 16-byte random salts.
* **Multi-Layered Lockout Protection:** 5 consecutive failed login attempts trigger an automatic 15-minute lockout. State is tracked simultaneously in process memory, HMAC-SHA256 authenticated files, and an immutable SQLite database ledger, ensuring lockout cannot be bypassed by deleting local state files or restarting the application.

### B. Cryptographic Key Management
* **Passcode-Derived Key Wrapping:** Data Encryption Keys (DEK) are 256-bit random keys wrapped via Key Wrapping Keys (KWK) derived using memory-hard Scrypt (`N=16384`, `r=8`, `p=1`, 32-byte length, 16-byte salt).
* **Fail-Closed Cipher Access:** Encryption functions raise `RuntimeError` if uninitialized. No fallback master secrets exist.
* **Tamper-Evident Decryption:** Decryption of tampered or corrupted ciphertext raises `ValueError` rather than silently falling back to plaintext.

### C. Audit Trail Immutability
* **Cryptographic Hash Chaining:** Every audit event includes the SHA-256 hash of the preceding event, forming an unbroken cryptographic chain.
* **Database Trigger Protection:** SQLite `BEFORE UPDATE` and `BEFORE DELETE` triggers reject any raw SQL manipulation with an `IntegrityError`.
* **Monotonic Ordering:** Ancestor resolution and chain verification order strictly by physical SQLite `rowid` to prevent same-second collision ambiguities.

### D. Authorization & Maker-Checker
* **Role-Based Access Control (RBAC):** Permissions are validated against server-side session state.
* **Segregation of Duties (SoD):** Working paper preparers cannot perform Partner final sign-offs on their own workpapers.
* **Engagement Isolation:** Single-tenant engagement boundaries prevent cross-engagement data or evidence leakage.

### E. Backup & Disaster Recovery
* **WAL Checkpointing:** `PRAGMA wal_checkpoint(TRUNCATE)` is executed before backup creation to ensure consistency.
* **Encrypted Archives:** Backups are bundled as ZIP archives with SHA-256 manifests and encrypted using PBKDF2 + Fernet AES-128-CBC.
* **Atomic Page Restoration:** Restorations use standard library `sqlite3.Connection.backup()` to restore database pages safely while disposing SQLAlchemy connection pools.

### F. Export & Input Sanitization
* **Formula Injection Neutralization:** Cell values starting with `=`, `+`, `-`, or `@` are automatically escaped with single quotes (`'`) during CSV and XLSX generation.
* **Prompt Injection Defense:** Local AI prompts strip reasoning tags (`<think>`) and neutralize untrusted prompt injection patterns.

---

## 3. Recommended Deployment Controls

* **Workstation Protection:** Ensure practitioner machines utilize full-disk encryption (e.g., Apple FileVault, Windows BitLocker) and standard OS-level account access controls.
* **Local LM Studio Configuration:** When using local AI features, ensure the LM Studio server is bound to the loopback interface (`127.0.0.1:1234`).

---

## 4. Known Security Boundaries & Limitations

* **Local OS Root Access:** Users with administrative OS root or debugger privileges on the workstation can inspect local process memory.
* **Backup Passphrase Management:** Encrypted backup archives cannot be decrypted if the firm loses the backup passphrase.
