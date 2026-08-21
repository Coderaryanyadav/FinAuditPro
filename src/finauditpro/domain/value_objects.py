"""Indian Domain Value Objects enforcing regulatory and financial domain constraints."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Money:
    """Money value object storing integer paise (100 paise = ₹1.00). Rejects float construction."""

    paise: int

    def __post_init__(self) -> None:
        if isinstance(self.paise, float):
            raise TypeError(
                "Float is prohibited for Money calculations to prevent rounding inaccuracies. Use int paise or Money.from_rupees()."
            )
        if not isinstance(self.paise, int):
            raise TypeError(f"Money paise must be an integer, got {type(self.paise).__name__}")

    @classmethod
    def from_rupees(cls, amount: Decimal | str | int) -> "Money":
        """Construct Money from rupees Decimal, string, or int."""
        if isinstance(amount, float):
            raise TypeError("Float is prohibited for Money construction. Pass Decimal or str.")
        dec = Decimal(str(amount))
        paise_val = int((dec * Decimal("100")).quantize(Decimal("1")))
        return cls(paise=paise_val)

    @property
    def rupees(self) -> Decimal:
        """Return monetary value in Rupees as Decimal."""
        return (Decimal(self.paise) / Decimal("100")).quantize(Decimal("0.01"))

    def format_indian(self) -> str:
        """Format rupees using Indian numbering system (e.g., ₹1,23,45,678.90)."""
        dec_val = self.rupees
        sign = "-" if dec_val < 0 else ""
        abs_dec = abs(dec_val)
        int_part, dec_part = f"{abs_dec:.2f}".split(".")

        if len(int_part) <= 3:
            formatted_int = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            groups = []
            while remaining:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            groups.reverse()
            formatted_int = ",".join(groups) + "," + last_three

        return f"{sign}₹{formatted_int}.{dec_part}"

    @property
    def formatted(self) -> str:
        return self.format_indian()

    def __add__(self, other: Any) -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(paise=self.paise + other.paise)

    def __sub__(self, other: Any) -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(paise=self.paise - other.paise)

    def __mul__(self, scalar: int) -> "Money":
        if not isinstance(scalar, int):
            raise TypeError("Money scalar multiplication requires integer factor.")
        return Money(paise=self.paise * scalar)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Money):
            return self.paise == other.paise
        if isinstance(other, (int, float, Decimal)):
            return self.rupees == Decimal(str(other))
        return False

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Money):
            return self.paise < other.paise
        if isinstance(other, (int, float, Decimal)):
            return self.rupees < Decimal(str(other))
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Money):
            return self.paise <= other.paise
        if isinstance(other, (int, float, Decimal)):
            return self.rupees <= Decimal(str(other))
        return NotImplemented


@dataclass(frozen=True)
class FinancialYear:
    """Indian Financial Year (1 April -> 31 March, e.g. 2025-26)."""

    start_year: int

    def __post_init__(self) -> None:
        if self.start_year < 1900 or self.start_year > 2100:
            raise ValueError(f"Invalid Financial Year start year: {self.start_year}")

    @classmethod
    def from_string(cls, fy_str: str) -> "FinancialYear":
        """Parse '2025-26' or '2025-2026' format."""
        clean = fy_str.strip()
        m = re.match(r"^(\d{4})[-/](\d{2}|\d{4})$", clean)
        if not m:
            raise ValueError(
                f"Invalid Indian Financial Year format: '{fy_str}'. Expected format e.g. '2025-26'"
            )
        start = int(m.group(1))
        return cls(start_year=start)

    @classmethod
    def from_date(cls, dt: date) -> "FinancialYear":
        """Derive FY from date (e.g. 2025-05-10 is FY 2025-26; 2026-02-15 is FY 2025-26)."""
        if dt.month >= 4:
            return cls(start_year=dt.year)
        return cls(start_year=dt.year - 1)

    @property
    def label(self) -> str:
        end_short = str(self.start_year + 1)[-2:]
        return f"{self.start_year}-{end_short}"

    @property
    def start_date(self) -> date:
        return date(self.start_year, 4, 1)

    @property
    def end_date(self) -> date:
        return date(self.start_year + 1, 3, 31)


_PAN_HOLDER_TYPES = {
    "P": "Individual",
    "C": "Company",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Firm / LLP",
    "A": "Association of Persons (AOP)",
    "T": "Trust",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government",
}


@dataclass(frozen=True)
class PAN:
    """Indian Permanent Account Number (PAN) value object."""

    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean):
            raise ValueError(
                f"Invalid PAN structure: '{self.value}'. Expected 5 letters, 4 digits, 1 letter."
            )
        object.__setattr__(self, "value", clean)

    @property
    def holder_type(self) -> str:
        code = self.value[3]
        return _PAN_HOLDER_TYPES.get(code, "Unknown")


_GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class GSTIN:
    """Indian Goods & Services Tax Identification Number (GSTIN)."""

    value: str
    checksum_valid: bool = True

    def __post_init__(self) -> None:
        clean = self.value.strip().upper()
        if not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", clean):
            raise ValueError(
                f"Invalid GSTIN structure: '{self.value}'. Must be 15 characters matching GSTIN format."
            )
        object.__setattr__(self, "value", clean)

        # Validate mod-36 checksum
        computed_check = self.compute_checksum(clean[:14])
        if computed_check != clean[14]:
            object.__setattr__(self, "checksum_valid", False)

    @staticmethod
    def compute_checksum(input_14: str) -> str:
        """Compute mod-36 checksum character for 14-char GSTIN prefix."""
        factor = [1, 2]
        total = 0
        for i, char in enumerate(input_14):
            val = _GSTIN_CHARSET.index(char)
            f = factor[i % 2]
            prod = val * f
            total += (prod // 36) + (prod % 36)
        check_idx = (36 - (total % 36)) % 36
        return _GSTIN_CHARSET[check_idx]

    @property
    def pan_number(self) -> str:
        return self.value[2:12]

    @property
    def state_code(self) -> str:
        return self.value[:2]


@dataclass(frozen=True)
class CIN:
    """Indian Corporate Identity Number (CIN)."""

    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip().upper()
        if not re.match(r"^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", clean):
            raise ValueError(
                f"Invalid CIN structure: '{self.value}'. Expected 21-character CIN format."
            )
        object.__setattr__(self, "value", clean)

    @property
    def is_listed(self) -> bool:
        return self.value[0] == "L"


@dataclass(frozen=True)
class DIN:
    """Indian Director Identification Number (DIN)."""

    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip()
        if not re.match(r"^[0-9]{8}$", clean):
            raise ValueError(f"Invalid DIN structure: '{self.value}'. Expected 8 digits.")
        object.__setattr__(self, "value", clean)
