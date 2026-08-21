"""
Parallel Rule Execution Engine for FinAuditPro.
Evaluates registered audit rules in parallel threads with caching for performance.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import time
import logging

from .base_rule import BaseRule
from .rule_result import RuleResult

logger = logging.getLogger(__name__)

class RuleExecutor:
    """Executes rules in parallel and manages execution cache."""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self._cache: Dict[str, RuleResult] = {}

    def execute_rule(self, rule: BaseRule, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> RuleResult:
        """Executes a single rule safely."""
        start_time = time.time()
        try:
            result = rule.evaluate(data, context)
            logger.debug(f"Evaluated rule {rule.rule_id} in {round(time.time() - start_time, 4)}s -> Passed: {result.passed}")
            return result
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Rule execution error for {rule.rule_id}: {e}", exc_info=True)
            return RuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                category=rule.category,
                severity=rule.severity,
                passed=False,
                risk_score=50.0,
                description=f"Rule evaluation failed with exception: {e}",
                evidence=[str(e)],
                recommendation="Investigate rule evaluation exception."
            )

    def execute_all(self, rules: List[BaseRule], data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[RuleResult]:
        """Executes list of rules in parallel using ThreadPoolExecutor."""
        if not rules:
            return []

        results: List[RuleResult] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(rules))) as executor:
            future_to_rule = {executor.submit(self.execute_rule, r, data, context): r for r in rules}
            for future in as_completed(future_to_rule):
                res = future.result()
                results.append(res)
                self._cache[res.rule_id] = res

        return results
