# FinAuditPro — Architecture Decision Records (ADRs)

This document captures the key architectural decisions, rationale, and compliance guarantees governing FinAuditPro.

---

## ADR-001: Offline-First Architecture & Single-Tenant Local SQLite WAL Database
* **Status**: Accepted
* **Context**: Statutory financial audit data in Indian CA practice is subject to strict confidentiality regulations. Cloud-hosted multi-tenant databases pose severe data leakage and compliance risks.
* **Decision**: All application state, evidence links, working papers, and audit trails are persisted locally on the auditor's workstation using SQLite 3 operating in Write-Ahead Logging (`WAL`) mode with multi-engagement single-tenant isolation (`engagement_id` scoped queries).
* **Consequences**: Zero outbound network dependency, low-latency transactional performance, robust atomic backups, and complete client confidentiality.

---

## ADR-002: Offline-First Local-Only AI via LM Studio (Zero Outbound Egress)
* **Status**: Accepted
* **Context**: Cloud LLM providers (e.g. external APIs) violate audit confidentiality if client trial balances or documents are transmitted over the public internet.
* **Decision**: All generative audit assistance, document chunk summarization, and query reasoning run strictly against local OpenAI-compatible endpoints provided by LM Studio (`http://localhost:1234`) running open-weights models (`deepseek-r1-distill-qwen-14b`, `nomic-embed-text`). If the local AI server is offline, FinAuditPro degrades gracefully to rule-based execution without interruption.
* **Consequences**: Strict privacy and confidentiality preservation. AI outputs are advisory and marked `[AI Advisory]` with mandatory human auditor review.

---

## ADR-003: Pure Domain Layer & 4-Layer Dependency Boundary Enforcement via AST Tests
* **Status**: Accepted
* **Context**: Tight coupling between presentation (PySide6), ORM models (SQLAlchemy), and statutory calculation logic leads to brittle code and difficult verification.
* **Decision**: Enforce a strict 4-layer Domain-Driven Architecture (`domain/` $\rightarrow$ `application/` $\rightarrow$ `infrastructure/` $\rightarrow$ `ui/`). The pure domain core contains zero external framework dependencies and is verified via automated AST boundary tests in `tests/test_architecture.py`.
* **Consequences**: Highly testable business logic (SA 320 materiality, Benford's Law, formula injection escaping) that runs deterministically without mocking databases or UI widgets.

---

## ADR-004: Exact Integer-Paise Precision for Financial Calculations
* **Status**: Accepted
* **Context**: IEEE 754 binary floating-point representation (`float`) introduces binary rounding errors (e.g. `0.1 + 0.2 != 0.3`), which is unacceptable in statutory audit schedules and balance sheet tie-outs.
* **Decision**: All financial figures, trial balance balances, ledger entries, and materiality thresholds are stored and calculated in **exact integer paise** (1 INR = 100 paise).
* **Consequences**: Eliminates floating-point drift, ensuring mathematical certainty in SA 510 opening balance tie-outs and SA 320 materiality benchmarks.

---

## ADR-005: SQLite FTS5 Porter Tokenization for Document Evidence Search
* **Status**: Accepted
* **Context**: Auditors require instant keyword search across thousands of pages of PDF evidence, invoices, and bank statements without running heavy external search services.
* **Decision**: Leverage SQLite's built-in `FTS5` full-text search module with porter stemmer tokenization, storing page snippets with highlighted match offsets.
* **Consequences**: Ultra-fast full-text search integrated directly into the embedded transactional database with zero additional daemon overhead.

---

## Historical Architecture Review & Remediation Log
* **Date**: 2026-08-21
* **Scope**: Full forensic audit of the entire codebase resolving type errors, AST line limits ($\le 400$ lines), maker-checker sign-off blocking, and formula injection sanitization across all tabular exports. All identified items were remediated and verified with 130 passing unit/integration tests.
