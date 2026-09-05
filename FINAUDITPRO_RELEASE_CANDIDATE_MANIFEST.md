# FINAUDITPRO — RELEASE CANDIDATE FREEZE SPECIFICATION

**Document Version:** 1.0.0  
**Freeze Status:** SEALED & FROZEN  
**Release Target:** FinAuditPro Enterprise Edition v1.2.0 (GA Candidate)  
**Audit Partner Sign-Off:** CA Rajesh Sharma (FCA, DISA, Lead Independent Reviewer)  

---

## 1. Release Identification & Baseline

| Property | Value |
| :--- | :--- |
| **Application Name** | FinAuditPro |
| **Application Version** | `1.2.0` |
| **Git Commit SHA** | `a7520b767ace6e4923e75bfc08a10ede5a83cd1b` |
| **Release Branch** | `main` |
| **Target Architecture** | Local / Offline-First Desktop (macOS arm64 / Windows x64 / Linux x86_64) |
| **Python Runtime** | Python 3.12+ (Validated on Python 3.14.7) |
| **Database Engine** | SQLite 3 with WAL (Write-Ahead Logging), Foreign Keys Enforced |
| **Schema Version** | 79 Relational Tables (Migrations v001 through v019 applied) |

---

## 2. Dependency Manifest & Lock State

### Runtime Dependencies
- `PySide6>=6.8,<7` — Native cross-platform Qt6 UI framework
- `SQLAlchemy>=2.0,<3` — Enterprise SQL toolkit and transactional ORM
- `pydantic>=2.7,<3` — Data parsing, schema validation, and domain modeling
- `cryptography>=42.0` — Scrypt KDF, AES-256/Fernet column encryption, and PKI
- `openpyxl>=3.1.0` — Excel financial statements & lead schedule ingestion/export
- `reportlab>=4.0` — Programmatic PDF generation with digital watermarking
- `httpx>=0.27` — Async local LM Studio/Ollama HTTP transport with circuit breakers
- `pyotp>=2.9.0` — RFC 6238 TOTP two-factor authentication
- `qrcode>=7.4.2` — 2FA enrollment QR code generation
- `pymupdf>=1.24` — PDF parsing, text extraction, and digital evidence processing
- `pillow>=10.3` — Document rasterization and OCR preprocessing
- `faiss-cpu>=1.8.0` — Offline vector indexing for audit standards & workpapers
- `matplotlib>=3.8.0` — Analytical graphs and financial variance charting

### Test & Quality Assurance Tooling
- `pytest>=8.2`, `pytest-cov>=5.0`, `ruff>=0.5`, `mypy>=1.10`, `pytest-qt>=4.4`

---

## 3. Storage & Directory Layout

The application operates with zero cloud lock-in under isolated directory anchors:
```text
${FINAUDITPRO_DATA_DIR:-~/.finauditpro}/
├── finauditpro.db              # SQLite database (WAL mode, PRAGMA foreign_keys = ON)
├── finauditpro.db-wal          # Write-Ahead Log
├── finauditpro.db-shm          # Shared Memory file
├── master_key.enc              # AES-256 DEK wrapped by Scrypt-derived KWK
├── documents/                  # Stored evidence PDFs & workpapers (SHA-256 named)
├── exports/                    # Sealed audit reports, Schedule III FS, XML filings
├── backups/                    # Encrypted *.fapb engagement archives
└── logs/                       # Immutable system & audit logs
```

---

## 4. Cryptographic & Security Baseline

1. **At-Rest Column Encryption**: AES-256-CBC with HMAC-SHA256 (Fernet) anchored by an scrypt-derived Key Wrapping Key (KWK) (`N=32768, r=8, p=1`).
2. **Audit Trail Cryptographic Invariant**: Continuous forward SHA-256 hash-chaining across all `audit_events`. Genesis hash: `GENESIS_HASH`. Block mutation immediately breaks chain verification.
3. **Authentication**: PBKDF2-HMAC-SHA256 (100,000 iterations) with 16-byte random salt, constant-time comparison, RFC 6238 TOTP 2FA, and brute-force lockout after 5 consecutive failures.
4. **Formula Injection Neutralization**: All dynamic spreadsheet exports apply prefix quotation (`'`) to cells starting with `=`, `+`, `-`, `@`, `|`, `\t`, `\r`.
5. **Tamper-Seal Invariant**: Post-finalization mutations on completed engagements (status `COMPLETED` or `ARCHIVED`) are blocked at the repository and service levels with fail-closed exceptions.
