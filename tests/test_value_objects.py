"""Unit tests for Indian Domain Value Objects (Money, FinancialYear, PAN, GSTIN, CIN, DIN)."""

from datetime import date
from decimal import Decimal

import pytest

from finauditpro.domain.value_objects import CIN, DIN, GSTIN, PAN, FinancialYear, Money


def test_money_paise_and_rupees() -> None:
    m1 = Money(10000)  # ₹100.00
    assert m1.rupees == Decimal("100.00")

    m2 = Money.from_rupees("12345678.90")
    assert m2.paise == 1234567890
    assert m2.rupees == Decimal("12345678.90")
    assert m2.format_indian() == "₹1,23,45,678.90"


def test_money_rejects_float() -> None:
    with pytest.raises(TypeError):
        Money(10.5)  # type: ignore

    with pytest.raises(TypeError):
        Money.from_rupees(10.5)  # type: ignore


def test_money_ordering_is_consistent_for_numeric_values() -> None:
    money = Money.from_rupees("100.00")
    assert money <= Money(10_000)
    assert money <= Decimal("100.00")
    assert money <= 100
    assert not money <= Decimal("99.99")


def test_financial_year() -> None:
    fy = FinancialYear.from_string("2025-26")
    assert fy.start_year == 2025
    assert fy.label == "2025-26"
    assert fy.start_date == date(2025, 4, 1)
    assert fy.end_date == date(2026, 3, 31)

    fy_from_dt1 = FinancialYear.from_date(date(2025, 5, 10))
    assert fy_from_dt1.label == "2025-26"

    fy_from_dt2 = FinancialYear.from_date(date(2026, 2, 15))
    assert fy_from_dt2.label == "2025-26"


def test_pan_holder_types() -> None:
    pan_ind = PAN("ABCPP1234F")
    assert pan_ind.holder_type == "Individual"

    pan_firm = PAN("ABCFF1234F")
    assert pan_firm.holder_type == "Firm / LLP"

    pan_comp = PAN("ABCCF1234F")
    assert pan_comp.holder_type == "Company"

    with pytest.raises(ValueError):
        PAN("INVALID_PAN")


def test_gstin_and_checksum() -> None:
    gstin = GSTIN("27AAPFU0939F1ZV")
    assert gstin.state_code == "27"
    assert gstin.pan_number == "AAPFU0939F"
    assert gstin.checksum_valid is True

    with pytest.raises(ValueError):
        GSTIN("INVALID_GSTIN")


def test_cin_and_din() -> None:
    cin = CIN("L12345MH2020PLC123456")
    assert cin.is_listed is True

    din = DIN("12345678")
    assert din.value == "12345678"

    with pytest.raises(ValueError):
        DIN("ABC12345")
