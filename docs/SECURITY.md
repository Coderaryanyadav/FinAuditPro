# Security & Governance Policy

## Cryptographic Security
- **Password Hashing**: PBKDF2-HMAC-SHA256 with random salt per account.
- **Backup Encryption**: AES-256 CBC encryption for automated database snapshot backups.
- **Audit Trails**: Immutable SQLite audit log tracking user authentication, engagement state changes, and document parsing events.

## Role-Based Access Control (RBAC)
- **Roles**: Audit Partner, Audit Manager, Senior Auditor, Junior Auditor.
- **Enforcement**: Permission checks verified at the service and UI controller levels before mutating client or engagement records.
