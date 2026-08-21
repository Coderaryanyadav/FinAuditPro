"""
Financial Metadata Extractor Module for FinAuditPro.
Uses regex pattern extraction to parse GSTIN, PAN, FY, Invoice Numbers, Dates, and Amounts.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ExtractedMetadata:
    gstin: Optional[str] = None
    pan: Optional[str] = None
    financial_year: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    customer_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number_masked: Optional[str] = None
    dates: List[str] = field(default_factory=list)
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: str = "INR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gstin": self.gstin,
            "pan": self.pan,
            "financial_year": self.financial_year,
            "invoice_number": self.invoice_number,
            "vendor_name": self.vendor_name,
            "customer_name": self.customer_name,
            "bank_name": self.bank_name,
            "account_number_masked": self.account_number_masked,
            "dates": self.dates,
            "total_amount": self.total_amount,
            "tax_amount": self.tax_amount,
            "currency": self.currency,
        }


class MetadataExtractor:
    """Extracts structured financial identifiers and key metrics from document text."""

    GSTIN_REGEX = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}\b"
    PAN_REGEX = r"\b[A-Z]{5}\d{4}[A-Z]{1}\b"
    FY_REGEX = r"\b(20\d{2})[-–\/](20\d{2}|\d{2})\b"
    INVOICE_REGEX = r"(?i)(?:invoice|inv|bill)\s*(?:no|num|number|\b)?\s*[:#-]\s*([A-Z0-9\/-]+)"
    DATE_REGEX = r"\b(?:\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}|\d{2,4}[-\/\.]\d{1,2}[-\/\.]\d{1,2})\b"
    AMOUNT_REGEX = r"(?i)(?:total|grand total|net amount|amount payable)\s*[:=]?\s*(?:₹|INR|Rs\.?)?\s*([\d,]+\.?\d*)"

    @classmethod
    def extract_metadata(cls, text: str) -> ExtractedMetadata:
        metadata = ExtractedMetadata()
        if not text:
            return metadata

        # 1. GSTIN
        gstin_match = re.search(cls.GSTIN_REGEX, text)
        if gstin_match:
            metadata.gstin = gstin_match.group(0)

        # 2. PAN
        pan_match = re.search(cls.PAN_REGEX, text)
        if pan_match:
            metadata.pan = pan_match.group(0)

        # 3. Financial Year
        fy_match = re.search(cls.FY_REGEX, text)
        if fy_match:
            metadata.financial_year = fy_match.group(0)

        # 4. Invoice Number
        inv_match = re.search(cls.INVOICE_REGEX, text)
        if inv_match:
            metadata.invoice_number = inv_match.group(1).strip()

        # 5. Dates
        dates = re.findall(cls.DATE_REGEX, text)
        if dates:
            metadata.dates = list(set(dates))[:5]

        # 6. Total Amount
        amt_match = re.search(cls.AMOUNT_REGEX, text)
        if amt_match:
            try:
                amt_str = amt_match.group(1).replace(",", "")
                metadata.total_amount = float(amt_str)
            except ValueError:
                pass

        return metadata
