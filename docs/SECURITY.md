# Security & Governance Policy

## Cryptographic Security
- **Password Hashing**: PBKDF2-HMAC-SHA256 with minimum 100,000 to 600,000 iterations and random salt per account.
- **Live Database Encryption**: Page-level AES-256 SQLCipher transparent encryption derived from installation secret key (`.crypto_key` / `.crypto_salt`). Loss of `.crypto_key` prevents DB decryption.
- **Backup Encryption**: AES-256 (Fernet) vault encryption for database backups.
- **Digital Integrity**: Ed25519 asymmetric signatures for internal audit ledger hash-chain integrity verification.
- **Audit Trails**: Immutable audit log tracking authentication, RBAC authorization, and document parsing events.

## Role-Based Access Control (RBAC) & Service Isolation
- **Roles**: Administrator, Audit Partner, Audit Manager, Senior Auditor, Articled Assistant, Read Only.
- **Enforcement**: Mandatory service-layer permission gates (`MANAGE_CLIENTS`, `UPLOAD_DOCUMENTS`, `EDIT_WORKING_PAPERS`, `REVIEW_WORKING_PAPERS`, `SIGN_REPORTS`, `VIEW_ANALYTICS`). Unauthenticated session calls raise `AuthError`.

## Client-Server & API Architecture
- **FastAPI REST Service**: Multi-user client-server backend support with JWT bearer token authentication (8-hour expiration).
- **PostgreSQL / Multi-Tenant Support**: Concurrent multi-user access support via PostgreSQL configuration override (`FINAUDITPRO_DATABASE_URL`).

