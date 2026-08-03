"""Asset-specific exceptions."""


class AssetError(Exception):
    """Base exception for asset-related errors."""

    pass


class AssetValidationError(AssetError):
    """Raised when asset validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class AssetNotFoundError(AssetError):
    """Raised when asset is not found."""

    pass


class AssetDuplicateIDError(AssetError):
    """Raised when duplicate asset ID is detected."""

    pass


class AssetSerializationError(AssetError):
    """Raised when asset serialization fails."""

    pass


class AssetReferenceError(AssetError):
    """Raised when asset reference is invalid."""

    pass


class AssetTypeError(AssetError):
    """Raised when asset type is invalid."""

    pass
