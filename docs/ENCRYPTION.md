# FinAuditPro Cryptographic & Key Management Architecture (v1.0.0)

## 1. Cryptographic Invariants
1. **Zero Hardcoded Secrets**: No encryption keys, fallback salts, or static initialization vectors exist in source or binaries.
2. **Fail-Closed Policy**: If cryptographic material is uninitialized or ciphertext verification fails, the application aborts immediately with a strict exception. It NEVER falls back to plain text or insecure default keys.
3. **Authenticated Encryption**: All sensitive columns and confidential exports use AES-128-CBC with HMAC-SHA256 authenticated envelope (Fernet).

---

## 2. Key Hierarchy: DEK & KWK
```
+-------------------------------------------------------------+
| User Passcode / Workstation Hardware Identity               |
+------------------------------+------------------------------+
                               |
                               v (PBKDF2-HMAC-SHA256, 100,000 iterations)
+------------------------------+------------------------------+
| Key Wrapping Key (KWK)                                      |
+------------------------------+------------------------------+
                               | (Fernet Encrypt / Decrypt)
                               v
+------------------------------+------------------------------+
| Data Encryption Key (DEK)                                   |
+-------------------------------------------------------------+
```

1. **Passcode-Derived KWK**: Derived from the user's master passcode using PBKDF2-HMAC-SHA256 with 100,000 rounds and a unique cryptographically random 16-byte salt.
2. **Column Encryption DEK**: A 256-bit cryptographically random key generated upon first database initialization, stored encrypted on disk wrapped by the KWK.
3. **Memory Hygiene**: Encryption keys reside strictly in memory for active user sessions and are zeroed upon session lock or application exit.

---

## 3. Hash Chaining & Evidence Seals
- **Audit Event Chain**: Each event calculates `event_hash = SHA256(previous_hash || timestamp || event_type || user_id || payload)`. Monotonically ordered by SQLite `rowid`.
- **Evidence Integrity**: Uploaded audit evidence (PDFs, scans, CSVs) generates a SHA-256 digest at ingestion time.
