"""Animation data models.

Defines the data contracts for camera animation without executing any
animation engine. These models describe the keyframes consumed by a camera
animator and the output format it produces.

This module does NOT:
- Implement interpolation (delegated to interpolation.py)
- Access GPU
- Execute rendering logic
- Depend on runtime.animation internals
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EasingType(StrEnum):
    """Easing function selector for keyframe interpolation.

    Members:
        LINEAR: Constant-speed interpolation between keyframes.
        EASE_IN_OUT: Smooth acceleration/deceleration using a cosine curve.
    """

    LINEAR = "linear"
    EASE_IN_OUT = "ease_in_out"


class CameraKeyframe(BaseModel):
    """A single camera keyframe on the animation timeline.

    Attributes:
        timestamp: Time in seconds (>= 0) when this keyframe occurs.
        zoom: Zoom factor (>= 0). 1.0 = no zoom, 2.0 = 2x zoom, 0.5 = zoom out.
            Maps directly to FrameTransform.scale.
        focus_x: Horizontal focus point normalized to [0, 1].
            Maps to FrameTransform.anchor_x.
        focus_y: Vertical focus point normalized to [0, 1].
            Maps to FrameTransform.anchor_y.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: float = Field(..., description="Time in seconds (>= 0)")
    zoom: float = Field(default=1.0, ge=0, description="Zoom factor (>= 0, default 1.0)")
    focus_x: float = Field(default=0.5, ge=0, le=1, description="Focus X in [0, 1] (default 0.5)")
    focus_y: float = Field(default=0.5, ge=0, le=1, description="Focus Y in [0, 1] (default 0.5)")

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, v: float) -> float:
        """Reject negative timestamps."""
        if v < 0:
            raise ValueError("timestamp must be >= 0")
        return v

    @model_validator(mode="after")
    def _validate_finite(self) -> CameraKeyframe:
        """Reject non-finite zoom values (NaN/inf)."""
        import math

        if math.isnan(self.zoom) or math.isinf(self.zoom):
            raise ValueError("zoom must be finite")
        return self


class AnimationConfig(BaseModel):
    """Configuration for a camera animation sequence.

    Attributes:
        keyframes: Ordered list of CameraKeyframe defining the camera path.
            Must contain at least one keyframe; timestamps must be
            non-decreasing. Duplicated timestamps are rejected.
        easing: Default easing type applied between consecutive keyframes.
        duration_seconds: Optional total duration hint. If None, inferred
            from the last keyframe's timestamp.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    keyframes: list[CameraKeyframe] = Field(
        default_factory=list, description="Ordered camera keyframes"
    )
    easing: EasingType = Field(default=EasingType.LINEAR, description="Default easing")
    duration_seconds: float | None = Field(
        default=None, ge=0, description="Optional total duration hint"
    )

    @field_validator("keyframes", mode="before")
    @classmethod
    def _coerce_keyframes(cls, v):
        """Coerce tuples to CameraKeyframe and accept empty input gracefully."""
        if v is None:
            return []
        coerced = []
        for kf in v:
            if isinstance(kf, CameraKeyframe):
                coerced.append(kf)
            elif isinstance(kf, dict):
                coerced.append(CameraKeyframe(**kf))
            else:
                raise ValueError(f"invalid keyframe entry: {kf!r}")
        return coerced

    @model_validator(mode="after")
    def _validate_keyframes(self) -> AnimationConfig:
        """Validate keyframe ordering and timestamps."""
        if len(self.keyframes) == 0:
            raise ValueError("AnimationConfig requires at least one keyframe")
        timestamps = [kf.timestamp for kf in self.keyframes]
        # Reject negative timestamps (defensive; CameraKeyframe already checks).
        if any(t < 0 for t in timestamps):
            raise ValueError("keyframe timestamps must be >= 0")
        # Require non-decreasing order.
        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i - 1]:
                raise ValueError(
                    "keyframe timestamps must be in non-decreasing order"
                )
        # Reject duplicate timestamps (degenerate interpolation interval).
        if len(set(timestamps)) != len(timestamps):
            raise ValueError("duplicate keyframe timestamps are not allowed")
        return self
