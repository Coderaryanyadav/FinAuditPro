# FinAuditPro — Documentation Index

Welcome to the FinAuditPro documentation. FinAuditPro is an offline-first desktop audit operating system designed specifically for Indian statutory audit practice.

---

## 📚 Master Documentation Map

```text
docs/
├── README.md                          # Master documentation index and sitemap
├── installation.md                    # Installation and launch instructions
├── design.md                          # UI/UX design tokens and component specification
├── decisions.md                       # Architecture Decision Records (ADRs 001..005)
├── roadmap.md                         # Completed milestones and product roadmap
│
├── architecture/
│   ├── overview.md                    # 4-layer architecture, invariants & data flows
│   └── database.md                    # SQLite WAL schema, tables & migrations 1..9
│
├── features/
│   ├── engagements.md                 # Firm, client & multi-year engagement management
│   ├── documents.md                   # Safe document ingestion, OCR & SQLite FTS5 search
│   ├── financial-data.md              # TB/GL import & deterministic analytics engine
│   ├── working-papers.md              # Working paper lifecycle, review notes & sign-off
│   ├── reporting.md                   # ReportLab PDF generation & formula-escaped XLSX export
│   ├── archival.md                    # SQC 1 sealed archives & SA 510 roll-forward tie-out
│   └── ai.md                          # Air-gapped local AI copilot & LM Studio RAG
│
├── security/
│   ├── security-model.md              # Fail-closed RBAC, encryption & isolation
│   └── threat-model.md                # Threat vectors, mitigations & defense-in-depth
│
├── development/
│   ├── setup.md                       # Environment setup, dependencies & tooling
│   └── testing.md                     # Pytest suite, static typing & architecture guards
│
└── operations/
    ├── configuration.md               # Environment variables & settings.json reference
    ├── troubleshooting.md             # Common error resolution & diagnostic remediation
    └── backup-restore.md              # Encrypted backup packaging & safe atomic restore
```

---

## 🚀 Quick Links
- **[Getting Started & Installation](installation.md)**
- **[System Architecture](architecture/overview.md)**
- **[Database Schema & Migrations](architecture/database.md)**
- **[Security Architecture & Model](security/security-model.md)**
- **[Architecture Decision Records](decisions.md)**
- **[Developer Setup](development/setup.md)**
- **[Testing Strategy](development/testing.md)**
- **[UI Design System](design.md)**
- **[Release Notes / Changelog](../CHANGELOG.md)**
- **[Canonical Security Policy](../SECURITY.md)**
