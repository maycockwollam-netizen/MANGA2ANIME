"""Scene object representation."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.scene.transform import Transform


class ObjectMetadata(BaseModel):
    """Metadata for a scene object."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SceneObject(BaseModel):
    """Generic scene object representation.

    Can represent any object in a scene: background, character parts,
    effects, lights, etc. Specialized objects will be defined in
    future modules.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="", max_length=255)
    object_type: str = Field(default="generic", max_length=100)
    transform: Transform = Field(default_factory=Transform)
    parent_id: str | None = Field(default=None)
    visible: bool = Field(default=True)
    enabled: bool = Field(default=True)
    metadata: ObjectMetadata = Field(default_factory=ObjectMetadata)
    custom_data: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _info: Any) -> None:
        """Validate object data."""
        if self.parent_id == self.id:
            raise ValueError("Object cannot be its own parent")

    def update_transform(
        self,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: tuple[float, float, float] | None = None,
    ) -> None:
        """Update transform components."""
        if position is not None:
            self.transform.position.x = position[0]
            self.transform.position.y = position[1]
            self.transform.position.z = position[2]

        if rotation is not None:
            self.transform.rotation.x = rotation[0]
            self.transform.rotation.y = rotation[1]
            self.transform.rotation.z = rotation[2]

        if scale is not None:
            self.transform.scale.x = scale[0]
            self.transform.scale.y = scale[1]
            self.transform.scale.z = scale[2]

        self.metadata.updated_at = datetime.now(UTC)

    def set_parent(self, parent_id: str | None) -> None:
        """Set the parent object ID."""
        if parent_id == self.id:
            raise ValueError("Object cannot be its own parent")
        self.parent_id = parent_id
        self.metadata.updated_at = datetime.now(UTC)

    def remove_parent(self) -> None:
        """Remove the parent reference."""
        self.parent_id = None
        self.metadata.updated_at = datetime.now(UTC)
