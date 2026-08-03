"""Camera-specific exceptions."""


class CameraError(Exception):
    """Base exception for camera-related errors."""

    pass


class CameraValidationError(CameraError):
    """Raised when camera validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class CameraNotFoundError(CameraError):
    """Raised when camera is not found."""

    pass


class CameraDuplicateIDError(CameraError):
    """Raised when duplicate camera ID is detected."""

    pass


class CameraProjectionError(CameraError):
    """Raised when camera projection configuration is invalid."""

    pass


class CameraSerializationError(CameraError):
    """Raised when camera serialization fails."""

    pass


class CameraReferenceError(CameraError):
    """Raised when camera reference is invalid."""

    pass
