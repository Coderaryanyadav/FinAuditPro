# Changelog

All notable changes to **FinAuditPro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- GitHub CI/CD fast matrix pipeline (`.github/workflows/ci.yml`) supporting Python 3.12, 3.13, and 3.14 across macOS and Ubuntu.
- Automated dependency scanning with Dependabot (`.github/dependabot.yml`).
- Statutory maintenance scripts for SQLite WAL vacuuming, archive hash verification, and retention policy scanning (`scripts/maintenance/`).

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
