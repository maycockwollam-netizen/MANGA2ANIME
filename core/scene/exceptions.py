"""Scene-specific exceptions."""


class SceneError(Exception):
    """Base exception for scene-related errors."""

    pass


class SceneValidationError(SceneError):
    """Raised when scene validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class SceneObjectError(SceneError):
    """Raised when scene object operation fails."""

    pass


class SceneHierarchyError(SceneObjectError):
    """Raised when hierarchy operation fails."""

    pass


class SceneSerializationError(SceneError):
    """Raised when scene serialization fails."""

    pass


class SceneNotFoundError(SceneObjectError):
    """Raised when scene object is not found."""

    pass


class SceneDuplicateIDError(SceneObjectError):
    """Raised when duplicate object ID is detected."""

    pass
