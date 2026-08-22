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
│   └── system-architecture.md         # 4-layer DDD architecture, invariants & migrations 1..9
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
│   └── security-guide.md              # Fail-closed RBAC, encryption & threat mitigations
│
├── development/
│   └── developer-guide.md             # Developer environment setup, testing & AST guards
│
└── operations/
    ├── operations-guide.md            # Environment configuration & diagnostics runbook
    └── backup-restore.md              # Encrypted backup packaging & safe atomic restore
```

---

## 🚀 Quick Links
- **[Getting Started & Installation](installation.md)**
- **[System & Database Architecture](architecture/system-architecture.md)**
- **[Security Architecture & Threat Defense](security/security-guide.md)**
- **[Architecture Decision Records](decisions.md)**
- **[Developer Onboarding & QA Guide](development/developer-guide.md)**
- **[Operations & Troubleshooting Guide](operations/operations-guide.md)**
- **[UI Design System](design.md)**
- **[Release Notes / Changelog](../CHANGELOG.md)**
- **[Canonical Security Policy](../SECURITY.md)**
