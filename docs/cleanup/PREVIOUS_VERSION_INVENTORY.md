# FinAuditPro — Previous Version Inventory (Commit `18c034c`)

> **Repository State:** Git Commit `18c034ccadb9a0008745a398725a7b8454d41008`  
> **Total Source Python Files:** 303 files  
> **Evaluation Date:** 2026-09-27  

---

## 1. Previous Architecture Overview
The previous version (`18c034c`) used a hybrid multi-tab enterprise shell with flat, loosely coupled service modules:

### 1.1 Disjointed Flat Services
- `client_workspace_service.py` (205 lines): Managed standalone client views without full engagement binding.
- `practice_dashboard_service.py` (311 lines): Aggregated cross-firm metrics without drill-down engagement context.
- `work_center_service.py` (373 lines): Generic task manager decoupled from formal SA 230 working papers.
- `inbox_service.py` (202 lines): Practice document intake workflow decoupled from PBC queries.
- `unified_reconciliation_service.py` (323 lines): Monolithic reconciliation handler mixing GST, bank, and ledger math.
- `unified_search_service.py` (321 lines): In-memory linear scan search engine duplicating SQLite FTS5.
- `guided_workflow_service.py` (269 lines): Hardcoded 4-step stepper decoupled from domain completion checklist invariants.

### 1.2 Fragmented UI Components
- 15 flat navigation views: `client_workspace_view.py`, `inbox_view.py`, `work_center_view.py`, `guided_workflow_view.py`, `unified_reconciliation_view.py`, `compliance_view.py`, `dashboard_view.py`, `working_paper_view.py`.
- Multiple uncoordinated sub-headers: `context_bar.py`, `header.py`, `sidebar.py`.
- Right-pane popup widgets: `evidence_inspector_panel.py`.

### 1.3 Previous Test Structure
- 100+ tests including duplicate test runners (`test_phase13_security_hardening.py`, `test_phase14_performance.py`, `test_phase15_ux_polish.py`, `test_command_center_gui.py`).
