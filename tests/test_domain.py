import pytest
from pydantic import ValidationError as PydanticValidationError

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    EntityTypeEnum,
    Firm,
)
from finauditpro.domain.exceptions import ValidationError


def test_firm_creation_and_validation() -> None:
    firm = Firm(
        name="Apex Audit & Co.",
        registration_number="123456N",
        pan="AAACC1234D",
        gstin="27AAACC1234D1Z5",
    )
    assert firm.name == "Apex Audit & Co."
    assert firm.pan == "AAACC1234D"
    assert firm.gstin == "27AAACC1234D1Z5"

    with pytest.raises((ValidationError, PydanticValidationError)):
        Firm(name="")

    with pytest.raises((ValidationError, PydanticValidationError)):
        Firm(name="Valid Firm", pan="INVALID_PAN")

    with pytest.raises((ValidationError, PydanticValidationError)):
        Firm(name="Valid Firm", gstin="INVALID_GSTIN")


def test_client_creation_and_validation() -> None:
    client = Client(
        firm_id="firm-123",
        name="Reliance Green Tech Pvt Ltd",
        entity_type=EntityTypeEnum.PVT_LTD,
        pan="AABCR9876E",
        gstin="27AABCR9876E1Z5",
    )
    assert client.name == "Reliance Green Tech Pvt Ltd"
    assert client.entity_type == EntityTypeEnum.PVT_LTD

    with pytest.raises((ValidationError, PydanticValidationError)):
        Client(firm_id="firm-123", name="  ")


def test_engagement_creation_and_validation() -> None:
    eng = Engagement(
        firm_id="firm-123",
        client_id="client-456",
        financial_year="2025-26",
        audit_type=AuditTypeEnum.STATUTORY_AUDIT,
        status=EngagementStatusEnum.PLANNING,
        assigned_team=["Partner", "Senior Auditor"],
    )
    assert eng.financial_year == "2025-26"
    assert eng.audit_type == AuditTypeEnum.STATUTORY_AUDIT
    assert eng.status == EngagementStatusEnum.PLANNING

    with pytest.raises((ValidationError, PydanticValidationError)):
        Engagement(firm_id="firm-123", client_id="client-456", financial_year="")


def test_utc_clock() -> None:
    now = utc_now()
    assert now.tzinfo is not None
