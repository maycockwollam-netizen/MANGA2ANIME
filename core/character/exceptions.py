"""Character-specific exceptions."""


class CharacterError(Exception):
    """Base exception for character-related errors."""

    pass


class CharacterValidationError(CharacterError):
    """Raised when character validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class CharacterNotFoundError(CharacterError):
    """Raised when character is not found."""

    pass


class CharacterDuplicateIDError(CharacterError):
    """Raised when duplicate character ID is detected."""

    pass


class CharacterSerializationError(CharacterError):
    """Raised when character serialization fails."""

    pass


class CharacterReferenceError(CharacterError):
    """Raised when character reference is invalid."""

    pass
