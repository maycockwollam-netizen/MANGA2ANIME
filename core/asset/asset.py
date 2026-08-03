"""Main Asset model."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from core.asset.exceptions import AssetValidationError
from core.asset.metadata import AssetMetadata
from core.asset.properties import AssetProperties
from core.asset.reference import AssetReference
from core.asset.state import AssetState
from core.asset.types import AssetType


class Asset(BaseModel):
    """Main asset model.

    Represents an asset in the Manga2Anime system.
    Does not load, decode, or process the actual asset data.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="", max_length=255)
    asset_type: AssetType = Field(default=AssetType.OTHER)
    metadata: AssetMetadata = Field(default_factory=AssetMetadata)
    reference: AssetReference = Field(default_factory=AssetReference)
    properties: AssetProperties = Field(default_factory=AssetProperties)
    state: AssetState = Field(default_factory=AssetState)

    def update_name(self, name: str) -> None:
        """Update asset name.

        Args:
            name: New name.
        """
        if len(name) > 255:
            raise ValueError("Name must be 255 characters or less")
        self.name = name
        self.metadata.updated_at = datetime.now(UTC)

    def update_display_name(self, display_name: str) -> None:
        """Update display name.

        Args:
            display_name: New display name.
        """
        if len(display_name) > 255:
            raise ValueError("Display name must be 255 characters or less")
        self.metadata.display_name = display_name
        self.metadata.updated_at = datetime.now(UTC)

    def set_asset_type(self, asset_type: AssetType) -> None:
        """Set asset type.

        Args:
            asset_type: New asset type.
        """
        self.asset_type = asset_type
        self.metadata.updated_at = datetime.now(UTC)

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state.

        Args:
            enabled: New enabled state.
        """
        self.state.enabled = enabled
        self.metadata.updated_at = datetime.now(UTC)

    def set_available(self, available: bool) -> None:
        """Set available state.

        Args:
            available: New available state.
        """
        self.state.available = available
        self.metadata.updated_at = datetime.now(UTC)

    def set_verified(self, verified: bool) -> None:
        """Set verified state.

        Args:
            verified: New verified state.
        """
        self.state.verified = verified
        self.metadata.updated_at = datetime.now(UTC)

    def add_tag(self, tag: str) -> None:
        """Add a tag.

        Args:
            tag: Tag to add.
        """
        if tag and tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.metadata.updated_at = datetime.now(UTC)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag.

        Args:
            tag: Tag to remove.
        """
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.metadata.updated_at = datetime.now(UTC)

    def has_tag(self, tag: str) -> bool:
        """Check if asset has a tag.

        Args:
            tag: Tag to check.

        Returns:
            True if tag exists, False otherwise.
        """
        return tag in self.metadata.tags

    def set_path(self, path: str) -> None:
        """Set asset path.

        Args:
            path: File path.
        """
        self.reference.path = path
        self.metadata.updated_at = datetime.now(UTC)

    def get_path(self) -> str:
        """Get asset path.

        Returns:
            Asset path or empty string.
        """
        return self.reference.path

    def set_uri(self, uri: str) -> None:
        """Set asset URI.

        Args:
            uri: Asset URI.
        """
        self.reference.uri = uri
        self.metadata.updated_at = datetime.now(UTC)

    def get_uri(self) -> str:
        """Get asset URI.

        Returns:
            Asset URI or empty string.
        """
        return self.reference.uri

    def set_checksum(self, checksum: str) -> None:
        """Set asset checksum.

        Args:
            checksum: File checksum.
        """
        self.reference.checksum = checksum
        self.metadata.updated_at = datetime.now(UTC)

    def get_checksum(self) -> str:
        """Get asset checksum.

        Returns:
            Asset checksum or empty string.
        """
        return self.reference.checksum

    def set_size(self, size_bytes: int) -> None:
        """Set asset size.

        Args:
            size_bytes: Size in bytes.
        """
        self.reference.size_bytes = size_bytes
        self.metadata.updated_at = datetime.now(UTC)

    def get_size(self) -> int:
        """Get asset size.

        Returns:
            Asset size in bytes.
        """
        return self.reference.size_bytes

    def validate(self) -> list[str]:
        """Validate the asset.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Asset ID is required")

        if len(self.name) > 255:
            errors.append("Name must be 255 characters or less")

        # Validate metadata
        metadata_errors = self.metadata.validate()
        for error in metadata_errors:
            errors.append(f"Metadata: {error}")

        # Validate reference
        reference_errors = self.reference.validate()
        for error in reference_errors:
            errors.append(f"Reference: {error}")

        # Validate properties
        property_errors = self.properties.validate()
        for error in property_errors:
            errors.append(f"Properties: {error}")

        # Validate state
        state_errors = self.state.validate()
        for error in state_errors:
            errors.append(f"State: {error}")

        return errors

    def validate_or_raise(self) -> None:
        """Validate the asset and raise if invalid.

        Raises:
            AssetValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise AssetValidationError("Asset validation failed", errors=errors)
