# FinAuditPro — Duplicate Code & Redundancy Analysis (Phase 7)

## 1. Resolved Duplication in Current Architecture
1. **Search Subsystems:** Eliminated duplicate Python in-memory search (`unified_search_service.py`) in favor of native SQLite FTS5 virtual tables.
2. **Currency Parsers:** Consolidated disparate decimal/string formatters into `Money.format_inr()` and `currency_parser.py`.
3. **Working Paper Task Models:** Eliminated duplicate generic `work_tasks` in favor of formal SA 230 `working_papers` aggregate.
4. **AI Prompt Construction:** Consolidated ad-hoc prompt templates into `copilot_prompt_engine.py` and `audit_context_builder.py`.
5. **Database Connection String Parsing:** Cleaned up duplicate URL string construction in `database.py`.

## 2. Canonical Single Responsibilities
- **Entity State Transitions:** Handled exclusively by pure domain state machines (`engagement_state_machine.py`, `evidence_state_machine.py`).
- **Money Arithmetic:** Handled exclusively by `domain/value_objects.py`.
- **Database Access:** Handled exclusively via repositories; direct UI database access is 100% prohibited.
