# FinAuditPro — Developer Onboarding & Extension Guide

Welcome to the **FinAuditPro** core developer guide. This document outlines architectural principles, development patterns, and instructions for extending application features.

---

## 1. Architectural Philosophy

FinAuditPro follows a **Database-Outward, Layered Architecture**:

1. **Database Tier (`src/database/models.py`)**: 22 declarative SQLAlchemy ORM models forming the single source of truth.
2. **Repository Tier (`src/database/repositories/`)**: Encapsulates all query operations and session persistence.
3. **Service Tier (`src/services/`)**: Implements domain business logic, statutory validations, and workflow orchestration.
4. **Presentation Tier (`src/ui/`)**: PySide6 desktop views bound to services via signals and thread workers.

---

## 2. Environment Setup & Conventions

### Prerequisites
- Python 3.10 – 3.12
- Git
- Ollama (for offline LLM testing)

### Virtual Environment Initialization
```bash
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro
python -m venv .venv
# Activate
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

## 3. How to Add a Custom Statutory Audit Rule

Rules inherit from `BaseRule` in `src/rule_engine/base_rule.py`.

1. **Create the Rule Class**:
   ```python
   from typing import Dict, Any, Optional
   from .base_rule import BaseRule
   from .severity import RuleSeverity, RuleCategory
   from .rule_result import RuleResult

   class CustomTDSThresholdRule(BaseRule):
       def __init__(self):
           super().__init__(
               rule_id="TAX-003",
               rule_name="Section 194C TDS Threshold Exceeded",
               category=RuleCategory.INCOME_TAX,
               severity=RuleSeverity.HIGH,
               threshold=30000.0,
               accounting_standard="Income Tax Act Sec 194C",
               audit_standard="SA 250"
           )

       def evaluate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> RuleResult:
           tot_amt = data.get("total_amount") or 0.0
           passed = tot_amt <= self.threshold
           
           return RuleResult(
               rule_id=self.rule_id,
               rule_name=self.rule_name,
               category=self.category,
               severity=self.severity,
               passed=passed,
               risk_score=0.0 if passed else 75.0,
               description="Single payment exceeds Section 194C TDS limit of ₹30,000.",
               evidence=[f"Transaction Amount: ₹{tot_amt:,.2f}"],
               recommendation="Verify TDS deduction at 1% (Individual/HUF) or 2% (Company).",
               accounting_standard=self.accounting_standard,
               audit_standard=self.audit_standard
           )
   ```

2. **Register in RuleLoader**:
   In `src/rule_engine/rule_loader.py`:
   ```python
   @classmethod
   def load_all_rules(cls) -> RuleRegistry:
       registry = RuleRegistry()
       # ... existing rules ...
       registry.register(CustomTDSThresholdRule())
       return registry
   ```

3. **Verify with Pytest**:
   Add test case in `tests/test_rule_engine.py` and run `pytest`.

---

## 4. How to Add a New Database Model

1. Define entity in `src/database/models.py`:
   ```python
   class AuditNote(Base):
       __tablename__ = 'audit_notes'
       id = Column(Integer, primary_key=True)
       engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
       note = Column(Text, nullable=False)
       created_at = Column(DateTime, default=datetime.datetime.utcnow)
   ```
2. Increment migration version in `src/deployment/migration.py`.

---

## 5. Coding Standards

- **Formatting**: `black` (120 line length)
- **Linting**: `ruff`
- **Typing**: Explicit type hints on all public function signatures.
- **Error Handling**: Use domain exceptions (`ValidationError`, `EntityNotFoundError`) from `core.exceptions`.
