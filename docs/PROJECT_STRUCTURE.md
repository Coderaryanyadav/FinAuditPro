# Project Structure

FinAuditPro follows a strict **Clean Architecture** approach. Understanding this layout is crucial for contributing.

```text
FinAuditPro/
├── .github/                  # GitHub Actions CI/CD workflows and issue templates
├── assets/                   # Static branding images, icons, and banners
├── docs/                     # End-user and deployment documentation
├── HTML/                     # (Legacy) Temporary assets and web fallback templates
├── scripts/                  # Native OS packager scripts (NSIS, DMG, AppImage)
├── src/                      # Primary Python Source Code
│   ├── main.py               # Application Entry Point & Global Config
│   ├── ai/                   # (Deprecated) Core AI integrations
│   ├── analytics/            # Real-time dashboard metric aggregation
│   ├── core/                 # Shared domain entities
│   ├── database/             # SQLAlchemy ORM definitions and Session management
│   ├── deployment/           # Release utilities (Crash Reporter, Loggers, Migrations)
│   ├── document_intelligence/# OCR Pipelines and FAISS Vector Embeddings
│   ├── reporting/            # ICAI PDF and Excel exporters
│   ├── rule_engine/          # Deterministic financial mismatch detectors
│   ├── security/             # AES-256 Crypto, RBAC, and Immutable Audit Trails
│   ├── services/             # Application Business Logic
│   ├── ui/                   # PySide6 Presentation Layer
│   └── workflow/             # State-machine for Audit Engagement progress
└── tests/                    # Comprehensive unit and integration test suite
```
