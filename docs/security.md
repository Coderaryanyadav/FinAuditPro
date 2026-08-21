# FinAuditPro — Security Architecture & Threat Model

FinAuditPro handles sensitive audit working papers, trial balances, general ledgers, and confidential client records. Security is designed into every layer.

---

## 1. Core Security Guarantees

1. **Air-Gapped Privacy Posture**: FinAuditPro defaults to a strictly air-gapped configuration (`allow_cloud_ai: false`). All AI capabilities run exclusively against a user-managed local LM Studio REST server (`http://localhost:1234`).
2. **Fail-Closed Role-Based Access Control (RBAC)**: Fine-grained permissions (Partner, Manager, Senior, Staff) enforced at the application service layer.
3. **Read-Only Sealed Engagement Archive**: Archived audit engagements lock SQLite database connections in `PRAGMA query_only=ON` mode with cryptographic SHA-256 seal manifest verification.
4. **Formula Injection Escaping**: XLSX/CSV export pipeline sanitizes leading `=`, `+`, `-`, `@` triggers.
5. **Fernet Encrypted Backups**: Automated database and document backups encrypted using AES-128-CBC with Fernet symmetric keys.

---

## 2. Multi-Tenant Client Boundary Protection

Audit engagements are strictly isolated by `client_id` and `engagement_id`. Cross-client roll-forwards or document retrievals raise `PermissionDeniedError` at the service layer.

---

## 3. Vulnerability Reporting

To report security vulnerabilities, see [SECURITY.md](../SECURITY.md).
