# Phase 18 Type Audit & Error Classification

**Date:** 2026-09-21  
**Total MyPy Errors:** 18  
**Scope:** `src/finauditpro/`

---

## 1. Error Classification Matrix

| Category | Count | Severity | Files | Action |
| :--- | :---: | :--- | :--- | :--- |
| **A. Missing Type Annotations** | 0 | Low | - | Keep monitoring strict mode |
| **B. Incorrect Return Types** | 0 | Medium | - | Fully verified |
| **C. Optional/None Handling** | 0 | High | - | Verified across repositories |
| **D. Incorrect Argument Types** | 0 | Medium | - | Verified |
| **E. SQLAlchemy / Model Typing** | 8 | High | `guided_workflow_service.py`, `practice_dashboard_service.py` | Correct model import locations and table references (`MaterialityCalculationModel`, `AuditReportPackageModel`, `ArchivalPackageModel`, `AuditFindingModel`, `AuditRiskModel`, `GSTEntryModel`) |
| **F. Pydantic / Enum Typing** | 2 | Medium | `smart_document_intelligence.py` | Add explicit type annotation `final_cat: DocumentCategoryEnum` to prevent improper literal narrowing |
| **G. Repository / Service Boundaries** | 1 | High | `document_service.py` | Fix import / re-export of `DocumentStructuredMetadata` from `domain.document_entities` |
| **M. Actual Implementation Bugs** | 7 | High | `practice_dashboard_service.py`, `guided_workflow_service.py` | Fix incorrect model attribute names (`AuditEventModel.action` vs `event_type`, `actor` vs `user_id`, `details` vs `details_json`, `SignOffRecordModel.role` vs `signoff_type`) |

---

## 2. Detailed Error Inventory

### File: `src/finauditpro/infrastructure/documents/smart_document_intelligence.py`
- **Line 156:** `Incompatible types in assignment (expression has type "DocumentCategoryEnum", variable has type "Literal[...]")`
  - *Root Cause:* Variable inferred as narrowed Literal union instead of full `DocumentCategoryEnum`.
  - *Fix:* Annotate `final_cat: DocumentCategoryEnum`.
- **Line 160:** `Non-overlapping equality check ... right operand type: "Literal[DocumentCategoryEnum.GENERAL]"`
  - *Root Cause:* Cascaded from Line 156 narrowing.
  - *Fix:* Resolved when `final_cat` is typed as `DocumentCategoryEnum`.

### File: `src/finauditpro/application/services/guided_workflow_service.py`
- **Line 103:** `Module "finauditpro.infrastructure.persistence.models" has no attribute "MaterialityCalculationModel"`
  - *Root Cause:* Model resides in `core_audit_engine_models` or `models.py`.
  - *Fix:* Import from correct module.
- **Line 173:** `Module "finauditpro.infrastructure.persistence.report_models" has no attribute "AuditReportPackageModel"`
  - *Root Cause:* Model is named `ReportPackageModel` or in `audit_report_models`.
  - *Fix:* Update import.
- **Line 195:** `"type[SignOffRecordModel]" has no attribute "signoff_type"`
  - *Root Cause:* Attribute is named `signoff_level` or `role`.
  - *Fix:* Update column query.
- **Line 205:** `Module "finauditpro.infrastructure.persistence.archival_models" has no attribute "ArchivalRecordModel"`
  - *Root Cause:* Model named `ArchivePackageModel`.
  - *Fix:* Update import and model query.

### File: `src/finauditpro/application/services/practice_dashboard_service.py`
- **Lines 138, 214:** `Module "core_audit_engine_models" has no attribute "FindingModel" / "RiskModel"`
  - *Root Cause:* Models named `AuditFindingModel` and `AuditRiskModel`.
  - *Fix:* Correct model class imports.
- **Lines 267, 268, 270, 271, 272:** `AuditEventModel` attributes (`event_type`, `details_json`, `user_id`, `entity_type`, `entity_id`)
  - *Root Cause:* Legacy column names queried instead of actual `AuditEventModel` columns (`action`, `details`, `actor`, `engagement_id`).
  - *Fix:* Update attribute access to match real ORM schema.
- **Line 282:** `Module "models" has no attribute "GSTEntryModel"`
  - *Root Cause:* Model defined in `compliance_models.py`.
  - *Fix:* Update import to `finauditpro.infrastructure.persistence.compliance_models`.

### File: `src/finauditpro/application/services/document_service.py`
- **Line 248:** `Module "finauditpro.domain.entities" has no attribute "DocumentStructuredMetadata"`
  - *Root Cause:* `DocumentStructuredMetadata` is in `finauditpro.domain.document_entities`.
  - *Fix:* Re-export in `finauditpro.domain.entities` and import directly.
