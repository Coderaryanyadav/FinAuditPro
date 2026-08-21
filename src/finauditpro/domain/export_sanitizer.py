"""Domain utility for CSV and Excel formula-injection escaping."""

from typing import Any

INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def escape_formula_injection(value: Any) -> Any:
    """Prefix single quote (') if value is a string starting with formula injection characters."""
    if isinstance(value, str):
        if value.startswith(INJECTION_PREFIXES):
            return f"'{value}"
    return value
