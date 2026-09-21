"""Smart Document Intelligence engine providing deterministic + AI extraction, provenance, and human override controls."""

import re
from typing import Any

from finauditpro.domain.document_entities import (
    DocumentCategoryEnum,
    DocumentMetadataField,
    DocumentStructuredMetadata,
    MetadataFieldStatusEnum,
    MetadataSourceEnum,
)
from finauditpro.infrastructure.documents.document_classifier import classify_document_text


def extract_deterministic_metadata(
    text: str,
    filename: str = "",
    client_name: str | None = None,
    active_fy: str | None = None,
    category: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL,
    category_confidence: float = 0.50,
) -> DocumentStructuredMetadata:
    """Extract structured audit metadata using transparent, deterministic regex & heuristic patterns."""
    corpus = f"{filename}\n{text}"
    meta = DocumentStructuredMetadata()

    # 1. Document Type
    meta.document_type = DocumentMetadataField(
        value=category.value,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=category_confidence,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 2. Client
    client_val = client_name
    if not client_val and client_name:
        client_val = client_name
    if not client_val:
        client_match = re.search(r"(?:Client|Company|M/s|Entity):\s*([A-Za-z0-9\s.&'-]{3,50})", corpus, re.I)
        if client_match:
            client_val = client_match.group(1).strip()
    meta.client = DocumentMetadataField(
        value=client_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.85 if client_val else 0.40,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 3. Financial Year
    fy_val = active_fy
    fy_match = re.search(r"\b(?:FY|AY|Financial Year)\s*:?\s*(\d{4}[-]\d{2,4})\b", corpus, re.I)
    if fy_match:
        fy_val = f"FY {fy_match.group(1)}"
    elif not fy_val:
        yr_match = re.search(r"\b(20\d{2}[-]20?\d{2})\b", corpus)
        if yr_match:
            fy_val = f"FY {yr_match.group(1)}"
    meta.fy = DocumentMetadataField(
        value=fy_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.90 if fy_match else (0.70 if fy_val else 0.40),
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 4. Period
    period_match = re.search(r"\b(Q[1-4]\s*(?:FY)?\s*\d{4}[-]?\d{0,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{2}/\d{2}/\d{4}\s+to\s+\d{2}/\d{2}/\d{4})\b", corpus, re.I)
    period_val = period_match.group(1) if period_match else None
    meta.period = DocumentMetadataField(
        value=period_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.85 if period_val else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 5. Document Date
    date_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b", corpus, re.I)
    date_val = date_match.group(1) if date_match else None
    meta.document_date = DocumentMetadataField(
        value=date_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.85 if date_val else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 6. Financial Amount
    amount_match = re.search(r"(?:Total|Net Payable|Grand Total|Amount|Balance)\s*:?\s*(?:INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)", corpus, re.I)
    amt_val = None
    if amount_match:
        try:
            amt_val = float(amount_match.group(1).replace(",", ""))
        except ValueError:
            amt_val = None
    meta.financial_amount = DocumentMetadataField(
        value=amt_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.85 if amt_val is not None else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 7. Reference Number
    ref_match = re.search(r"\b(INV[-:\s]+[A-Za-z0-9_-]+|PO[-:\s]+[A-Za-z0-9_-]+|Cheque\s*No\.?\s*\d+|REF[-:\s]+[A-Za-z0-9_-]+|\d{10,16})\b", corpus, re.I)
    ref_val = ref_match.group(1) if ref_match else None
    meta.reference_number = DocumentMetadataField(
        value=ref_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.80 if ref_val else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 8. Vendor / Customer
    vendor_match = re.search(r"(?:Vendor|Supplier|Billed To|Customer|Party Name):\s*([A-Za-z0-9\s.&'-]{3,50})", corpus, re.I)
    vendor_val = vendor_match.group(1).strip() if vendor_match else None
    meta.vendor_customer = DocumentMetadataField(
        value=vendor_val,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.80 if vendor_val else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    # 9. Tax Identifiers (GSTIN / PAN)
    gstin_match = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1})\b", corpus)
    pan_match = re.search(r"\b([A-Z]{5}\d{4}[A-Z]{1})\b", corpus)
    tax_id = None
    if gstin_match:
        tax_id = f"GSTIN: {gstin_match.group(1)}"
    elif pan_match:
        tax_id = f"PAN: {pan_match.group(1)}"
    meta.tax_identifiers = DocumentMetadataField(
        value=tax_id,
        source=MetadataSourceEnum.DETERMINISTIC,
        confidence=0.95 if tax_id else 0.30,
        status=MetadataFieldStatusEnum.PENDING_REVIEW,
    )

    return meta


def process_smart_document_classification_and_metadata(
    text: str,
    filename: str = "",
    client_name: str | None = None,
    active_fy: str | None = None,
    category_hint: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL,
    ai_service: Any = None,
    existing_metadata: DocumentStructuredMetadata | None = None,
) -> tuple[DocumentCategoryEnum, float, list[str], DocumentStructuredMetadata]:
    """Run pipeline: Deterministic classification -> AI classification if uncertain -> Extract metadata -> Apply human provenance locks."""
    # 1. Deterministic classification
    machine_cat, conf, evidence = classify_document_text(text, filename=filename)

    final_cat: DocumentCategoryEnum = (
        category_hint if category_hint != DocumentCategoryEnum.GENERAL else machine_cat
    )

    # 2. AI classification if uncertain (confidence < 0.75 or GENERAL)
    used_ai = False
    if (conf < 0.75 or final_cat == DocumentCategoryEnum.GENERAL) and ai_service is not None:
        try:
            # Resilient invocation of AI service
            ai_cat, ai_conf, ai_ev = ai_service.classify_document(text, filename=filename)
            if ai_cat:
                final_cat = ai_cat
                conf = max(conf, ai_conf or 0.88)
                evidence.extend(ai_ev or ["AI Classification"])
                used_ai = True
        except Exception:
            # Gracefully handle AI unavailable / error
            pass

    # 3. Extract deterministic metadata
    extracted = extract_deterministic_metadata(
        text=text,
        filename=filename,
        client_name=client_name,
        active_fy=active_fy,
        category=final_cat,
        category_confidence=conf,
    )

    if used_ai:
        extracted.document_type.source = MetadataSourceEnum.AI
        extracted.document_type.confidence = conf

    # 4. Merge metadata preserving human confirmed fields (AI must NEVER overwrite human confirmed fields)
    final_meta = merge_metadata_with_provenance(extracted, existing_metadata)

    return final_cat, conf, evidence, final_meta


def merge_metadata_with_provenance(
    new_metadata: DocumentStructuredMetadata,
    existing_metadata: DocumentStructuredMetadata | None,
) -> DocumentStructuredMetadata:
    """Merge extracted metadata, ensuring confirmed human fields are NEVER overwritten silently."""
    if not existing_metadata:
        return new_metadata

    merged = new_metadata.model_copy(deep=True)
    field_names = [
        "document_type", "client", "fy", "period", "document_date",
        "financial_amount", "reference_number", "vendor_customer", "tax_identifiers"
    ]

    for f_name in field_names:
        existing_field: DocumentMetadataField = getattr(existing_metadata, f_name)

        # Rule: Human confirmed fields take total precedence
        if (
            existing_field
            and existing_field.status == MetadataFieldStatusEnum.CONFIRMED
            and existing_field.source == MetadataSourceEnum.HUMAN
        ):
            setattr(merged, f_name, existing_field.model_copy(deep=True))

    return merged


def confirm_human_metadata(
    current_metadata: DocumentStructuredMetadata,
    overrides: dict[str, Any],
) -> DocumentStructuredMetadata:
    """Apply auditor confirmations and overrides to structured metadata with HUMAN provenance."""
    updated = current_metadata.model_copy(deep=True) if current_metadata else DocumentStructuredMetadata()

    for f_name, new_val in overrides.items():
        if hasattr(updated, f_name):
            setattr(
                updated,
                f_name,
                DocumentMetadataField(
                    value=new_val,
                    source=MetadataSourceEnum.HUMAN,
                    confidence=1.0,
                    status=MetadataFieldStatusEnum.CONFIRMED,
                ),
            )

    return updated
