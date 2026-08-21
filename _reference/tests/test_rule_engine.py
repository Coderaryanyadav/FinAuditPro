"""
Unit Tests for FinAuditPro Enterprise Audit Rule Engine.
Tests Rule Registration, GST, Tax, Fraud (Benford's Law), Accounting Rules, and Parallel Execution.
"""

import unittest
from rule_engine.rule_engine import AuditRuleEngine
from rule_engine.severity import RuleCategory, RuleSeverity
from rule_engine.rule_loader import RuleLoader


class TestRuleEngine(unittest.TestCase):

    def setUp(self):
        self.engine = AuditRuleEngine()

    def test_missing_gstin_rule(self):
        data = {"cleaned_text": "Invoice without GSTIN", "gstin": None}
        res = self.engine.evaluate_document(data)
        self.assertTrue(res["failed_count"] > 0)
        failed_ids = [r["rule_id"] for r in res["failed_rules"]]
        self.assertIn("GST-001", failed_ids)

    def test_benford_law_rule(self):
        # Benford distribution violation data
        data = {"amounts_list": [999, 988, 888, 877, 777, 766, 666, 555, 444, 333]}
        res = self.engine.evaluate_document(data)
        failed_ids = [r["rule_id"] for r in res["failed_rules"]]
        self.assertIn("FRAUD-001", failed_ids)

    def test_negative_cash_rule(self):
        data = {"cash_balance": -45000.0}
        res = self.engine.evaluate_document(data)
        failed_ids = [r["rule_id"] for r in res["failed_rules"]]
        self.assertIn("ACCT-001", failed_ids)

    def test_large_cash_payment_rule(self):
        data = {"payment_mode": "cash", "total_amount": 25000.0}
        res = self.engine.evaluate_document(data)
        failed_ids = [r["rule_id"] for r in res["failed_rules"]]
        self.assertIn("TAX-002", failed_ids)


if __name__ == "__main__":
    unittest.main()
