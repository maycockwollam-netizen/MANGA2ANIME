"""VFX data models V1.

Pure data contracts for visual effects applied to rendered frames.
No execution, rendering, or image processing beyond configuration description.

Scope:
    This module defines the configuration and result contracts for VFX effects.
    It does NOT implement effect rendering logic (see concrete_effect.py) nor
    depend on runtime.animation internals.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class SpeedLineDirection(StrEnum):
    """Direction of speed line emanation from the focal point.

    Enum values are lowercase for consistency with project conventions.
    """

    RADIAL = "radial"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class SpeedLinesConfig(BaseModel):
    """Configuration for the speed lines VFX effect.

    Represents the parameters of the basic speed-lines effect without
    executing it. Speed lines are radiating lines drawn from a focal point
    toward the canvas edges, a staple manga/anime motion cue.

    Attributes:
        line_count: Number of speed lines to draw. Must be >= 0.
        line_length: Length of each line in pixels. Must be >= 0.
        line_thickness: Thickness of each line in pixels. Must be >= 1.
        line_color: RGBA tuple for line color (0-255 per channel).
        focal_x: Normalized focal point X (0.0 = left, 1.0 = right).
        focal_y: Normalized focal point Y (0.0 = top, 1.0 = bottom).
        direction: Emanation direction of the lines.
        intensity: Opacity multiplier applied to lines (0.0-1.0).
        seed: Deterministic seed for reproducible line placement.

    Invariant: focal_x and focal_y must be within [0.0, 1.0]. The combination
    of line_count and line_length should leave enough canvas space to render
    visible lines; this is not enforced at the model level because canvas
    dimensions are only known at render time.
    """

    line_count: int = Field(default=64, ge=0, description="Number of speed lines")
    line_length: int = Field(default=120, ge=0, description="Line length in pixels")
    line_thickness: int = Field(default=2, ge=1, description="Line thickness in pixels")
    line_color: tuple[int, int, int, int] = Field(
        default=(0, 0, 0, 255),
        description="RGBA line color (0-255 per channel)",
    )
    focal_x: float = Field(default=0.5, ge=0.0, le=1.0, description="Normalized focal X (0-1)")
    focal_y: float = Field(default=0.5, ge=0.0, le=1.0, description="Normalized focal Y (0-1)")
    direction: SpeedLineDirection = Field(
        default=SpeedLineDirection.RADIAL,
        description="Line emanation direction",
    )
    intensity: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity multiplier (0-1)")
    seed: int = Field(default=0, ge=0, description="Deterministic seed for placement")

    @field_validator("line_color", mode="before")
    @classmethod
    def validate_line_color(cls, v: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Validate line color is a 4-tuple of ints in 0-255 range."""
        if not isinstance(v, (tuple, list)) or len(v) != 4:
            raise ValueError("line_color must be a 4-element tuple/list (RGBA)")
        channels = []
        for c in v:
            if not isinstance(c, int) or isinstance(c, bool):
                raise ValueError(f"line_color channels must be int, got {type(c).__name__}")
            if not (0 <= c <= 255):
                raise ValueError(f"line_color channel {c} out of range 0-255")
            channels.append(c)
        return (channels[0], channels[1], channels[2], channels[3])

    @model_validator(mode="after")
    def validate_intensity_consistency(self) -> SpeedLinesConfig:
        """Validate intensity produces a meaningful alpha.

        When intensity is 0.0 the lines are fully transparent; this is allowed
        (it disables the effect) but the line_color alpha is kept as-is. No
        transformation is applied here — the renderer combines intensity with
        alpha at draw time.
        """
        return self


class VfxResult(BaseModel):
    """Result of applying a VFX effect.

    Pure data contract describing the output of an effect application.
    Does not hold the image bytes themselves; the path points to the artifact.

    Attributes:
        effect_name: Name of the effect that produced this result.
        output_path: Path to the rendered output image (RGBA PNG).
        canvas_size: (width, height) of the output image in pixels.
        applied: Whether the effect was actually applied (False for no-op).
    """

    model_config = {"frozen": True}

    effect_name: str = Field(min_length=1, description="Name of the effect")
    output_path: Path = Field(description="Path to the rendered output image")
    canvas_size: tuple[int, int] = Field(description="Output image (width, height)")
    applied: bool = Field(default=True, description="Whether the effect was applied")


__all__ = [
    "SpeedLineDirection",
    "SpeedLinesConfig",
    "VfxResult",
]
