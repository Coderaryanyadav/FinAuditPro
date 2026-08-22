# Encrypted Backup & Atomic Restore

FinAuditPro provides passphrase-encrypted backup packaging and safe atomic restore workflows.

---

## 1. Backup Packaging Workflow

Implemented in `src/finauditpro/application/services/backup_restore_service.py`:
1. **Engagement Snapshot**: Exports engagement database rows, document storage files, and evidence links.
2. **Manifest Generation**: Generates `manifest.json` containing SHA-256 digests for all files.
3. **ZIP Bundling**: Compresses the dataset into a standard ZIP structure.
4. **Passphrase Encryption**: Encrypts the archive using Fernet with PBKDF2 key derivation (100,000 iterations).

---

## 2. Safe Atomic Restore Workflow

To protect against corrupted or malicious backups, restore operates strictly out-of-place before replacing the active database:
```text
Verify Passphrase & Decrypt to Isolated Temp Directory
        ⬇
Validate Manifest SHA-256 Hashes
        ⬇
Inspect SQLite Integrity & Audit Chain
        ⬇
Atomically Swap / Import Records into Active Database
        ⬇
Re-verify Post-Restore Database State
```
If any checksum fails, the restore aborts without altering the active database.
