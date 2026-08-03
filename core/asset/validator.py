"""Asset validation logic."""

from core.asset.asset import Asset
from core.asset.exceptions import AssetValidationError


class AssetValidator:
    """Validates assets and asset data."""

    @staticmethod
    def validate(asset: Asset) -> list[str]:
        """Validate an asset.

        Args:
            asset: Asset to validate.

        Returns:
            List of validation errors.
        """
        return asset.validate()

    @staticmethod
    def validate_or_raise(asset: Asset) -> None:
        """Validate an asset and raise if invalid.

        Args:
            asset: Asset to validate.

        Raises:
            AssetValidationError: If validation fails.
        """
        errors = asset.validate()
        if errors:
            raise AssetValidationError("Asset validation failed", errors=errors)

    @staticmethod
    def validate_path(path: str) -> list[str]:
        """Validate an asset path.

        Args:
            path: Path to validate.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if not path:
            errors.append("Path cannot be empty")
        elif len(path) > 1000:
            errors.append("Path must be 1000 characters or less")
        return errors

    @staticmethod
    def validate_uri(uri: str) -> list[str]:
        """Validate an asset URI.

        Args:
            uri: URI to validate.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if not uri:
            errors.append("URI cannot be empty")
        elif len(uri) > 2000:
            errors.append("URI must be 2000 characters or less")
        # Basic URI validation
        if uri and not uri.startswith(("http://", "https://", "file://", "s3://", "gs://")):
            if ":" in uri and "/" not in uri:
                pass  # Could be a Windows path with drive letter
            elif uri.startswith("/") or uri.startswith("./") or uri.startswith("../"):
                pass  # Unix-style path
            else:
                errors.append("URI must start with a valid scheme or be a relative/absolute path")
        return errors

    @staticmethod
    def validate_dimensions(width: int | None, height: int | None) -> list[str]:
        """Validate image/video dimensions.

        Args:
            width: Width in pixels.
            height: Height in pixels.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if width is not None and width <= 0:
            errors.append("Width must be positive")
        if height is not None and height <= 0:
            errors.append("Height must be positive")
        if width is not None and height is not None:
            if width > 32768:
                errors.append("Width exceeds maximum supported value (32768)")
            if height > 32768:
                errors.append("Height exceeds maximum supported value (32768)")
        return errors

    @staticmethod
    def validate_duration(duration: float | None) -> list[str]:
        """Validate media duration.

        Args:
            duration: Duration in seconds.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if duration is not None and duration < 0:
            errors.append("Duration must be non-negative")
        if duration is not None and duration > 86400:
            errors.append("Duration exceeds 24 hours")
        return errors
