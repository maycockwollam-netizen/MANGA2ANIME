"""Transform representation for scene objects."""

from typing import Any

from pydantic import BaseModel, Field


class Vector2(BaseModel):
    """2D vector for position/scale."""

    x: float = 0.0
    y: float = 0.0

    def model_post_init(self, _info: Any) -> None:
        """Validate vector components."""
        if self.x != self.x or self.y != self.y:  # Check for NaN
            raise ValueError("Vector components cannot be NaN")


class Vector3(BaseModel):
    """3D vector for position/scale."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def model_post_init(self, _info: Any) -> None:
        """Validate vector components."""
        if self.x != self.x or self.y != self.y or self.z != self.z:  # Check for NaN
            raise ValueError("Vector components cannot be NaN")

    def to_vector2(self) -> Vector2:
        """Convert to Vector2 (x, y only)."""
        return Vector2(x=self.x, y=self.y)


class EulerRotation(BaseModel):
    """Euler rotation representation."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def model_post_init(self, _info: Any) -> None:
        """Validate rotation components."""
        if self.x != self.x or self.y != self.y or self.z != self.z:
            raise ValueError("Rotation components cannot be NaN")


class Transform(BaseModel):
    """Transform representation for scene objects.

    Supports both 2D and 3D workflows with extensible design.
    """

    position: Vector3 = Field(default_factory=Vector3)
    rotation: EulerRotation = Field(default_factory=EulerRotation)
    scale: Vector3 = Field(default_factory=lambda: Vector3(x=1.0, y=1.0, z=1.0))

    def model_post_init(self, _info: Any) -> None:
        """Validate transform data."""
        # Validate scale is not zero
        if self.scale.x == 0 or self.scale.y == 0 or self.scale.z == 0:
            raise ValueError("Scale components cannot be zero")

    def is_2d(self) -> bool:
        """Check if transform is effectively 2D (z=0)."""
        return self.position.z == 0.0 and self.rotation.x == 0.0 and self.rotation.y == 0.0
