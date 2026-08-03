"""Keyframe representation."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InterpolationType(StrEnum):
    """Interpolation mode for keyframes."""

    STEP = "step"
    LINEAR = "linear"


class Keyframe(BaseModel):
    """Represents a single keyframe in an animation track.

    Supports generic values (numbers, strings, lists, dicts).
    """

    time: float = Field(ge=0.0)
    value: Any = Field(default=None)
    interpolation: InterpolationType = Field(default=InterpolationType.LINEAR)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _info: object) -> None:
        """Validate keyframe data."""
        if self.time < 0:
            raise ValueError("Keyframe time cannot be negative")

    def is_numeric(self) -> bool:
        """Check if the keyframe value is numeric."""
        return isinstance(self.value, (int, float))

    def interpolate_to(self, other: "Keyframe", t: float) -> Any:
        """Interpolate to another keyframe.

        Args:
            other: Target keyframe.
            t: Normalized time (0.0 to 1.0).

        Returns:
            Interpolated value.

        Raises:
            ValueError: If t is out of range or values are not compatible.
        """
        if not (0.0 <= t <= 1.0):
            raise ValueError("Interpolation parameter t must be between 0.0 and 1.0")

        if self.interpolation == InterpolationType.STEP:
            return self.value

        # LINEAR interpolation
        if self.is_numeric() and other.is_numeric():
            return self.value + (other.value - self.value) * t

        # For non-numeric values, return step (hold)
        return self.value

    def __lt__(self, other: "Keyframe") -> bool:
        """Compare keyframes by time for sorting."""
        return self.time < other.time

    def __eq__(self, other: object) -> bool:
        """Check equality based on time and value."""
        if not isinstance(other, Keyframe):
            return NotImplemented
        return self.time == other.time and self.value == other.value
