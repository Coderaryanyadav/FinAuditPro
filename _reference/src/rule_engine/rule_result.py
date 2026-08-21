"""
Rule Evaluation Result Model for FinAuditPro.
Defines the standardized audit finding structure returned by every audit rule.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .severity import RuleSeverity, RuleCategory

@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    passed: bool
    risk_score: float  # 0 to 100
    description: str
    evidence: List[str] = field(default_factory=list)
    affected_records: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    accounting_standard: str = "SA 240"
    audit_standard: str = "SA 500"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "passed": self.passed,
            "risk_score": round(self.risk_score, 2),
            "description": self.description,
            "evidence": self.evidence,
            "affected_records": self.affected_records,
            "recommendation": self.recommendation,
            "accounting_standard": self.accounting_standard,
            "audit_standard": self.audit_standard,
        }
