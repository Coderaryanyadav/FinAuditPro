"""
Master Audit Rule Engine Facade for FinAuditPro.
Orchestrates parallel rule execution, computes portfolio risk metrics, builds AI context for failed rules, and saves findings.
"""

from typing import Dict, Any, List, Optional
import time
import logging

from .rule_registry import RuleRegistry
from .rule_loader import RuleLoader
from .rule_executor import RuleExecutor
from .rule_result import RuleResult
from .severity import RuleSeverity

logger = logging.getLogger(__name__)

class AuditRuleEngine:
    """Master Facade for the Enterprise Audit Rule Engine."""

    def __init__(self, registry: Optional[RuleRegistry] = None, executor: Optional[RuleExecutor] = None):
        self.registry = registry or RuleLoader.load_all_rules()
        self.executor = executor or RuleExecutor()

    def evaluate_document(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluates active audit rules against document data.
        Returns execution metrics, list of passed/failed RuleResults, and AI context summary.
        """
        start_time = time.time()
        active_rules = self.registry.get_active_rules()

        # Execute rules in parallel
        results: List[RuleResult] = self.executor.execute_all(active_rules, data, context)

        passed_results = [r for r in results if r.passed]
        failed_results = [r for r in results if not r.passed]

        # Calculate aggregated risk score
        total_risk = sum(r.risk_score for r in failed_results)
        max_possible_risk = len(active_rules) * 100.0
        portfolio_risk_score = min(round((total_risk / max_possible_risk) * 100.0 if max_possible_risk > 0 else 0.0, 2), 100.0)

        # Count severities
        critical_count = sum(1 for r in failed_results if r.severity == RuleSeverity.CRITICAL)
        high_count = sum(1 for r in failed_results if r.severity == RuleSeverity.HIGH)
        medium_count = sum(1 for r in failed_results if r.severity == RuleSeverity.MEDIUM)
        low_count = sum(1 for r in failed_results if r.severity == RuleSeverity.LOW)

        # Generate AI Prompt Context for failed rules
        ai_context = self.build_ai_rule_context(failed_results)

        elapsed = round(time.time() - start_time, 4)
        logger.info(f"Rule Engine evaluated {len(results)} rules in {elapsed}s. Failed: {len(failed_results)}")

        return {
            "total_rules": len(results),
            "passed_count": len(passed_results),
            "failed_count": len(failed_results),
            "risk_score": portfolio_risk_score,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "processing_time": elapsed,
            "failed_rules": [r.to_dict() for r in failed_results],
            "all_results": [r.to_dict() for r in results],
            "ai_prompt_context": ai_context
        }

    def build_ai_rule_context(self, failed_results: List[RuleResult]) -> str:
        """Constructs structured context text from failed rules to feed into the AuditCopilot."""
        if not failed_results:
            return "Rule Engine Evaluation: All automated audit and compliance rules passed successfully."

        lines = ["FAILED AUTOMATED AUDIT RULES:"]
        for idx, r in enumerate(failed_results, start=1):
            lines.append(
                f"{idx}. [{r.rule_id}] {r.rule_name} (Severity: {r.severity.value})\n"
                f"   Standard: {r.accounting_standard} / {r.audit_standard}\n"
                f"   Issue: {r.description}\n"
                f"   Evidence: {', '.join(r.evidence)}\n"
                f"   Recommendation: {r.recommendation}\n"
            )

        return "\n".join(lines)
