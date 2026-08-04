"""Frame tool data models V1.

Pure data contracts for the frame/animation pipeline.
No execution, rendering, or image processing.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class LayerType(StrEnum):
    """Types of frame layers.

    Enum values are lowercase for consistency with project conventions.
    """

    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"


class TransitionType(StrEnum):
    """Types of frame transitions.

    Represents transition metadata without execution.
    """

    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"


class InterpolationType(StrEnum):
    """Types of interpolation for animations.

    Represents interpolation metadata without execution.
    """

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class FrameTransform(BaseModel):
    """Data contract for frame/layer transform.

    Represents transform parameters without execution.
    Does not implement animation engine.

    Attributes:
        position_x: X position offset from origin
        position_y: Y position offset from origin
        scale: Scale factor (1.0 = original size)
        rotation_deg: Rotation in degrees (clockwise positive)
        opacity: Opacity from 0.0 (transparent) to 1.0 (opaque)
        anchor_x: Anchor/pivot X point (0-1 normalized)
        anchor_y: Anchor/pivot Y point (0-1 normalized)
    """

    position_x: float | None = Field(default=None, description="X position offset")
    position_y: float | None = Field(default=None, description="Y position offset")
    scale: float | None = Field(default=1.0, ge=0, description="Scale factor (default: 1.0)")
    rotation_deg: float | None = Field(default=0, description="Rotation in degrees (default: 0)")
    opacity: float | None = Field(default=1.0, ge=0, le=1, description="Opacity 0-1 (default: 1.0)")
    anchor_x: float | None = Field(default=0.5, ge=0, le=1, description="Anchor X point (default: 0.5)")
    anchor_y: float | None = Field(default=0.5, ge=0, le=1, description="Anchor Y point (default: 0.5)")

    @model_validator(mode="after")
    def validate_rotation(self) -> FrameTransform:
        """Validate rotation is finite."""
        if self.rotation_deg is not None and not (-360000 <= self.rotation_deg <= 360000):
            raise ValueError("rotation_deg must be a finite number (reasonable range: ±360000 degrees)")
        return self


class FrameLayer(BaseModel):
    """Represents a layer within a frame.

    Contains metadata about a layer type and source reference.
    Does not decode or manipulate image data.

    Attributes:
        layer_id: Unique identifier for this layer
        layer_type: Type of layer (background, character, foreground, effect)
        layer_index: Z-order index for layer stacking
        source_path: Optional path to layer source file
        transform: Optional transform data for this layer
        visible: Whether layer is visible (default: True)
    """

    layer_id: str | None = Field(default=None, description="Unique layer identifier")
    layer_type: LayerType = Field(description="Type of layer")
    layer_index: int = Field(ge=0, description="Layer order index (z-order)")
    source_path: Path | None = Field(default=None, description="Path to layer source")
    transform: FrameTransform | None = Field(default=None, description="Layer transform")
    visible: bool = Field(default=True, description="Layer visibility")

    @field_validator("layer_id", mode="before")
    @classmethod
    def validate_layer_id(cls, v: str | None) -> str | None:
        """Validate layer ID is non-empty if provided."""
        if v is None:
            return None
        if isinstance(v, str):
            stripped = v.strip()
            if stripped:
                return stripped
            raise ValueError("layer_id cannot be empty or whitespace-only")
        raise ValueError(f"layer_id must be string, got {type(v).__name__}")


class Frame(BaseModel):
    """Represents a frame in a timeline.

    Contains metadata about a single frame. Does not contain raw image data.
    Frame index uniquely identifies the frame in the sequence.

    Attributes:
        frame_index: Zero-based index for frame ordering
        timestamp_ms: Optional timestamp in milliseconds from sequence start
        duration_ms: Optional duration this frame is displayed
        layers: Ordered list of frame layers (bottom to top)
        source_path: Optional path to frame source
    """

    frame_index: int = Field(ge=0, description="Zero-based frame index")
    timestamp_ms: int | None = Field(default=None, ge=0, description="Timestamp in milliseconds")
    duration_ms: int | None = Field(default=None, ge=0, description="Duration in milliseconds")
    layers: list[FrameLayer] = Field(default_factory=list, description="Frame layers (bottom to top)")
    source_path: Path | None = Field(default=None, description="Path to frame source")

    @field_validator("timestamp_ms", "duration_ms", mode="before")
    @classmethod
    def validate_timing(cls, v: int | None) -> int | None:
        """Validate timing values are non-negative if provided."""
        if v is None:
            return None
        if not isinstance(v, int):
            raise ValueError(f"Timing value must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("Timing values cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_layer_ordering(self) -> Frame:
        """Validate layers have consistent ordering."""
        if self.layers:
            indices = [layer.layer_index for layer in self.layers]
            if indices != sorted(indices):
                raise ValueError("layers should be ordered by layer_index (bottom to top)")
        return self


class FrameTransition(BaseModel):
    """Data contract for transition between frames.

    Represents transition metadata without execution.
    Does not implement interpolation or rendering.

    Attributes:
        source_frame_index: Index of source frame
        target_frame_index: Index of target frame
        duration_ms: Transition duration in milliseconds
        transition_type: Type of transition (cut, fade, dissolve, etc.)
        interpolation: Optional interpolation type
    """

    source_frame_index: int = Field(ge=0, description="Source frame index")
    target_frame_index: int = Field(ge=0, description="Target frame index")
    duration_ms: int = Field(ge=0, description="Transition duration in milliseconds")
    transition_type: str | TransitionType = Field(default=TransitionType.CUT, description="Transition type")
    interpolation: InterpolationType | None = Field(default=None, description="Interpolation type")

    @field_validator("source_frame_index", "target_frame_index", mode="before")
    @classmethod
    def validate_frame_index(cls, v: int) -> int:
        """Validate frame index is non-negative."""
        if not isinstance(v, int):
            raise ValueError(f"frame_index must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("frame_index cannot be negative")
        return v

    @field_validator("transition_type", mode="before")
    @classmethod
    def normalize_transition_type(cls, v: str | TransitionType) -> str:
        """Normalize transition type to lowercase string."""
        if isinstance(v, TransitionType):
            return v.value
        if isinstance(v, str):
            return v.lower().strip()
        raise ValueError(f"transition_type must be string, got {type(v).__name__}")

    @model_validator(mode="after")
    def validate_different_frames(self) -> FrameTransition:
        """Validate source and target frames are different."""
        if self.source_frame_index == self.target_frame_index:
            raise ValueError("source_frame_index and target_frame_index must be different")
        return self


class FrameSequence(BaseModel):
    """Represents a sequence of frames with metadata.

    Pure data contract for frame sequences.
    Does not perform playback or rendering.

    Attributes:
        sequence_id: Unique identifier for this sequence
        name: Human-readable name for the sequence
        frame_rate: Target frame rate in FPS (for timing calculations)
        frames: Ordered list of frames in the sequence
        transitions: Optional list of transitions between frames
    """

    model_config = {"frozen": True}

    sequence_id: str = Field(min_length=1, description="Unique sequence identifier")
    name: str | None = Field(default=None, description="Human-readable sequence name")
    frame_rate: float = Field(default=24.0, gt=0, le=120, description="Frame rate in FPS")
    frames: list[Frame] = Field(default_factory=list, description="Ordered frames")
    transitions: list[FrameTransition] = Field(default_factory=list, description="Transitions")

    @field_validator("sequence_id", mode="before")
    @classmethod
    def validate_sequence_id(cls, v: str) -> str:
        """Validate sequence ID is non-empty and trimmed."""
        if not isinstance(v, str):
            raise ValueError(f"sequence_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("sequence_id cannot be empty or whitespace-only")
        return stripped


__all__ = [
    "Frame",
    "FrameLayer",
    "FrameSequence",
    "FrameTransform",
    "FrameTransition",
    "InterpolationType",
    "LayerType",
    "TransitionType",
]
