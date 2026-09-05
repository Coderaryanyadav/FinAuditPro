"""Deterministic heuristic document classifier for statutory audit documents."""

import re

from finauditpro.domain.document_entities import DocumentCategoryEnum

_CATEGORY_KEYWORDS: dict[DocumentCategoryEnum, list[str]] = {
    DocumentCategoryEnum.BANK_STATEMENT: [
        "bank statement", "account statement", "opening balance", "closing balance",
        "account number", "ifsc", "neft", "rtgs", "upi", "cheque no", "withdrawal",
        "deposit", "available balance", "statement of account",
    ],
    DocumentCategoryEnum.TAX_RETURN: [
        "income tax return", "itr", "form 26as", "assessment year", "financial year",
        "taxable income", "section 80c", "tds deducted", "advance tax", "gstr-1",
        "gstr-3b", "gstr-9", "gstin", "input tax credit", "net tax payable",
    ],
    DocumentCategoryEnum.INVOICE: [
        "tax invoice", "invoice no", "invoice date", "bill to", "ship to",
        "place of supply", "hsn/sac", "cgst", "sgst", "igst", "total amount",
        "subtotal", "tax amount", "due date", "vendor gstin",
    ],
    DocumentCategoryEnum.PURCHASE_ORDER: [
        "purchase order", "po number", "po date", "order date", "vendor code",
        "delivery date", "terms of payment", "shipping instructions",
    ],
    DocumentCategoryEnum.FINANCIAL_STATEMENT: [
        "balance sheet", "statement of profit and loss", "profit & loss",
        "cash flow statement", "trial balance", "notes forming part of financial statements",
        "schedules to balance sheet", "share capital", "reserves & surplus",
    ],
    DocumentCategoryEnum.BOARD_MINUTES: [
        "minutes of the meeting", "board of directors", "held on", "present",
        "in attendance", "resolved that", "unanimously resolved", "chairman",
        "quorum", "company secretary",
    ],
    DocumentCategoryEnum.AUDIT_REPORT: [
        "independent auditor's report", "opinion", "basis for opinion",
        "key audit matters", "responsibilities of management", "sa 700",
        "report on statutory requirements", "chartered accountants",
    ],
    DocumentCategoryEnum.CONTRACT: [
        "agreement", "memorandum of understanding", "mou", "deed of partnership",
        "party of the first part", "whereas", "now it is hereby agreed",
        "indemnification", "jurisdiction", "termination clause",
    ],
}


def classify_document_text(
    text: str, filename: str = ""
) -> tuple[DocumentCategoryEnum, float, list[str]]:
    """Classify document category using transparent, deterministic keyword matching.

    Returns tuple of (DocumentCategoryEnum, confidence_score, evidence_keywords).
    """
    corpus = f"{filename} {text}".lower()

    category_scores: dict[DocumentCategoryEnum, tuple[int, list[str]]] = {}

    for category, keywords in _CATEGORY_KEYWORDS.items():
        matched_kw = []
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", corpus):
                matched_kw.append(kw)

        if matched_kw:
            category_scores[category] = (len(matched_kw), matched_kw)

    if not category_scores:
        return DocumentCategoryEnum.GENERAL, 0.50, []

    # Select category with highest keyword matches
    best_category = max(category_scores.keys(), key=lambda c: category_scores[c][0])
    match_count, evidence = category_scores[best_category]

    # Calculate confidence based on keyword density
    if match_count >= 5:
        confidence = 0.95
    elif match_count >= 3:
        confidence = 0.85
    elif match_count >= 2:
        confidence = 0.70
    else:
        confidence = 0.60

    return best_category, confidence, evidence
