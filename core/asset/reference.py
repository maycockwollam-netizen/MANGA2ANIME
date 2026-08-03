"""Asset reference - lightweight reference to asset location."""


from pydantic import BaseModel, Field


class AssetReference(BaseModel):
    """Lightweight reference to where an asset is stored.

    This is metadata only - does not load or verify the file.
    """

    path: str = Field(default="", max_length=1000)
    uri: str = Field(default="", max_length=2000)
    mime_type: str = Field(default="", max_length=255)
    extension: str = Field(default="", max_length=50)
    checksum: str = Field(default="", max_length=128)
    size_bytes: int = Field(default=0, ge=0)

    def validate(self) -> list[str]:
        """Validate reference fields.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if len(self.path) > 1000:
            errors.append("Path must be 1000 characters or less")
        if len(self.uri) > 2000:
            errors.append("URI must be 2000 characters or less")
        if len(self.mime_type) > 255:
            errors.append("MIME type must be 255 characters or less")
        if len(self.extension) > 50:
            errors.append("Extension must be 50 characters or less")
        if len(self.checksum) > 128:
            errors.append("Checksum must be 128 characters or less")
        if self.size_bytes < 0:
            errors.append("Size in bytes must be non-negative")
        return errors

    def has_path(self) -> bool:
        """Check if reference has a path.

        Returns:
            True if path is set.
        """
        return bool(self.path)

    def has_uri(self) -> bool:
        """Check if reference has a URI.

        Returns:
            True if URI is set.
        """
        return bool(self.uri)

    def has_checksum(self) -> bool:
        """Check if reference has a checksum.

        Returns:
            True if checksum is set.
        """
        return bool(self.checksum)
