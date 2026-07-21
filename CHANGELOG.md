# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-21

### Added
- **Core Desktop Application**: Launched the initial version of FinAuditPro using PySide6.
- **Offline Intelligence**: Integrated FAISS vector store and local LLM embeddings pipeline.
- **OCR Engine**: Added support for local text extraction from images and PDFs using Tesseract/PaddleOCR.
- **Rule Engine**: Hardcoded 12 essential financial mismatch and risk detection rules.
- **Analytics Dashboards**: Added real-time CEO and Audit Partner dashboards with dynamic SQLite querying.
- **Security & Privacy**:
  - Implemented 100% offline-first architecture.
  - Added Role-Based Access Control (RBAC).
  - Implemented SQLite WAL mode and concurrent worker threads.
  - Added PBKDF2-HMAC-SHA256 password hashing.
  - Added robust AES-256 Fernet data encryption with fallback stream cipher.
  - Added immutable cryptographically chained audit logging for all critical UI actions.
- **Reporting Engine**: Added the ability to export ICAI-Standard Audit Packs as PDF.
- **Working Papers Module**: Built a UI to view AI findings alongside extracted financial evidence.

### Fixed
- **Architecture**: Enforced strict Clean Architecture between UI, Services, and Data Repositories.
- **Thread Safety**: Applied `threading.Lock` to all core singletons (`SecurityManager`, `WorkflowManager`).
- **Database Locking**: Solved `sqlite3.OperationalError` bottlenecks during background OCR tasks using thread-scoped sessions and a 30-second timeout.
- **Memory Leaks**: Migrated `get_session()` to a `@contextmanager` to ensure deterministic database session closure.

### Security
- Replaced custom XOR fallback encryption with a secure hash-based stream cipher.
- Prevented potential UI bypasses by injecting RBAC permission checks directly into view controllers.
