"""Domain layer exception hierarchy for FinAuditPro."""


class DomainError(Exception):
    """Base exception for all domain logic errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityNotFoundError(DomainError):
    """Raised when a requested domain entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} with ID '{entity_id}' was not found.")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(DomainError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(self, entity_type: str, field_name: str, field_value: str) -> None:
        super().__init__(
            f"{entity_type} with {field_name} '{field_value}' already exists."
        )
        self.entity_type = entity_type
        self.field_name = field_name
        self.field_value = field_value


class ValidationError(DomainError):
    """Raised when domain validation rules are violated."""

    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class PermissionDeniedError(DomainError):
    """Raised when access control permissions are violated or session is missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidStateTransitionError(DomainError):
    """Raised when an illegal status state transition is attempted."""

    def __init__(self, entity_type: str, current_state: str, target_state: str) -> None:
        super().__init__(f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'.")
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state


class AuditIntegrityError(DomainError):
    """Raised when audit log hash chain or content hash integrity is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SecurityError(DomainError):
    """Raised when path traversal, Zip-Slip, or security controls are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
