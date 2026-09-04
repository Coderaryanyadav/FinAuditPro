"""Financial currency and date parsers with Indian locale, Decimal precision, and CSV formula sanitization."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from finauditpro.domain.value_objects import Money


def parse_indian_currency(val: Any) -> Money:
    """Parse raw cell string into stdlib Decimal and convert to Money value object (integer paise).

    Strips Indian digit separators (e.g. '1,23,456.78' -> Decimal('123456.78') -> 12345678 paise).
    Raises ValueError on unparseable non-empty amounts.
    """
    if val is None:
        return Money(paise=0)

    s_val = str(val).strip()
    if not s_val or s_val.lower() in ("nan", "none", "null", "-"):
        return Money(paise=0)

    clean_str = re.sub(r"[₹\$\,\s]", "", s_val)
    if clean_str.startswith("(") and clean_str.endswith(")"):
        clean_str = f"-{clean_str[1:-1]}"

    try:
        dec = Decimal(clean_str)
        paise = int((dec * Decimal("100")).quantize(Decimal("1")))
        return Money(paise=paise)
    except (InvalidOperation, ValueError) as ex:
        raise ValueError(f"Invalid monetary amount cell value: '{val}'") from ex


def parse_indian_date(val: Any) -> str | None:
    """Parse raw date string or Excel date value into YYYY-MM-DD format using day-first convention."""
    if val is None:
        return None

    s_val = str(val).strip()
    if not s_val or s_val.lower() in ("nan", "none", "null", "-"):
        return None

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d-%b-%Y", "%d %b %Y"):
        try:
            from datetime import datetime

            dt = datetime.strptime(s_val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    try:
        from dateutil import parser

        dt = parser.parse(s_val, dayfirst=True)
        return str(dt.strftime("%Y-%m-%d"))
    except Exception:
        raise ValueError(f"Unparseable date value: '{val}'") from None


def sanitize_export_cell(val: str) -> str:
    """Protect against CSV formula injection attacks by prefixing dangerous formula triggers with a single quote."""
    if not val:
        return val
    s = str(val)
    if s.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{s}"
    return s
