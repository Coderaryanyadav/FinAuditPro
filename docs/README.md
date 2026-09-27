# FinAuditPro Documentation Hub

Welcome to the canonical documentation for **FinAuditPro**, the offline-first statutory audit operating system for Indian Chartered Accountants.

---

## Documentation Map

### [Architecture](./architecture/)
- [`ARCHITECTURE.md`](./architecture/ARCHITECTURE.md) — 4-layer Domain-Driven Design (DDD) specification and domain graph.
- [`DOMAIN_MODEL.md`](./architecture/DOMAIN_MODEL.md) — Domain entities, aggregates, and integer-paise math.
- [`DATABASE.md`](./architecture/DATABASE.md) — SQLite WAL mode configuration, concurrency, and trigger immutability.
- [`SECURITY.md`](./architecture/SECURITY.md) — Cryptographic architecture, AES-128, PBKDF2, and threat model.

### [Product Specification](./product/)
- [`PRODUCT_REQUIREMENTS.md`](./product/PRODUCT_REQUIREMENTS.md) — Product vision, functional requirements, and RBAC matrix.
- [`USER_WORKFLOW.md`](./product/USER_WORKFLOW.md) — User personas and end-to-end statutory audit journey.

### [Audit Methodology](./audit/)
- [`AUDIT_WORKFLOW.md`](./audit/AUDIT_WORKFLOW.md) — ICAI Standards on Auditing (SA 200–SA 700), CARO 2020, and Form 3CD.
- [`RISK_MODEL.md`](./audit/RISK_MODEL.md) — Audit risk formula, assertion-level mapping, and Materiality Engine (SA 320).
- [`WORKING_PAPERS.md`](./audit/WORKING_PAPERS.md) — Electronic working papers (SA 230), sampling algorithms (SA 530), and review notes.
- [`FINALISATION.md`](./audit/FINALISATION.md) — Finalisation gate checks, misstatement evaluation (SA 450), and SQC 1 archival.

### [Engineering & Operations](./engineering/)
- [`DEVELOPMENT.md`](./engineering/DEVELOPMENT.md) — Developer environment setup, coding standards, and project layout.
- [`TESTING.md`](./engineering/TESTING.md) — Pytest suite execution, coverage, and E2E validation.
- [`RELEASE.md`](./engineering/RELEASE.md) — Desktop binary packaging (macOS DMG, Windows EXE, Linux) and verification.

### [Artificial Intelligence](./ai/)
- [`AI_ARCHITECTURE.md`](./ai/AI_ARCHITECTURE.md) — Local LM Studio AI integration with zero cloud egress.
- [`AI_SAFETY.md`](./ai/AI_SAFETY.md) — Deterministic math guardrails and AST prompt injection defenses.

### [UI/UX Design](./ui/)
- [`DESIGN_SYSTEM.md`](./ui/DESIGN_SYSTEM.md) — Dark mode color palette tokens, typography, and table styles.
- [`UI_WORKFLOW.md`](./ui/UI_WORKFLOW.md) — Information architecture, sidebar navigation, and keyboard shortcuts.

### [Roadmap & Decisions](./roadmap/)
- [`MASTER_ROADMAP.md`](./roadmap/MASTER_ROADMAP.md) — Development milestones and Architecture Decision Records (ADRs).
- [`CURRENT_PHASE.md`](./roadmap/CURRENT_PHASE.md) — Production Release v1.2.0 status and feature backlog.

---

## Root Documentation
- [README.md](../README.md) — Main repository landing page and quick start guide.
- [SECURITY.md](../SECURITY.md) — Vulnerability reporting and security policy.
- [CHANGELOG.md](../CHANGELOG.md) — Version release history.
