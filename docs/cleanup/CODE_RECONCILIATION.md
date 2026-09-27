# FinAuditPro — File-Level Code Reconciliation Matrix (Phase 3)

| Previous File (`18c034c`) | Current Status | Replacement in Current Architecture | Functionality Lost? | Action | Rationale |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `application/services/client_workspace_service.py` | Removed | `application/services/engagement_service.py` | No | **KEEP CURRENT** | Functionality subsumed into engagement-centric 3-tier architecture with strict tenant isolation. |
| `application/services/compliance_workflow_service.py` | Removed | `application/services/methodology_service.py` & `domain/methodology_catalog.py` | No | **KEEP CURRENT** | Replaced by pure domain methodology catalog and dedicated CARO/3CD engines. |
| `application/services/guided_workflow_service.py` | Removed | `domain/finalization_gate_engine.py` & `domain/engagement_state_machine.py` | No | **KEEP CURRENT** | Hardcoded stepper replaced by formal mathematical completion gates. |
| `application/services/inbox_service.py` | Removed | `application/services/pbc_and_query_service.py` & `document_service.py` | No | **KEEP CURRENT** | Generic inbox replaced by statutory PBC (Provided by Client) & Audit Query lifecycle. |
| `application/services/practice_dashboard_service.py` | Removed | `application/services/engagement_service.py` & `financial_service.py` | No | **KEEP CURRENT** | Consolidated into engagement dashboard with real-time trial balance balancing and review note KPIs. |
| `application/services/unified_reconciliation_service.py` | Removed | `domain/bank_reconciliation_engine.py` & `domain/three_way_match_engine.py` | No | **KEEP CURRENT** | Monolithic service decomposed into dedicated deterministic math engines. |
| `application/services/unified_search_service.py` | Removed | `document_service.py` (SQLite FTS5) & `command_palette_dialog.py` | No | **KEEP CURRENT** | Python in-memory search replaced by high-performance native SQLite FTS5 index. |
| `application/services/work_center_service.py` | Removed | `working_paper_service.py` & `audit_planning_service.py` | No | **KEEP CURRENT** | Ad-hoc task list replaced by formal SA 230 working paper lifecycle and procedure programs. |
| `domain/compliance_workflow_engine.py` | Removed | `domain/methodology_statutory_catalog.py` & `risk_procedure_engine.py` | No | **KEEP CURRENT** | Upgraded with complete ICAI SA 200–700 taxonomy and CARO 2020 21 clauses. |
| `domain/document_entities.py` | Removed | `domain/audit_matrix_entities.py` & `evidence_state_machine.py` | No | **KEEP CURRENT** | Enhanced with SHA-256 cryptographic provenance and bidirectional working paper links. |
| `domain/prompt_engine.py` | Removed | `application/ai/copilot_prompt_engine.py` & `audit_context_builder.py` | No | **KEEP CURRENT** | Upgraded with AST sanitization, dual-fencing, and PII masking. |
| `domain/unified_search_engine.py` | Removed | `infrastructure/persistence/database.py` (FTS5 virtual tables) | No | **KEEP CURRENT** | SQLite FTS5 virtual tables provide superior indexing and lower memory overhead. |
| `infrastructure/documents/smart_document_intelligence.py` | Removed | `infrastructure/documents/document_pipeline.py` & `evidence_service.py` | No | **KEEP CURRENT** | Consolidated into document pipeline with streaming SHA-256 hashing. |
| `infrastructure/persistence/migration_sqls_g.py` | Removed | `infrastructure/persistence/migration_list.py` | No | **KEEP CURRENT** | Index creation consolidated into main linear migrations. |
| `infrastructure/persistence/work_models.py` | Removed | `infrastructure/persistence/working_paper_models.py` | No | **KEEP CURRENT** | Work task models unified into formal working paper entity tables. |
| `ui/components/context_bar.py`, `header.py`, `sidebar.py` | Removed | `ui/main_window.py` | No | **KEEP CURRENT** | Unified into single cohesive window shell, eliminating widget layout flicker. |
| `ui/dialogs/confirm_dialog.py` | Removed | `PyQt6.QtWidgets.QMessageBox` & `close_wizard_dialog.py` | No | **KEEP CURRENT** | Standardized on native Qt message dialogs for platform compliance. |
| `ui/human_formatters.py` | Removed | `domain/value_objects.py` & `infrastructure/financial/currency_parser.py` | No | **KEEP CURRENT** | Currency formatting unified in `Money.format_inr()` and domain value objects. |
| `ui/views/client_workspace_view.py` | Removed | `ui/main_window.py` & `ui/views/dashboard_view.py` | No | **KEEP CURRENT** | Multi-client workspace selector embedded in top toolbar. |
| `ui/views/guided_workflow_view.py` | Removed | `ui/views/dashboard_view.py` (Completion Stepper) | No | **KEEP CURRENT** | Replaced by live engagement completion gate widget. |
| `ui/views/inbox_view.py` | Removed | `ui/views/document_view.py` & `ui/views/pbc_view.py` | No | **KEEP CURRENT** | Replaced by dedicated Document Repository and PBC Request Center. |
| `ui/views/unified_reconciliation_view.py` | Removed | `ui/views/financial_view.py` & `ui/views/audit_adjustment_view.py` | No | **KEEP CURRENT** | Integrated into financial data ingestion and adjustments view. |
| `ui/views/work_center_view.py` | Removed | `ui/views/working_paper_view.py` | No | **KEEP CURRENT** | Replaced by 3-pane Working Paper Workbench. |
| `ui/widgets/evidence_inspector_panel.py` | Removed | `ui/views/working_paper_view.py` (Right Pane) | No | **KEEP CURRENT** | Integrated directly into right pane of working paper workbench. |
