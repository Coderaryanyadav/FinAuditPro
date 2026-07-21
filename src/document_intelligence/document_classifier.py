"""
Financial Document Classifier Module for FinAuditPro.
Uses pattern matching and keyword heuristics to automatically categorize audit files.
"""

from enum import Enum
import re
from typing import Dict

class DocumentCategory(str, Enum):
    INVOICE = "Invoice"
    TRIAL_BALANCE = "Trial Balance"
    LEDGER = "Ledger"
    GST_RETURN = "GST Return"
    BANK_STATEMENT = "Bank Statement"
    BALANCE_SHEET = "Balance Sheet"
    PROFIT_AND_LOSS = "Profit & Loss"
    CASH_BOOK = "Cash Book"
    PURCHASE_REGISTER = "Purchase Register"
    SALES_REGISTER = "Sales Register"
    UNKNOWN = "Unknown"


class DocumentClassifier:
    """Classifies document category using financial keyword heuristics."""

    PATTERNS: Dict[DocumentCategory, List[str]] = {
        DocumentCategory.GST_RETURN: [
            r"gstr-?1", r"gstr-?3b", r"gstr-?2a", r"gstr-?2b", r"gstin", r"input tax credit", r"outward supplies"
        ],
        DocumentCategory.INVOICE: [
            r"tax invoice", r"invoice no", r"bill to", r"ship to", r"hsn/sac", r"cgst", r"sgst", r"igst"
        ],
        DocumentCategory.TRIAL_BALANCE: [
            r"trial balance", r"debit balance", r"credit balance", r"opening balance", r"closing balance"
        ],
        DocumentCategory.BALANCE_SHEET: [
            r"balance sheet", r"liabilities", r"assets", r"share capital", r"fixed assets", r"current liabilities"
        ],
        DocumentCategory.PROFIT_AND_LOSS: [
            r"profit & loss", r"profit and loss", r"revenue from operations", r"cost of materials", r"net profit"
        ],
        DocumentCategory.BANK_STATEMENT: [
            r"bank statement", r"account statement", r"withdrawal", r"deposit", r"chq no", r"ifs code"
        ],
        DocumentCategory.PURCHASE_REGISTER: [
            r"purchase register", r"purchase invoice", r"vendor name", r"supplier name"
        ],
        DocumentCategory.SALES_REGISTER: [
            r"sales register", r"sales invoice", r"customer name", r"debtors"
        ],
        DocumentCategory.CASH_BOOK: [
            r"cash book", r"cash in hand", r"cash voucher", r"petty cash"
        ],
        DocumentCategory.LEDGER: [
            r"ledger account", r"general ledger", r"account name", r"particulars", r"vch no"
        ],
    }

    @classmethod
    def classify_text(cls, text: str, file_name: str = "") -> DocumentCategory:
        """Classifies document based on text content and file name patterns."""
        combined_text = f"{file_name}\n{text}".lower()

        # Score category matches based on pattern hits
        scores: Dict[DocumentCategory, int] = {}
        for category, patterns in cls.PATTERNS.items():
            hit_count = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text))
                hit_count += matches
            if hit_count > 0:
                scores[category] = hit_count

        if not scores:
            return DocumentCategory.UNKNOWN

        # Return category with highest pattern match count
        best_category = max(scores, key=scores.get)
        return best_category
