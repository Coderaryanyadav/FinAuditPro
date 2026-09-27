# FinAuditPro — Security Architecture & Threat Defense Model

## 1. Core Security Guarantees
1. **Zero Cloud Egress:** Client financial data never leaves the local machine. Network isolation tests ensure no socket connections outside `127.0.0.1`.
2. **Cryptographic Storage:** Sensitive workspace databases and backups are encrypted at rest using AES-128-CBC via Fernet with PBKDF2-HMAC-SHA256 key derivation (100,000 iterations).
3. **Role-Based Access Control (RBAC):** Rigid enforcement across 4 tiers: `Partner`, `Manager`, `Senior`, and `Assistant`.
4. **Formula Injection Defense:** All CSV/Excel exports sanitize dangerous formula prefixes (`=`, `+`, `-`, `@`, `	`, ``) to prevent DDE injection in external spreadsheet viewers.
5. **Prompt Injection Defense:** Local LLM queries pass through an AST sanitizer and input fence to strip hostile jailbreak instructions before reaching LM Studio.
