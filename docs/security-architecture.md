# FinAuditPro — Security Architecture & Cryptographic Integrity

This document describes the cryptographic mechanisms, tamper-evident seals, and security controls enforced by **FinAuditPro**.

---

## 1. Cryptographic Audit Log Append-Only Integrity

Historical audit actions are recorded in the `audit_events` table using SHA-256 hash-chaining:

$$Hash_n = \text{SHA-256}(Hash_{n-1} \parallel Actor \parallel Action \parallel Timestamp \parallel EntityID)$$

### SQLite Append-Only Triggers
The database prevents historical audit tampering via triggers:
```sql
CREATE TRIGGER prevent_audit_events_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit log entries are immutable and append-only.');
END;

CREATE TRIGGER prevent_audit_events_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit log entries cannot be deleted.');
END;
```

---

## 2. Encrypted Backup Architecture

Exported `.zip` backup archives are encrypted using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).

### Key Derivation
Keys are derived using PBKDF2 with SHA-256 (100,000 iterations) and a 16-byte cryptographically secure random salt generated per backup file (`os.urandom(16)`).

---

## 3. Path Traversal & Zip-Slip Protection

Archive extraction validates every file path prior to writing:
```python
target_path = (destination_dir / member_name).resolve()
if not str(target_path).startswith(str(destination_dir.resolve())):
    raise SecurityError("Path traversal or Zip-Slip attempt detected.")
```
