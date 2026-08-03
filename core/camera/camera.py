"""Camera model and camera configuration."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.camera.exceptions import CameraValidationError


class ProjectionType(StrEnum):
    """Camera projection type."""

    ORTHOGRAPHIC = "orthographic"
    PERSPECTIVE = "perspective"


class CameraMetadata(BaseModel):
    """Metadata for a camera."""

    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class CameraState(BaseModel):
    """Basic camera state representation."""

    enabled: bool = Field(default=True)
    active: bool = Field(default=False)
    custom_state: dict[str, Any] = Field(default_factory=dict)


class CameraTransform(BaseModel):
    """Camera transform data.

    Supports both 2D and 3D workflows.
    """

    position_x: float = Field(default=0.0)
    position_y: float = Field(default=0.0)
    position_z: float = Field(default=0.0)
    rotation_x: float = Field(default=0.0)
    rotation_y: float = Field(default=0.0)
    rotation_z: float = Field(default=0.0)

    def is_2d(self) -> bool:
        """Check if transform is effectively 2D.

        Returns:
            True if Z position is zero and no rotation around Z.
        """
        return self.position_z == 0.0 and self.rotation_x == 0.0 and self.rotation_y == 0.0

    def validate(self) -> list[str]:
        """Validate transform values.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        # Values can be any float, no specific range constraints
        return errors


class OrthographicProjection(BaseModel):
    """Orthographic projection configuration."""

    size: float = Field(default=5.0, gt=0.0)

    def validate(self) -> list[str]:
        """Validate orthographic settings.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if self.size <= 0:
            errors.append("Orthographic size must be positive")
        return errors


class PerspectiveProjection(BaseModel):
    """Perspective projection configuration."""

    field_of_view: float = Field(default=60.0, gt=0.0, lt=180.0)
    near_clip: float = Field(default=0.1, gt=0.0)
    far_clip: float = Field(default=1000.0, gt=0.0)

    def model_post_init(self, _info: object) -> None:
        """Validate perspective settings."""
        if self.near_clip <= 0:
            raise ValueError("Near clip must be positive")
        if self.far_clip <= self.near_clip:
            raise ValueError("Far clip must be greater than near clip")

    def validate(self) -> list[str]:
        """Validate perspective settings.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if not (0 < self.field_of_view < 180):
            errors.append("Field of view must be between 0 and 180 degrees")
        if self.near_clip <= 0:
            errors.append("Near clip must be positive")
        if self.far_clip <= self.near_clip:
            errors.append("Far clip must be greater than near clip")
        return errors


class Projection(BaseModel):
    """Camera projection configuration."""

    type: ProjectionType = Field(default=ProjectionType.PERSPECTIVE)
    orthographic: OrthographicProjection = Field(default_factory=OrthographicProjection)
    perspective: PerspectiveProjection = Field(default_factory=PerspectiveProjection)

    def validate(self) -> list[str]:
        """Validate projection configuration.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if self.type == ProjectionType.ORTHOGRAPHIC:
            errors.extend(self.orthographic.validate())
        elif self.type == ProjectionType.PERSPECTIVE:
            errors.extend(self.perspective.validate())

        return errors


class Viewport(BaseModel):
    """Viewport configuration."""

    width: int = Field(default=1920, gt=0)
    height: int = Field(default=1080, gt=0)

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width / height).

        Returns:
            Aspect ratio as float.
        """
        return self.width / self.height if self.height > 0 else 1.0

    def validate(self) -> list[str]:
        """Validate viewport dimensions.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if self.width <= 0:
            errors.append("Viewport width must be positive")
        if self.height <= 0:
            errors.append("Viewport height must be positive")
        return errors


class Framing(BaseModel):
    """Generic framing configuration."""

    center_x: float = Field(default=0.0)
    center_y: float = Field(default=0.0)
    size_width: float = Field(default=1.0, gt=0.0)
    size_height: float = Field(default=1.0, gt=0.0)
    zoom: float = Field(default=1.0, gt=0.0)
    margin_left: float = Field(default=0.0, ge=0.0)
    margin_right: float = Field(default=0.0, ge=0.0)
    margin_top: float = Field(default=0.0, ge=0.0)
    margin_bottom: float = Field(default=0.0, ge=0.0)

    def validate(self) -> list[str]:
        """Validate framing configuration.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if self.size_width <= 0:
            errors.append("Framing width must be positive")
        if self.size_height <= 0:
            errors.append("Framing height must be positive")
        if self.zoom <= 0:
            errors.append("Zoom must be positive")
        if self.margin_left < 0 or self.margin_right < 0:
            errors.append("Margins cannot be negative")
        if self.margin_top < 0 or self.margin_bottom < 0:
            errors.append("Margins cannot be negative")
        return errors


class CameraReferences(BaseModel):
    """Lightweight references to external resources."""

    scene_id: str = Field(default="")
    target_id: str = Field(default="")
    custom_references: dict[str, str] = Field(default_factory=dict)

    def get_scene_reference(self) -> str | None:
        """Get scene ID if set.

        Returns:
            Scene ID or None.
        """
        return self.scene_id if self.scene_id else None

    def get_target_reference(self) -> str | None:
        """Get target ID if set.

        Returns:
            Target ID or None.
        """
        return self.target_id if self.target_id else None

    def set_scene_reference(self, scene_id: str) -> None:
        """Set scene reference.

        Args:
            scene_id: Scene identifier.
        """
        self.scene_id = scene_id

    def set_target_reference(self, target_id: str) -> None:
        """Set target reference.

        Args:
            target_id: Target identifier.
        """
        self.target_id = target_id

    def validate(self) -> list[str]:
        """Validate references.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        if self.scene_id and len(self.scene_id) > 255:
            errors.append("scene_id must be 255 characters or less")
        if self.target_id and len(self.target_id) > 255:
            errors.append("target_id must be 255 characters or less")
        for key, value in self.custom_references.items():
            if not key or len(key) > 255:
                errors.append(f"Invalid reference key: '{key}'")
            if len(value) > 255:
                errors.append(f"Reference '{key}' must be 255 characters or less")
        return errors


class Camera(BaseModel):
    """Main camera model.

    Represents a camera in the Manga2Anime system.
    Does not handle rendering, GPU interaction, or camera animation.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="", max_length=255)
    metadata: CameraMetadata = Field(default_factory=CameraMetadata)
    transform: CameraTransform = Field(default_factory=CameraTransform)
    projection: Projection = Field(default_factory=Projection)
    viewport: Viewport = Field(default_factory=Viewport)
    framing: Framing = Field(default_factory=Framing)
    state: CameraState = Field(default_factory=CameraState)
    references: CameraReferences = Field(default_factory=CameraReferences)

    def model_post_init(self, _info: object) -> None:
        """Validate camera state."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid camera state: {errors}")

    def update_name(self, name: str) -> None:
        """Update camera name.

        Args:
            name: New name.
        """
        if len(name) > 255:
            raise ValueError("Name must be 255 characters or less")
        self.name = name
        self.metadata.updated_at = datetime.now(UTC)

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state.

        Args:
            enabled: Enabled state.
        """
        self.state.enabled = enabled
        self.metadata.updated_at = datetime.now(UTC)

    def set_active(self, active: bool) -> None:
        """Set active state.

        Args:
            active: Active state.
        """
        self.state.active = active
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
        """Check if camera has a tag.

        Args:
            tag: Tag to check.

        Returns:
            True if tag exists, False otherwise.
        """
        return tag in self.metadata.tags

    def set_projection_type(self, projection_type: ProjectionType) -> None:
        """Set projection type.

        Args:
            projection_type: New projection type.
        """
        self.projection.type = projection_type
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

    def set_target_reference(self, target_id: str) -> None:
        """Set target reference.

        Args:
            target_id: Target identifier.
        """
        self.references.set_target_reference(target_id)
        self.metadata.updated_at = datetime.now(UTC)

    def get_target_reference(self) -> str | None:
        """Get target reference.

        Returns:
            Target ID or None.
        """
        return self.references.get_target_reference()

    def validate(self) -> list[str]:
        """Validate the camera.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Camera ID is required")

        if len(self.name) > 255:
            errors.append("Name must be 255 characters or less")

        if len(self.metadata.description) > 2000:
            errors.append("Metadata description must be 2000 characters or less")

        if len(self.metadata.notes) > 2000:
            errors.append("Metadata notes must be 2000 characters or less")

        # Validate transform
        errors.extend(self.transform.validate())

        # Validate projection
        projection_errors = self.projection.validate()
        for error in projection_errors:
            errors.append(f"Projection: {error}")

        # Validate viewport
        viewport_errors = self.viewport.validate()
        for error in viewport_errors:
            errors.append(f"Viewport: {error}")

        # Validate framing
        framing_errors = self.framing.validate()
        for error in framing_errors:
            errors.append(f"Framing: {error}")

        # Validate references
        reference_errors = self.references.validate()
        for error in reference_errors:
            errors.append(f"References: {error}")

        return errors

    def validate_or_raise(self) -> None:
        """Validate the camera and raise if invalid.

        Raises:
            CameraValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise CameraValidationError("Camera validation failed", errors=errors)
