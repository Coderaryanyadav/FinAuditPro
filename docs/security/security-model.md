# FinAuditPro Security Architecture & Model

FinAuditPro enforces a defense-in-depth security model tailored for air-gapped financial audit practice.

---

## 1. Fail-Closed Role-Based Access Control (RBAC)

Access control is enforced in application services via `src/finauditpro/application/security/rbac.py`:

| Role | Firm / Client Admin | Engagement Config | Upload Documents | Sign-Off Working Papers | Archive / Reopen |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Partner** | Yes | Yes | Yes | Yes | Yes |
| **Manager** | No | Yes | Yes | No (Review Only) | No |
| **Senior Auditor** | No | No | Yes | No (Draft/Edit Only) | No |
| **Associate** | No | No | Yes | No (View Only) | No |

---

## 2. Multi-Tenant Engagement Isolation

All database tables partition sensitive records by `engagement_id`. Repositories mandate `engagement_id` parameters in every retrieval and modification query to prevent cross-engagement data leakage.

---

## 3. Cryptography & Column-Level Encryption

Sensitive tokens and metadata at rest are protected via `cryptography.fernet.Fernet` with machine-local PBKDF2 salt derivation (`src/finauditpro/infrastructure/security/encryption.py`).

---

## 4. Immutable Audit Trail

All critical security events (login, user creation, document upload, sign-off, archival, roll-forward) are logged to the `audit_events` ledger table with sequential SHA-256 block hashing for tamper evidence.
