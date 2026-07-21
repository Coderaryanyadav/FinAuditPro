"""
Central Rule Registry & Configuration Store for FinAuditPro.
Manages rule lookup, enabling/disabling rules, category indexing, and dynamic threshold overrides.
"""

from typing import Dict, List, Optional
import logging
from .base_rule import BaseRule
from .severity import RuleCategory, RuleSeverity

logger = logging.getLogger(__name__)

class RuleRegistry:
    """Central registry storing and managing all enterprise audit rules."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleRegistry, cls).__new__(cls)
            cls._instance._rules: Dict[str, BaseRule] = {}
        return cls._instance

    def register(self, rule: BaseRule) -> None:
        """Register an audit rule."""
        self._rules[rule.rule_id] = rule
        logger.debug(f"Registered audit rule: {rule.rule_id} ({rule.rule_name})")

    def get_rule(self, rule_id: str) -> Optional[BaseRule]:
        """Get rule by ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[BaseRule]:
        """Get list of all registered rules."""
        return list(self._rules.values())

    def get_active_rules(self) -> List[BaseRule]:
        """Get list of enabled rules."""
        return [r for r in self._rules.values() if r.enabled]

    def get_rules_by_category(self, category: RuleCategory) -> List[BaseRule]:
        """Get rules filtered by category."""
        return [r for r in self._rules.values() if r.category == category]

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> bool:
        """Enable or disable a specific rule."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = enabled
            return True
        return False

    def clear(self) -> None:
        """Clear all registered rules."""
        self._rules.clear()
