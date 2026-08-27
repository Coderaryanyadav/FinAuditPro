# Changelog

All notable changes to **FinAuditPro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-08-27

### Changed
- **Package Assets Relocation**: Moved application static assets from root `assets/` to `src/finauditpro/assets/` using standard Python `importlib.resources` for robust asset resolution across source and standalone PyInstaller bundles.
- **Canonical OS Data Path Decoupling**: Fully decoupled runtime database to standard OS directories (`~/Library/Application Support/FinAuditPro/db/` on macOS, `%APPDATA%\FinAuditPro\db\` on Windows) and eliminated root database creation.
- **Packaging Pipeline Streamlining**: Updated `finauditpro.spec`, `build_macos.py`, and Windows packaging scripts for automated asset and icon packaging into native `.app` and standalone DMG bundles.
- **Architecture & Strict Typing Enhancements**: Resolved UI layer isolation boundaries, added type safety across substantive domain engines, and expanded test suite to 161 passing tests.

---

## [1.1.0] - 2026-08-26

### Added
- **Vector Branding & Custom UI Controls**: Added custom combo box delegate and standardized navigation typography.
- **Extended Forensic Verifications**: 15-stage 1,000-point forensic runner for substantive analytics and statutory validations.

---

## [1.0.0] - 2026-08-26

### Added
- **Persistent User Authentication**: PBKDF2-HMAC-SHA256 password hashing (100,000 iterations, 16-byte cryptographic salt, constant-time `secrets.compare_digest` verification) stored in SQLite `users` table.
- **Mandatory First-Login Password Change**: Automatic `ChangePasswordDialog` forcing default `Admin@123` replacement with password complexity enforcement (min. 8 characters, letters, numbers/symbols).
- **Segregation of Duties (SoD) Enforcement**: Statutory rule in `WorkingPaperService` preventing preparers from performing final sign-offs on their own working papers.
- **Deterministic Vector Alignment**: Chronological and deterministic `(created_at ASC, id ASC)` ordering across both FAISS embedding chunks and SQLite retrieval.
- **Approved Report Artifact Ledger**: Approved report PDFs recorded into `report_artifacts` with SHA-256 digests.
- **Clean UI & Universal Dropdown Styling**: Universal `QComboBox` and `QAbstractItemView` styling eliminating unstyled system grey-pills on macOS; clean text labels across all navigation items and buttons.
- **138 Passing Automated Tests**: Comprehensive test suite covering auth, SoD, RAG, materiality, analytics, persistence, and scale performance.

---

## [0.1.0] - 2026-08-21

### Added
- **Milestone 1: Core Foundation & Persistence**: Firm/Client/Engagement models, fail-closed RBAC, hash-chained audit event logging.
- **Milestone 2: Document Management, Security, OCR & FTS5**: PyMuPDF + Tesseract OCR extraction, SQLite FTS5 search index, document evidence linking.
- **Milestone 3: Financial Data Import & Analytics**: Multi-file Trial Balance, General Ledger, and Bank Statement import with deterministic Benford's Law, duplicate payment, and outlier analytics.
- **Milestone 4: Audit Planning & Execution Core**: SA 320 materiality calculation engine, risk assessment register, structured audit procedures, and unified findings lifecycle.
- **Milestone 5: Local AI Subsystem**: Provider-agnostic LLM client, engagement-partitioned FAISS RAG, and AI-assisted findings with RAG citations.
- **Milestone 6: Working Papers & Sign-Off**: Working paper lifecycle, maker-checker sign-offs, and open-notes sign-off blocking control.
- **Milestone 7: Reporting & Export**: ReportLab PDF generator with draft watermarks, OpenPyXL XLSX exporter with formula injection escaping.
- **Milestone 8: Hardening & Performance**: Backup/restore Fernet encryption, SQLite append-only triggers, 10,000 GL row scale benchmark.
- **Milestone 9: Engagement Archival**: Readiness check, deterministic SHA-256 seal manifest, retention rules (SA 230), and Partner reopen workflow.
- **Milestone 10: Multi-Year Roll-Forward**: Next FY engagement roll-forward, SA 510 opening balance tie-out engine in paise, carried findings AI provenance.
- **Milestone 11: Packaging & Distribution**: App data bootstrap, launch-time environment self-check, PyInstaller spec, and build/signing scripts.
- **Product Design Transformation**: Neutral-first design tokens, categorized sidebar navigation, tabular financial figures, and visual calm.
