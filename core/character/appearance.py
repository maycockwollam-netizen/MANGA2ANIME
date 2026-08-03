"""Character appearance representation."""

from typing import Any

from pydantic import BaseModel, Field


class CharacterAppearance(BaseModel):
    """Represents a character's visual appearance.

    This is a generic representation that contains lightweight references
    to visual assets and style descriptions. Asset loading/processing
    is handled by future asset systems.
    """

    description: str = Field(default="", max_length=2000)
    style: str = Field(default="", max_length=255)
    hair_color: str = Field(default="", max_length=100)
    eye_color: str = Field(default="", max_length=100)
    skin_tone: str = Field(default="", max_length=100)
    height_description: str = Field(default="", max_length=255)
    build_description: str = Field(default="", max_length=255)
    age_description: str = Field(default="", max_length=255)
    asset_references: dict[str, str] = Field(default_factory=dict)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _info: object) -> None:
        """Validate appearance data."""
        if len(self.description) > 2000:
            raise ValueError("Description must be 2000 characters or less")
        if len(self.style) > 255:
            raise ValueError("Style must be 255 characters or less")

    def has_asset_reference(self, key: str) -> bool:
        """Check if an asset reference exists.

        Args:
            key: Reference key (e.g., 'design', 'portrait', 'model').

        Returns:
            True if reference exists, False otherwise.
        """
        return key in self.asset_references and bool(self.asset_references[key])

    def get_asset_reference(self, key: str) -> str | None:
        """Get an asset reference.

        Args:
            key: Reference key.

        Returns:
            The asset reference value or None if not set.
        """
        return self.asset_references.get(key)

    def set_asset_reference(self, key: str, value: str) -> None:
        """Set an asset reference.

        Args:
            key: Reference key.
            value: Asset identifier/path/URI.
        """
        self.asset_references[key] = value

    def remove_asset_reference(self, key: str) -> None:
        """Remove an asset reference.

        Args:
            key: Reference key to remove.
        """
        if key in self.asset_references:
            del self.asset_references[key]

    def get_asset_references(self) -> dict[str, str]:
        """Get all asset references.

        Returns:
            Dictionary of asset references.
        """
        return dict(self.asset_references)

    def validate(self) -> list[str]:
        """Validate the appearance.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if len(self.description) > 2000:
            errors.append("Description must be 2000 characters or less")

        if len(self.style) > 255:
            errors.append("Style must be 255 characters or less")

        # Validate asset reference keys
        for key in self.asset_references:
            if not key or len(key) > 255:
                errors.append(f"Invalid asset reference key: '{key}'")

        return errors
