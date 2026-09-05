<div align="center">

<h1>FinAuditPro</h1>

<h3>Offline-First Audit Intelligence Workspace for Indian Audit Practice</h3>

<p><i>Workflows and mathematical controls supporting Indian statutory audit practice (SA 230, SA 320, SA 510, CARO 2020, Schedule III)</i></p>

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.8-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![SQLite WAL](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Local AI](https://img.shields.io/badge/Local_AI-Optional_LM_Studio-4F46E5?style=for-the-badge&logo=openai&logoColor=white)](https://lmstudio.ai/)
[![Tests](https://img.shields.io/badge/Tests-307%2F307%20passing-brightgreen?style=for-the-badge&logo=pytest)](tests/)
[![Type Checked](https://img.shields.io/badge/MyPy-Strict%20Passed-blue?style=for-the-badge&logo=python)](pyproject.toml)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black?style=for-the-badge&logo=ruff)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## Overview

**FinAuditPro** is an offline-first desktop workstation engineered for Indian
Chartered Accountants (CAs), audit managers, and engagement teams. It provides
deterministic integer paise mathematical analytics, automated SA 320 materiality
calculations, PyMuPDF and Tesseract OCR document extraction, SQLite FTS5
full-text indexing, electronic working paper maker-checker workflows, and SQC 1
sealed archival — operating locally on the practitioner's workstation with
**zero outbound client data transmission**.

---

## Core Capabilities

| Capability Area                       | Functional Scope & Supported Workflows                                                                                                                                                                                                    |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Workspace & Multi-Tenancy**         | 3-tier hierarchy (`Firm` $\rightarrow$ `Client` $\rightarrow$ `Engagement`), financial year scoping (`FY 2024-25`), single-tenant SQLite partition with strict `engagement_id` query isolation.                                           |
| **Deterministic Financial Analytics** | Automated Trial Balance, General Ledger, and Bank Statement ingestion; **exact 64-bit integer paise** calculation; Benford's 1st Law Chi-Square ($\chi^2$) analysis; duplicate payment clustering ($\pm 3$-day window); outlier z-scores. |
| **Audit Matrix & Materiality**        | Supports SA 320 materiality workflows (Overall, Performance, and Clearly Trivial threshold calculations based on Revenue/PBT/Assets benchmarks); risk assessment and procedure mapping.                                                   |
| **Document Processing & OCR**         | Ingestion of PDF, PNG, JPG, CSV, TXT; PyMuPDF vector text extraction with local Tesseract OCR fallback; SQLite FTS5 full-text search; SHA-256 evidence digests.                                                                           |
| **Working Papers & Sign-Off**         | Supports SA 230 electronic working paper lifecycle (`Draft` $\rightarrow$ `InReview` $\rightarrow$ `SignedOff`); maker-checker segregation of duties; open review notes blocking validation; SHA-256 content hash locking.                |
| **Statutory Reporting & Export**      | Dynamic ReportLab PDF generation with automatic `"DRAFT"` watermark management; spreadsheet formula-injection escaping (`'=...`) in OpenPyXL exports; full audit event provenance logging.                                                |
| **Archival & Opening Balances**       | SQC 1 engagement sealing with SHA-256 manifest validation; SQLite `PRAGMA query_only = ON` lock; multi-year roll-forward with carried-forward findings; SA 510 opening balance tie-out variance analysis.                                 |
| **Local AI Assistance (Optional)**    | Optional integration with local LM Studio REST endpoint (`http://localhost:1234`); prompt injection defense; reasoning token neutralization; mandatory `[AI Advisory]` tagging with human auditor sign-off.                               |

---

## Security & Privacy Model

- **Offline-First / Zero Outbound Client Data Transmission**: All database
  transactions, analytics, OCR extraction, vector indexing, and report
  generation execute exclusively on the local machine.
- **Fail-Closed Authenticated Encryption**: AES-128-CBC with Fernet
  authenticated envelope; Scrypt/PBKDF2 passcode key wrapping; zero hardcoded
  fallback secrets.
- **Cryptographic Audit Trail**: Monotonically ordered SHA-256 hash-chained
  event ledger protected by SQLite database triggers prohibiting `UPDATE` and
  `DELETE` queries.
- **Multi-Layer Lockout Protection**: 3-tier defense (memory +
  HMAC-authenticated state + immutable SQLite ledger) surviving state file
  deletion and process restart.
- **Formula Injection Defense**: XLSX and CSV export pipelines neutralize
  leading `=`, `+`, `-`, `@`, `\t`, `\r` trigger characters.

---

## Production Releases & Downloads

Pre-built, standalone release packages for **v1.0.0** are available on the
[GitHub Releases](https://github.com/Coderaryanyadav/FinAuditPro/releases/tag/v1.0.0)
page:

### macOS (Apple Silicon & Intel)

1. Download `FinAuditPro-1.0.0-macOS-arm64.dmg` (or Intel `x86_64`).
2. Double-click the DMG to open the installer.
3. Drag **FinAuditPro** into your **Applications** folder.
4. Launch FinAuditPro from Launchpad or Spotlight.

### Windows (64-bit)

1. Download `FinAuditPro-Setup-1.0.0-x64.exe` (or standalone portable `.zip`).
2. Run the installer wizard (or extract portable folder).
3. Launch **FinAuditPro** from your Start Menu or Desktop shortcut.

---

## Quickstart Guide (Running from Source)

### Prerequisites

- **Python**: Python 3.12 or higher (verified on Python 3.12, 3.13, and 3.14)
- **OS**: macOS (Apple Silicon arm64 / Intel), Linux x64, or Windows x64
- **Optional Tools**:
  - `tesseract` (for OCR on scanned images: `brew install tesseract` on macOS /
    `sudo apt-get install tesseract-ocr` on Linux)
  - [LM Studio](https://lmstudio.ai/) (optional for local AI assistant features
    on `http://localhost:1234`)

### Installation & Launch

```bash
# 1. Clone repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install package and optional extensions
pip install -e .[ocr,ai]

# 4. Launch Desktop Application
python -m finauditpro
```

---

## Documentation Directory

Comprehensive, authoritative documentation is organized in the [`docs/`](docs/)
directory:

- **[Installation Guide](docs/INSTALLATION.md)** — Detailed multi-platform setup
  instructions
- **[User Guide](docs/USER_GUIDE.md)** — Practitioner workflow, working paper
  sign-off & reporting
- **[System Architecture](docs/ARCHITECTURE.md)** — 4-layer Domain-Driven
  Architecture specification
- **[Security Policy & Architecture](docs/SECURITY.md)** — Threat model, key
  hierarchy & RBAC enforcement
- **[Audit Methodology](docs/AUDIT_METHODOLOGY.md)** — Standards on Auditing (SA
  230, SA 320, CARO 2020) support
- **[Accounting Controls](docs/ACCOUNTING_CONTROLS.md)** — Exact integer paise
  math & trial balance invariants
- **[Database Architecture](docs/DATABASE.md)** — SQLite WAL mode, schema design
  & migrations 1..9
- **[Encryption & Key Wrapping](docs/ENCRYPTION.md)** — Fernet DEK/KWK key
  hierarchy & fail-closed crypto
- **[Backup & Disaster Recovery](docs/BACKUP_RESTORE.md)** — WAL-safe atomic
  backup & restore validation
- **[QA & Testing Guide](docs/TESTING.md)** — 307-test automated QA architecture
  & test execution
- **[Compliance Scope & Disclaimer](docs/COMPLIANCE_SCOPE.md)** — Statutory
  disclaimer & DPDP Act 2023 posture
- **[Known Limitations](docs/LIMITATIONS.md)** — Single-workstation desktop
  boundaries
- **[Troubleshooting Runbook](docs/TROUBLESHOOTING.md)** — Operational
  diagnostic & resolution steps
- **[Release Notes](docs/RELEASE_NOTES.md)** — Official v1.0.0 release notes
- **[Maintainer Release Guide](RELEASE.md)** — Release engineering, build &
  distribution pipeline
- **[Changelog](CHANGELOG.md)** — Semantic version history

---

## Compliance Scope & Statutory Disclaimer

> **Important Statutory Notice**:\
> FinAuditPro provides software workflows, mathematical controls, and structured
> working paper management designed to assist audit teams performing statutory
> and internal audit procedures.
>
> FinAuditPro does **NOT** grant regulatory certification, issue audit opinions,
> or replace the professional skepticism and judgment of the auditor. The
> Engagement Partner and the audit firm remain exclusively responsible for
> evidence sufficiency, documentation completeness, and the final audit opinion
> rendered in compliance with applicable auditing standards and regulatory
> requirements.

---

## License & Authors

FinAuditPro is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for
details.

<div align="center">
  <sub>Built for Indian Statutory Audit Practice by <b>Aryan Yadav</b>, <b>Jeet Shah</b>, and <b>Hitansh Jasani</b></sub>
</div>
