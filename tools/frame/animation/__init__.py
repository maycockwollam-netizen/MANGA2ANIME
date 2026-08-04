"""Frame animation module V1.

Pure, deterministic animation/timeline layer for the frame system.
Describes how frames are generated over time without rendering images.

This module does NOT:
- Perform image manipulation
- Execute rendering
- Access GPU
- Perform I/O operations
- Process audio
- Use AI/LLM
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator, model_validator

from tools.frame.models import FrameTransform, InterpolationType

# Default frame rate constant
DEFAULT_FRAME_RATE = 24.0


class AnimationKeyframe(BaseModel):
    """Represents a transform state at a specific frame.

    Attributes:
        frame_index: The frame number where this keyframe applies (>= 0)
        transform: The transform state at this frame
        interpolation: How to interpolate from previous keyframe (default: LINEAR)
    """

    model_config = {"frozen": True}

    frame_index: int = Field(ge=0, description="Frame index (>= 0)")
    transform: FrameTransform = Field(description="Transform state at this frame")
    interpolation: InterpolationType = Field(
        default=InterpolationType.LINEAR,
        description="Interpolation type to next keyframe",
    )

    @property
    def position_x(self) -> float | None:
        """Get position X from transform."""
        return self.transform.position_x

    @property
    def position_y(self) -> float | None:
        """Get position Y from transform."""
        return self.transform.position_y

    @property
    def scale(self) -> float | None:
        """Get scale from transform."""
        return self.transform.scale

    @property
    def rotation_deg(self) -> float | None:
        """Get rotation from transform."""
        return self.transform.rotation_deg

    @property
    def opacity(self) -> float | None:
        """Get opacity from transform."""
        return self.transform.opacity


@dataclass(frozen=True, slots=True)
class AnimationFrame:
    """Evaluated animation state at a specific frame.

    Immutable result containing the computed transform at a frame.

    Attributes:
        frame_index: The frame number
        timestamp_ms: Timestamp in milliseconds from animation start
        transform: The evaluated transform at this frame
        clip_id: Identifier of the source animation clip
    """

    frame_index: int
    timestamp_ms: int
    transform: FrameTransform
    clip_id: str | None = None

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "transform": self.transform.model_dump(),
            "clip_id": self.clip_id,
        }


class AnimationClip(BaseModel):
    """Represents animation for one layer/object.

    Contains keyframes that define the animation over a frame range.

    Attributes:
        clip_id: Unique identifier for this clip
        start_frame: First frame of the clip (inclusive)
        end_frame: Last frame of the clip (inclusive)
        keyframes: Ordered list of keyframes
        default_transform: Transform to use before first keyframe
    """

    clip_id: str = Field(min_length=1, description="Unique clip identifier")
    start_frame: int = Field(ge=0, description="Start frame (inclusive)")
    end_frame: int = Field(ge=0, description="End frame (inclusive)")
    keyframes: list[AnimationKeyframe] = Field(default_factory=list, description="Keyframes")
    default_transform: FrameTransform = Field(
        default_factory=FrameTransform,
        description="Transform before first keyframe",
    )

    @field_validator("clip_id", mode="before")
    @classmethod
    def validate_clip_id(cls, v: str) -> str:
        """Validate and normalize clip ID."""
        if not isinstance(v, str):
            raise ValueError(f"clip_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("clip_id cannot be empty or whitespace-only")
        return stripped

    @model_validator(mode="after")
    def validate_frame_range(self) -> AnimationClip:
        """Validate frame range and keyframes."""
        if self.end_frame < self.start_frame:
            raise ValueError("end_frame must be >= start_frame")

        if self.keyframes:
            # Check keyframes are ordered and within range
            prev_index = -1
            seen_indexes: set[int] = set()

            for kf in self.keyframes:
                if kf.frame_index < self.start_frame or kf.frame_index > self.end_frame:
                    raise ValueError(
                        f"keyframe frame_index {kf.frame_index} must be within "
                        f"[{self.start_frame}, {self.end_frame}]"
                    )
                if kf.frame_index <= prev_index:
                    raise ValueError("keyframes must be ordered by frame_index")
                if kf.frame_index in seen_indexes:
                    raise ValueError(f"duplicate keyframe at frame_index {kf.frame_index}")
                prev_index = kf.frame_index
                seen_indexes.add(kf.frame_index)

        return self


class AnimationTimeline(BaseModel):
    """Timeline for animation with configurable frame rate.

    Manages frame/time conversion and animation clip evaluation.

    Attributes:
        frame_rate: Frames per second (default: 24.0)
        duration_frames: Total duration in frames
    """

    model_config = {"frozen": True}

    frame_rate: float = Field(default=DEFAULT_FRAME_RATE, gt=0, le=120, description="Frames per second")
    duration_frames: int = Field(ge=0, description="Total duration in frames")

    def frame_time(self, frame_index: int) -> float:
        """Calculate timestamp in seconds for a frame.

        Args:
            frame_index: Frame number

        Returns:
            Timestamp in seconds from animation start

        Raises:
            ValueError: If frame_index is out of range
        """
        if frame_index < 0 or frame_index > self.duration_frames:
            raise ValueError(f"frame_index {frame_index} out of range [0, {self.duration_frames}]")
        return frame_index / self.frame_rate

    def frame_time_ms(self, frame_index: int) -> int:
        """Calculate timestamp in milliseconds for a frame.

        Args:
            frame_index: Frame number

        Returns:
            Timestamp in milliseconds (rounded)
        """
        return int(round(self.frame_time(frame_index) * 1000))

    def frame_index_at(self, timestamp_seconds: float) -> int:
        """Calculate frame index for a timestamp.

        Args:
            timestamp_seconds: Time in seconds

        Returns:
            Frame index (rounded to nearest)

        Raises:
            ValueError: If timestamp is out of range
        """
        if timestamp_seconds < 0:
            raise ValueError(f"timestamp {timestamp_seconds} cannot be negative")
        frame = int(round(timestamp_seconds * self.frame_rate))
        return min(frame, self.duration_frames)

    def duration_seconds(self) -> float:
        """Calculate total duration in seconds."""
        return self.duration_frames / self.frame_rate

    def duration_ms(self) -> int:
        """Calculate total duration in milliseconds."""
        return int(round(self.duration_seconds() * 1000))


def _get_interpolator():
    """Lazy import to avoid circular dependency."""
    from tools.frame.transforms import interpolate_transform as _interp
    return _interp


def evaluate_keyframe_at_frame(
    clip: AnimationClip,
    frame_index: int,
    timeline: AnimationTimeline,
) -> FrameTransform:
    """Evaluate the transform at a specific frame.

    If frame_index matches a keyframe exactly, returns that keyframe's transform.
    Otherwise, interpolates between adjacent keyframes.

    Args:
        clip: Animation clip to evaluate
        frame_index: Frame to evaluate
        timeline: Timeline for reference

    Returns:
        Evaluated FrameTransform at the frame

    Raises:
        ValueError: If frame_index is out of clip range
    """
    if frame_index < clip.start_frame or frame_index > clip.end_frame:
        raise ValueError(
            f"frame_index {frame_index} out of clip range [{clip.start_frame}, {clip.end_frame}]"
        )

    if not clip.keyframes:
        return clip.default_transform

    # Find surrounding keyframes
    prev_kf: AnimationKeyframe | None = None
    next_kf: AnimationKeyframe | None = None

    for kf in clip.keyframes:
        if kf.frame_index <= frame_index:
            prev_kf = kf
        if kf.frame_index >= frame_index and next_kf is None:
            next_kf = kf
            break

    # Case 1: At or before first keyframe
    if prev_kf is None or prev_kf.frame_index == frame_index:
        return prev_kf.transform if prev_kf else clip.default_transform

    # Case 2: At last keyframe
    if next_kf is None:
        return clip.keyframes[-1].transform

    # Case 3: Between keyframes - interpolate
    interpolate_transform = _get_interpolator()

    # Calculate interpolation parameter t
    span = next_kf.frame_index - prev_kf.frame_index
    if span == 0:
        return prev_kf.transform

    t = (frame_index - prev_kf.frame_index) / span

    # Linear interpolation only supported in V1
    if next_kf.interpolation != InterpolationType.LINEAR:
        raise ValueError(
            f"Only LINEAR interpolation is supported in V1, "
            f"got {next_kf.interpolation}"
        )

    return interpolate_transform(prev_kf.transform, next_kf.transform, t)


def generate_animation_frames(
    clip: AnimationClip,
    timeline: AnimationTimeline,
) -> list[AnimationFrame]:
    """Generate all animation frames for a clip.

    Evaluates the transform at each frame in the clip's range.

    Args:
        clip: Animation clip to evaluate
        timeline: Timeline for frame/time calculations

    Returns:
        List of AnimationFrame results for each frame in the clip

    Raises:
        ValueError: If clip extends beyond timeline
    """
    if clip.end_frame > timeline.duration_frames:
        raise ValueError(
            f"clip end_frame {clip.end_frame} exceeds timeline "
            f"duration {timeline.duration_frames}"
        )

    frames: list[AnimationFrame] = []

    for frame_index in range(clip.start_frame, clip.end_frame + 1):
        transform = evaluate_keyframe_at_frame(clip, frame_index, timeline)
        timestamp_ms = timeline.frame_time_ms(frame_index)

        frames.append(
            AnimationFrame(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                transform=transform,
                clip_id=clip.clip_id,
            )
        )

    return frames


def evaluate_at_frame(
    clips: list[AnimationClip],
    frame_index: int,
    timeline: AnimationTimeline,
) -> list[AnimationFrame]:
    """Evaluate multiple clips at a specific frame.

    Useful for evaluating all layers at once.

    Args:
        clips: List of animation clips
        frame_index: Frame to evaluate
        timeline: Timeline for reference

    Returns:
        List of AnimationFrame results for all clips at the frame
    """
    results: list[AnimationFrame] = []

    for clip in clips:
        if clip.start_frame <= frame_index <= clip.end_frame:
            transform = evaluate_keyframe_at_frame(clip, frame_index, timeline)
            timestamp_ms = timeline.frame_time_ms(frame_index)

            results.append(
                AnimationFrame(
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                    transform=transform,
                    clip_id=clip.clip_id,
                )
            )

    return results


__all__ = [
    "DEFAULT_FRAME_RATE",
    "AnimationClip",
    "AnimationFrame",
    "AnimationKeyframe",
    "AnimationTimeline",
    "evaluate_keyframe_at_frame",
    "evaluate_at_frame",
    "generate_animation_frames",
]
