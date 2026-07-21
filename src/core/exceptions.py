class FinAuditError(Exception):
    """Base exception class for all FinAuditPro custom exceptions."""
    pass

class ValidationError(FinAuditError):
    """Raised when business rules or field validations fail."""
    pass

class AuthenticationError(FinAuditError):
    """Raised when login fails or permissions are insufficient."""
    pass

class EntityNotFoundError(FinAuditError):
    """Raised when a requested database record does not exist."""
    pass

class DuplicateRecordError(FinAuditError):
    """Raised when unique constraints are violated (e.g., duplicate GSTIN)."""
    pass
