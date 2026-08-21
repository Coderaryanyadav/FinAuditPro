"""
Abstract Base Rule Class for FinAuditPro.
Serves as the foundation for all configurable audit, tax, and fraud detection rules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .severity import RuleSeverity, RuleCategory
from .rule_result import RuleResult

class BaseRule(ABC):
    """Abstract Base Class for Configurable Enterprise Audit Rules."""

    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        category: RuleCategory,
        severity: RuleSeverity = RuleSeverity.MEDIUM,
        enabled: bool = True,
        threshold: float = 0.0,
        tolerance: float = 0.0,
        accounting_standard: str = "SA 240",
        audit_standard: str = "SA 500"
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.category = category
        self.severity = severity
        self.enabled = enabled
        self.threshold = threshold
        self.tolerance = tolerance
        self.accounting_standard = accounting_standard
        self.audit_standard = audit_standard

    @abstractmethod
    def evaluate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> RuleResult:
        """
        Evaluates document text, extracted metadata, or transaction records against the rule.
        Must return a valid RuleResult object.
        """
        pass
