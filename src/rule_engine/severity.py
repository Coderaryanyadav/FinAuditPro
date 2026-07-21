"""
Rule Severity & Category Enumerations for FinAuditPro.
"""

from enum import Enum

class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RuleCategory(str, Enum):
    GST = "GST Rules"
    INCOME_TAX = "Income Tax Rules"
    ACCOUNTING = "Accounting Rules"
    FRAUD = "Fraud Detection Rules"
    COMPLIANCE = "Compliance Rules"
    INTERNAL_CONTROL = "Internal Control Rules"
    AUDIT_PROCEDURE = "Audit Procedure Rules"
