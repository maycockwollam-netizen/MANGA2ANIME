"""Integration-level exceptions."""


class IntegrationError(Exception):
    """Base exception for integration-related errors."""

    pass


class DuplicateRegistrationError(IntegrationError):
    """Raised when attempting to register a duplicate entity."""

    pass


class EntityNotFoundError(IntegrationError):
    """Raised when an entity is not found in the context."""

    pass


class ReferenceResolutionError(IntegrationError):
    """Raised when a reference cannot be resolved."""

    def __init__(
        self, message: str, reference_id: str | None = None, reference_type: str | None = None
    ) -> None:
        super().__init__(message)
        self.reference_id = reference_id
        self.reference_type = reference_type


class IntegrationValidationError(IntegrationError):
    """Raised when integration validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class DanglingReferenceError(ReferenceResolutionError):
    """Raised when a reference points to a non-existent entity."""

    pass
