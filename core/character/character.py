"""Character model and character management."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.character.appearance import CharacterAppearance
from core.character.exceptions import (
    CharacterReferenceError,
    CharacterValidationError,
)


class CharacterMetadata(BaseModel):
    """Metadata for a character."""

    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class CharacterProperties(BaseModel):
    """Extensible properties for a character."""

    height: str = Field(default="", max_length=100)
    age: str = Field(default="", max_length=100)
    role: str = Field(default="", max_length=255)
    faction: str = Field(default="", max_length=255)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class CharacterState(BaseModel):
    """Basic character state representation."""

    active: bool = Field(default=True)
    visible: bool = Field(default=True)
    enabled: bool = Field(default=True)
    custom_state: dict[str, Any] = Field(default_factory=dict)


class CharacterReferences(BaseModel):
    """Lightweight references to external resources.

    These are identifiers/paths only - no asset loading.
    """

    design_asset_id: str = Field(default="")
    portrait_asset_id: str = Field(default="")
    model_asset_id: str = Field(default="")
    voice_asset_id: str = Field(default="")
    scene_id: str = Field(default="")
    object_id: str = Field(default="")
    track_ids: list[str] = Field(default_factory=list)
    custom_references: dict[str, str] = Field(default_factory=dict)

    def get_scene_reference(self) -> str | None:
        """Get scene ID if set.

        Returns:
            Scene ID or None.
        """
        return self.scene_id if self.scene_id else None

    def get_object_reference(self) -> str | None:
        """Get object ID if set.

        Returns:
            Object ID or None.
        """
        return self.object_id if self.object_id else None

    def set_scene_reference(self, scene_id: str) -> None:
        """Set scene reference.

        Args:
            scene_id: Scene identifier.
        """
        self.scene_id = scene_id

    def set_object_reference(self, object_id: str) -> None:
        """Set object reference.

        Args:
            object_id: Object identifier.
        """
        self.object_id = object_id

    def add_track_reference(self, track_id: str) -> None:
        """Add a timeline track reference.

        Args:
            track_id: Track identifier.
        """
        if track_id and track_id not in self.track_ids:
            self.track_ids.append(track_id)

    def remove_track_reference(self, track_id: str) -> None:
        """Remove a timeline track reference.

        Args:
            track_id: Track identifier to remove.
        """
        if track_id in self.track_ids:
            self.track_ids.remove(track_id)

    def get_track_references(self) -> list[str]:
        """Get all track references.

        Returns:
            List of track IDs.
        """
        return list(self.track_ids)

    def set_asset_reference(self, key: str, asset_id: str) -> None:
        """Set an asset reference.

        Args:
            key: Asset type (design, portrait, model, voice).
            asset_id: Asset identifier.
        """
        valid_keys = {"design", "portrait", "model", "voice"}
        if key not in valid_keys:
            raise CharacterReferenceError(f"Invalid asset reference key: {key}")
        setattr(self, f"{key}_asset_id", asset_id)

    def get_asset_reference(self, key: str) -> str | None:
        """Get an asset reference.

        Args:
            key: Asset type.

        Returns:
            Asset ID or None.
        """
        valid_keys = {"design", "portrait", "model", "voice"}
        if key not in valid_keys:
            raise CharacterReferenceError(f"Invalid asset reference key: {key}")
        value = getattr(self, f"{key}_asset_id", "")
        return value if value else None

    def validate(self) -> list[str]:
        """Validate the references.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        # Validate asset IDs are not empty strings if set
        for asset_type in ["design", "portrait", "model", "voice"]:
            attr = f"{asset_type}_asset_id"
            value = getattr(self, attr, "")
            if value and len(value) > 255:
                errors.append(f"{attr} must be 255 characters or less")

        # Validate scene/object IDs
        if self.scene_id and len(self.scene_id) > 255:
            errors.append("scene_id must be 255 characters or less")
        if self.object_id and len(self.object_id) > 255:
            errors.append("object_id must be 255 characters or less")

        # Validate track IDs
        for track_id in self.track_ids:
            if not track_id or len(track_id) > 255:
                errors.append(f"Invalid track_id: '{track_id}'")

        # Validate custom references
        for key, value in self.custom_references.items():
            if not key or len(key) > 255:
                errors.append(f"Invalid custom reference key: '{key}'")
            if len(value) > 255:
                errors.append(f"Custom reference '{key}' must be 255 characters or less")

        return errors


class Character(BaseModel):
    """Main character model.

    Represents a character in the Manga2Anime system.
    Does not handle rendering, animation, AI, or asset loading.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="", max_length=255)
    display_name: str = Field(default="", max_length=255)
    metadata: CharacterMetadata = Field(default_factory=CharacterMetadata)
    appearance: CharacterAppearance = Field(default_factory=CharacterAppearance)
    properties: CharacterProperties = Field(default_factory=CharacterProperties)
    state: CharacterState = Field(default_factory=CharacterState)
    references: CharacterReferences = Field(default_factory=CharacterReferences)

    def model_post_init(self, _info: object) -> None:
        """Validate character state."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid character state: {errors}")

    def update_name(self, name: str) -> None:
        """Update character name.

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
        self.display_name = display_name
        self.metadata.updated_at = datetime.now(UTC)

    def set_active(self, active: bool) -> None:
        """Set active state.

        Args:
            active: Active state.
        """
        self.state.active = active
        self.metadata.updated_at = datetime.now(UTC)

    def set_visible(self, visible: bool) -> None:
        """Set visible state.

        Args:
            visible: Visible state.
        """
        self.state.visible = visible
        self.metadata.updated_at = datetime.now(UTC)

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state.

        Args:
            enabled: Enabled state.
        """
        self.state.enabled = enabled
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
        """Check if character has a tag.

        Args:
            tag: Tag to check.

        Returns:
            True if tag exists, False otherwise.
        """
        return tag in self.metadata.tags

    def set_custom_property(self, key: str, value: Any) -> None:
        """Set a custom property.

        Args:
            key: Property key.
            value: Property value.
        """
        self.properties.custom_attributes[key] = value
        self.metadata.updated_at = datetime.now(UTC)

    def get_custom_property(self, key: str) -> Any | None:
        """Get a custom property.

        Args:
            key: Property key.

        Returns:
            Property value or None.
        """
        return self.properties.custom_attributes.get(key)

    def remove_custom_property(self, key: str) -> None:
        """Remove a custom property.

        Args:
            key: Property key.
        """
        if key in self.properties.custom_attributes:
            del self.properties.custom_attributes[key]
            self.metadata.updated_at = datetime.now(UTC)

    def set_scene_reference(self, scene_id: str) -> None:
        """Set scene reference.

        Args:
            scene_id: Scene identifier.
        """
        self.references.set_scene_reference(scene_id)
        self.metadata.updated_at = datetime.now(UTC)

    def get_scene_reference(self) -> str | None:
        """Get scene reference.

        Returns:
            Scene ID or None.
        """
        return self.references.get_scene_reference()

    def set_object_reference(self, object_id: str) -> None:
        """Set object reference.

        Args:
            object_id: Object identifier.
        """
        self.references.set_object_reference(object_id)
        self.metadata.updated_at = datetime.now(UTC)

    def get_object_reference(self) -> str | None:
        """Get object reference.

        Returns:
            Object ID or None.
        """
        return self.references.get_object_reference()

    def add_track_reference(self, track_id: str) -> None:
        """Add timeline track reference.

        Args:
            track_id: Track identifier.
        """
        self.references.add_track_reference(track_id)
        self.metadata.updated_at = datetime.now(UTC)

    def remove_track_reference(self, track_id: str) -> None:
        """Remove timeline track reference.

        Args:
            track_id: Track identifier.
        """
        self.references.remove_track_reference(track_id)
        self.metadata.updated_at = datetime.now(UTC)

    def get_track_references(self) -> list[str]:
        """Get track references.

        Returns:
            List of track IDs.
        """
        return self.references.get_track_references()

    def validate(self) -> list[str]:
        """Validate the character.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Character ID is required")

        if len(self.name) > 255:
            errors.append("Name must be 255 characters or less")

        if len(self.display_name) > 255:
            errors.append("Display name must be 255 characters or less")

        if len(self.metadata.description) > 2000:
            errors.append("Metadata description must be 2000 characters or less")

        if len(self.metadata.notes) > 2000:
            errors.append("Metadata notes must be 2000 characters or less")

        # Validate appearance
        appearance_errors = self.appearance.validate()
        for error in appearance_errors:
            errors.append(f"Appearance: {error}")

        # Validate references
        reference_errors = self.references.validate()
        for error in reference_errors:
            errors.append(f"References: {error}")

        return errors

    def validate_or_raise(self) -> None:
        """Validate the character and raise if invalid.

        Raises:
            CharacterValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise CharacterValidationError("Character validation failed", errors=errors)
