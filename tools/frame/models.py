"""Frame tool data models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class LayerType(StrEnum):
    """Types of frame layers."""

    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"


class Frame(BaseModel):
    """Represents a frame in a timeline.

    Contains metadata about a single frame. Does not contain raw image data.
    """

    frame_index: int = Field(ge=0, description="Zero-based frame index")
    timestamp_ms: int | None = Field(default=None, ge=0, description="Timestamp in milliseconds")
    duration_ms: int | None = Field(default=None, ge=0, description="Duration in milliseconds")
    layers: list[FrameLayer] = Field(default_factory=list, description="Frame layers")


class FrameLayer(BaseModel):
    """Represents a layer within a frame.

    Contains metadata about a layer type and source reference.
    Does not decode or manipulate image data.
    """

    layer_type: LayerType = Field(description="Type of layer")
    source_path: Path | None = Field(default=None, description="Path to layer source")
    layer_index: int = Field(ge=0, description="Layer order index")
    transform: FrameTransform | None = Field(default=None, description="Layer transform")


class FrameTransform(BaseModel):
    """Data contract for frame/layer transform.

    Represents transform parameters without execution.
    Does not implement animation engine.
    """

    position_x: float | None = Field(default=None, description="X position offset")
    position_y: float | None = Field(default=None, description="Y position offset")
    scale: float | None = Field(default=1.0, ge=0, description="Scale factor")
    rotation_deg: float | None = Field(default=0, description="Rotation in degrees")
    opacity: float | None = Field(default=1.0, ge=0, le=1, description="Opacity 0-1")


class FrameTransition(BaseModel):
    """Data contract for transition between frames.

    Represents transition metadata without execution.
    Does not implement interpolation or rendering.
    """

    source_frame_index: int = Field(ge=0, description="Source frame index")
    target_frame_index: int = Field(ge=0, description="Target frame index")
    duration_ms: int = Field(ge=0, description="Transition duration in milliseconds")
    transition_type: str = Field(default="cut", description="Transition type (cut, fade, dissolve, etc.)")
