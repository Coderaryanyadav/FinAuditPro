"""
ICAI-Standard Report Templates & Audit Opinions Factory for FinAuditPro.
Provides templates formatted according to Standards on Auditing (SA 700, SA 705, SA 706).
"""

from enum import Enum
from typing import Dict, Any

class ReportType(str, Enum):
    AUDIT_REPORT = "Audit Report"
    RISK_ASSESSMENT = "Risk Assessment Report"
    COMPLIANCE_REPORT = "Compliance Report"
    GST_REPORT = "GST Report"
    WORKING_PAPERS = "Working Papers"
    MANAGEMENT_LETTER = "Management Letter"
    EXECUTIVE_SUMMARY = "Executive Summary"
    INTERNAL_CONTROL = "Internal Control Report"


class ReportTemplateFactory:
    """Generates standard audit report opinion text templates."""

    @staticmethod
    def get_unmodified_opinion_template(company_name: str, financial_year: str) -> str:
        return f"""
INDEPENDENT AUDITOR'S REPORT
To the Members of {company_name}

Report on the Audit of the Financial Statements

Opinion:
We have audited the financial statements of {company_name}, which comprise the Balance Sheet as at 31st March {financial_year}, the Statement of Profit and Loss, and Statement of Cash Flows for the year then ended.

In our opinion and to the best of our information and according to the explanations given to us, the aforesaid financial statements give the information required by the Companies Act, 2013 in the manner so required and give a true and fair view in conformity with the accounting principles generally accepted in India.

Basis for Opinion:
We conducted our audit in accordance with the Standards on Auditing (SAs) specified under Section 143(10) of the Companies Act, 2013. We are independent of the Company in accordance with the Code of Ethics issued by the Institute of Chartered Accountants of India (ICAI).
"""

    @staticmethod
    def get_qualified_opinion_template(company_name: str, financial_year: str, qualification_reasons: str) -> str:
        return f"""
INDEPENDENT AUDITOR'S REPORT (QUALIFIED OPINION)
To the Members of {company_name}

Qualified Opinion:
Except for the effects of the matter described in the Basis for Qualified Opinion section of our report, the aforesaid financial statements give a true and fair view in conformity with the accounting principles generally accepted in India.

Basis for Qualified Opinion:
{qualification_reasons}
"""
