# FinAuditPro — Comprehensive Application Threat Model

This document outlines the threat model, attack vectors, trust boundaries, mitigations, and residual risks for **FinAuditPro**.

---

## 1. Assets Needing Protection

1. **Audit Working Papers & Sign-Off Records**: Confidential auditor attestations, review notes, and work performed.
2. **Financial Datasets**: General ledgers, trial balances, bank statements, invoice listings.
3. **Client Identification Records**: Client names, PAN, GSTIN, legal entity profiles.
4. **Original Source Documents**: Invoices, contracts, scanned PDFs, bank statements.
5. **Audit Evidence & Findings**: Identified anomalies, Benford exceptions, materiality thresholds, draft findings.
6. **Local Vector Embeddings & AI Context**: Document chunks, embeddings in FAISS, search indices.
7. **Cryptographic Keys & Database Seals**: Machine Fernet encryption keys, SHA-256 archive seal manifests.

---

## 2. Threat Agents & Attack Vectors

| ID | Threat Agent | Description / Attack Vector | Severity | Mitigation Implemented |
| :--- | :--- | :--- | :---: | :--- |
| **TA-1** | Malicious Document | PDF or image containing embedded scripts, malformed objects, or prompt injection text. | `HIGH` | PyMuPDF safe parsing, text sanitization (`<think>` tags & override disarming), zero JS execution. |
| **TA-2** | Malicious Spreadsheet | XLSX or CSV file containing formula injection (`=`, `+`, `-`, `@`) targeting auditor's spreadsheet viewer. | `HIGH` | `escape_formula_injection()` cell sanitization on export. |
| **TA-3** | Cross-Client Access | User attempting to view Client A data while in Client B scope. | `CRITICAL` | Service-layer tenant scope verification (`PermissionDeniedError`). |
| **TA-4** | Tampering with Audit Log | Attacker or user modifying historical `audit_events` rows to hide actions. | `CRITICAL` | SQLite `BEFORE UPDATE/DELETE` triggers (`RAISE(ABORT)`) and SHA-256 hash-chaining. |
| **TA-5** | Path Traversal / Zip-Slip | Archive containing `../../secret` paths during archive import or backup restore. | `HIGH` | Path normalization and parent-directory traversal rejection. |
| **TA-6** | Tampering Sealed Archive | Attacker altering files inside a frozen/archived `.zip` bundle. | `HIGH` | `sha256_manifest.json` verification; recomputing digests on launch/restore. |
| **TA-7** | Malicious Local Process | Unauthorized process reading database files on disk. | `MEDIUM` | Host OS Full-Disk Encryption (FileVault / BitLocker); Fernet encrypted backups. |
| **TA-8** | Unauthorized Sign-Off | Non-authorized role attempting maker-checker sign-off or reopening archive. | `HIGH` | Service-layer RBAC checking (`RoleEnum.PARTNER` enforced). |
| **TA-9** | Prompt Injection via AI | Attacker embedding instructions in invoices to trick local LLM into altering conclusions. | `HIGH` | Strict system/user prompt separation; auditor manual override requirement. |
| **TA-10**| Data Leakage via Telemetry | Application leaking client data to external cloud APIs. | `HIGH` | Air-gapped default (`allow_cloud_ai: false`); zero cloud telemetry network calls. |

---

## 3. Trust Boundaries

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ WORKSTATION TRUST BOUNDARY (Host OS & Full-Disk Encryption)                            │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ PYSIDE6 DESKTOP UI (Presentation Layer)                                        │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ Service RBAC & Scope Verification          │
│   ┌───────────────────────────────────────▼────────────────────────────────────────┐   │
│   │ APPLICATION SERVICE LAYER (Business Logic & Access Enforcement)                │   │
│   └───────────────────┬────────────────────────────────────────┬───────────────────┘   │
│                       │ Database Access                        │ RAG Retrieval Filter  │
│   ┌───────────────────▼───────────────────┐    ┌───────────────▼───────────────────┐   │
│   │ INFRASTRUCTURE (SQLite WAL / FTS5)    │    │ LOCAL AI (LM Studio RAG & FAISS)  │   │
│   └───────────────────────────────────────┘    └───────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Residual Risks & Documented Disclaimers

1. **Host Workstation Compromise**: If an attacker gains full root/administrator privileges on the auditor's local workstation, they can inspect raw memory or unencrypted temporary files. **Mitigation**: Auditor must enforce OS-level FileVault / BitLocker and local password protection.
2. **Local LLM Model Hallucination**: AI-generated suggestions may be incorrect. **Mitigation**: All AI outputs carry disclaimers requiring auditor review and manual confirmation.
