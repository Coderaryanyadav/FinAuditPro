# FinAuditPro Backup, Disaster Recovery & Restore (v1.0.0)

## 1. Backup Strategy & Transactional Safety
Because FinAuditPro operates in SQLite WAL (Write-Ahead Logging) mode, naive file copying while the application is running risks capturing inconsistent database pages.

To ensure transactional safety:
1. **WAL Checkpoint**: The backup engine executes `PRAGMA wal_checkpoint(TRUNCATE);` to flush all uncommitted journal transactions to the main database file.
2. **Atomic SQLite Backup API**: Utilizes Python's native `sqlite3.Connection.backup()` method to take a consistent live snapshot without database locking or corruption.
3. **Evidence Vault Bundling**: Working papers, OCR text caches, and uploaded audit evidence files are bundled into the encrypted backup archive.
4. **Manifest & SHA-256 Digest**: A cryptographic manifest containing SHA-256 hashes of all bundled components is embedded into the backup container.

---

## 2. Backup Archive Encryption
Backup archives are optionally encrypted using AES-256-CBC / Fernet with a user-supplied recovery passphrase:
- **Passphrase Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations + 16-byte random salt).
- **Authentication**: HMAC-SHA256 authenticated envelope prevents archive tampering.

---

## 3. Disaster Recovery & Restoration Lifecycle
Restoration performs rigorous verification before modifying local state:
1. **Passphrase Verification**: Attempts decryption; fails immediately if passphrase is incorrect or signature is invalid.
2. **Manifest Check**: Computes SHA-256 hashes of extracted files against the embedded manifest.
3. **Integrity Validation**: Runs SQLite `PRAGMA integrity_check` on the restored database.
4. **Audit Trail Verification**: Recomputes the SHA-256 hash chain across all `audit_events` from genesis to the latest event.
5. **Atomic Switch**: Replaces the active working database only after all verification gates pass.
