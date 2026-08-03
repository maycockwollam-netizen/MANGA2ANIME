"""Asset metadata."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AssetMetadata(BaseModel):
    """Metadata for an asset."""

    name: str = Field(default="", max_length=255)
    display_name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    author: str = Field(default="", max_length=255)
    source: str = Field(default="", max_length=500)
    license: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    custom_metadata: dict[str, Any] = Field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate metadata.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if len(self.name) > 255:
            errors.append("Name must be 255 characters or less")
        if len(self.display_name) > 255:
            errors.append("Display name must be 255 characters or less")
        if len(self.description) > 2000:
            errors.append("Description must be 2000 characters or less")
        if len(self.author) > 255:
            errors.append("Author must be 255 characters or less")
        if len(self.source) > 500:
            errors.append("Source must be 500 characters or less")
        if len(self.license) > 255:
            errors.append("License must be 255 characters or less")
        if len(self.notes) > 2000:
            errors.append("Notes must be 2000 characters or less")
        return errors
