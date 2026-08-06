# Changelog

## [2.4.0] - 2026-08-03

### Added

- **Repository Reorganization**: Standardized enterprise GitHub directory layout
  (`api/`, `assets/`, `docs/`, `scripts/`, `src/`, `tests/`).
- **RFC 7519 JTI Claims**: Added cryptographic unique `jti` claim to all access
  tokens to eliminate JWT revocation collisions across sessions.
- **Statutory GST Rate Slabs**: Expanded `GSTMismatchRule` valid rates to
  include Indian statutory GST slabs (`0.0%`, `0.1%`, `0.25%`, `1.5%`, `3.0%`,
  `5.0%`, `12.0%`, `18.0%`, `28.0%`).
- **Automatic Admin Provisioning**: Integrated auto-bootstrapping of initial
  default admin credentials (`admin@finauditpro.com` / `Admin@123`) on clean
  database launch.
- **UI Empty State Polish**: Added graceful empty state handling for client
  selectors, risk charts, and time-aware macOS header greetings.

### Security & Hardening

- Hardened API CORS middleware to prevent wildcard origin disallowance when
  `allow_credentials=True`.
- Enforced process-wide caching of installation cryptography keys
  (`.jwt_secret`, `.crypto_key`, `.crypto_salt`).
- Achieved 100% automated test suite pass rate (78 / 78 passing).

## [1.0.0] - 2026-07-21

### Added

- Pure Database-Outward Architecture for PySide6 UI.
- Real-time SQL aggregations for Executive Dashboard KPIs.
- Local Ollama AI RAG integration (`llama3`).
- PBKDF2 cryptographic password hashing and RBAC permission enforcement.
- Automated DDL schema migrator engine.
- Multi-engine OCR document parsing & FAISS vector search indexing.
