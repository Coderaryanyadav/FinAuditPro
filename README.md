# FinAuditPro — Professional Statutory Audit Operating System (v1.2.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Tests: 130+ Passed](https://img.shields.io/badge/tests-130%2B%20passed-brightgreen.svg)](docs/engineering/TESTING.md)
[![Privacy: 100% Offline](https://img.shields.io/badge/privacy-100%25%20offline%20(zero%20egress)-success.svg)](docs/architecture/SECURITY.md)
[![ICAI SAs & CARO 2020](https://img.shields.io/badge/compliance-ICAI%20SAs%20%7C%20CARO%202020%20%7C%20Form%203CD-blueviolet.svg)](docs/audit/AUDIT_WORKFLOW.md)

**FinAuditPro** is an offline-first, professional desktop operating system engineered specifically for Indian Chartered Accountants (CAs), audit managers, article assistants, and engagement partners. It provides a deterministic, mathematically rigorous platform for statutory audits under the Companies Act 2013, Indian Standards on Auditing (SA 200–SA 700), CARO 2020, and Tax Audit Form 3CD.

---

## Key Highlights & Architectural Guarantees

- **100% Offline & Local Privacy:** Zero cloud telemetry or external network calls. All financial analytics and AI co-pilot queries execute locally on the practitioner's workstation.
- **Deterministic Integer-Paise Math:** Storage and math in exact integer paise (1 INR = 100 paise) preventing floating-point rounding errors.
- **4-Layer Domain-Driven Design (DDD):** Pure Python domain layer decoupled from presentation (PyQt6) and persistence (SQLite).
- **SQLite WAL with Immutability Triggers:** High-performance ACID storage with database-level triggers enforcing immutable audit trails.
- **Local AI Copilot via LM Studio:** On-device RAG assistant querying statutory standards with prompt injection defenses.
- **Electronic Working Papers (SA 230):** Full maker-checker review workflows, threaded notes, and SQC 1 10-year archival sealing.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run test suite
pytest

# Launch the desktop application
python3 src/main.py
```

---

## Authoritative Documentation Map

All project documentation is structured in the [`docs/`](./docs/README.md) directory:

| Section | Focus Area | Canonical Documents |
| :--- | :--- | :--- |
| **Architecture** | System Design & Invariants | [`ARCHITECTURE.md`](./docs/architecture/ARCHITECTURE.md), [`DOMAIN_MODEL.md`](./docs/architecture/DOMAIN_MODEL.md), [`DATABASE.md`](./docs/architecture/DATABASE.md), [`SECURITY.md`](./docs/architecture/SECURITY.md) |
| **Product** | PRD & Workflows | [`PRODUCT_REQUIREMENTS.md`](./docs/product/PRODUCT_REQUIREMENTS.md), [`USER_WORKFLOW.md`](./docs/product/USER_WORKFLOW.md) |
| **Audit** | SAs, CARO & Workpapers | [`AUDIT_WORKFLOW.md`](./docs/audit/AUDIT_WORKFLOW.md), [`RISK_MODEL.md`](./docs/audit/RISK_MODEL.md), [`WORKING_PAPERS.md`](./docs/audit/WORKING_PAPERS.md), [`FINALISATION.md`](./docs/audit/FINALISATION.md) |
| **Engineering** | Dev Setup, Tests & Packaging | [`DEVELOPMENT.md`](./docs/engineering/DEVELOPMENT.md), [`TESTING.md`](./docs/engineering/TESTING.md), [`RELEASE.md`](./docs/engineering/RELEASE.md) |
| **AI** | Local Copilot & Safety | [`AI_ARCHITECTURE.md`](./docs/ai/AI_ARCHITECTURE.md), [`AI_SAFETY.md`](./docs/ai/AI_SAFETY.md) |
| **UI/UX** | Design System & Shortcuts | [`DESIGN_SYSTEM.md`](./docs/ui/DESIGN_SYSTEM.md), [`UI_WORKFLOW.md`](./docs/ui/UI_WORKFLOW.md) |
| **Roadmap** | Milestones & ADRs | [`MASTER_ROADMAP.md`](./docs/roadmap/MASTER_ROADMAP.md), [`CURRENT_PHASE.md`](./docs/roadmap/CURRENT_PHASE.md) |

For complete documentation details, visit the [**Documentation Hub**](./docs/README.md).

---

## License & Contributing
- **License:** [MIT License](LICENSE)
- **Security Policy:** [SECURITY.md](SECURITY.md)
- **Contributing Guidelines:** [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)
