"""Frame timeline mapping.

Provides deterministic timestamp <-> frame index mapping for rendered sequences.

This module creates an immutable timeline abstraction that maps frame indices
to timestamps and vice versa using constant frame-rate semantics.

Architecture:
    RenderSequenceManifest / RenderPreview
        ↓
    FrameTimeline

This module does NOT:
- Modify files
- Access animation runtime
- Implement playback threads
- Encode video
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from tools.render.preview import RenderPreview


class TimelineError(Exception):
    """Error working with frame timeline mapping.

    Raised when timeline operations fail (invalid frame index, timestamp, etc.).
    """

    pass


@dataclass(frozen=True)
class FrameTimeline:
    """Immutable timeline mapping frame indices to timestamps.

    Uses deterministic constant frame-rate semantics for mapping.

    Attributes:
        frame_indices: Sorted tuple of frame indices in the sequence.
        frame_rate: Frame rate in frames per second (always positive).
        duration_seconds: Total duration of the sequence.
    """

    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float

    def __post_init__(self) -> None:
        """Validate timeline parameters."""
        if not self.frame_indices:
            raise TimelineError("frame_indices cannot be empty")

        if len(self.frame_indices) != len(set(self.frame_indices)):
            raise TimelineError("frame_indices must be unique")

        if self.frame_rate <= 0:
            raise TimelineError(
                f"frame_rate must be positive, got {self.frame_rate}"
            )

        if math.isnan(self.frame_rate):
            raise TimelineError("frame_rate cannot be NaN")

        if math.isinf(self.frame_rate):
            raise TimelineError("frame_rate cannot be infinite")

        if self.duration_seconds < 0:
            raise TimelineError(
                f"duration_seconds cannot be negative, got {self.duration_seconds}"
            )

        if math.isnan(self.duration_seconds):
            raise TimelineError("duration_seconds cannot be NaN")

        if math.isinf(self.duration_seconds):
            raise TimelineError("duration_seconds cannot be infinite")

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sequence."""
        return len(self.frame_indices)

    @property
    def frame_duration(self) -> float:
        """Duration of a single frame in seconds (1 / frame_rate)."""
        return 1.0 / self.frame_rate

    @property
    def start_timestamp(self) -> float:
        """Timestamp of the first frame (always 0.0)."""
        return 0.0

    @property
    def end_timestamp(self) -> float:
        """Timestamp just after the last frame.

        This is the timestamp at which the sequence ends, not the
        timestamp of the last frame itself.
        """
        return self.duration_seconds

    def timestamp_for_frame(self, frame_index: int) -> float:
        """Get the timestamp for a specific frame index.

        Args:
            frame_index: The frame index to look up.

        Returns:
            Timestamp in seconds from the start of the sequence.

        Raises:
            TimelineError: If frame_index is not in the sequence.
        """
        if frame_index not in self.frame_indices:
            raise TimelineError(
                f"Frame index {frame_index} not found in timeline. "
                f"Available: {self.frame_indices}"
            )

        position = self.frame_position(frame_index)
        return position * self.frame_duration

    def frame_for_timestamp(self, timestamp: float) -> int:
        """Get the frame index for a specific timestamp.

        Uses floor(timestamp * frame_rate) to map timestamps to frames.
        This provides deterministic behavior at frame boundaries.

        Args:
            timestamp: Timestamp in seconds from sequence start.

        Returns:
            Frame index at the given timestamp.

        Raises:
            TimelineError: If timestamp is negative or beyond sequence duration.
        """
        if timestamp < 0:
            raise TimelineError(
                f"timestamp cannot be negative, got {timestamp}"
            )

        if timestamp > self.duration_seconds:
            raise TimelineError(
                f"timestamp {timestamp} exceeds sequence duration {self.duration_seconds}"
            )

        # Use floor to map timestamp to frame position
        position = math.floor(timestamp * self.frame_rate)

        # Clamp position to valid range
        position = max(0, min(position, self.frame_count - 1))

        return self.frame_indices[position]

    def frame_position(self, frame_index: int) -> int:
        """Get the zero-based position of a frame index in the sequence.

        Args:
            frame_index: The frame index to look up.

        Returns:
            Zero-based position (0 for first frame, 1 for second, etc.).

        Raises:
            TimelineError: If frame_index is not in the sequence.
        """
        if frame_index not in self.frame_indices:
            raise TimelineError(
                f"Frame index {frame_index} not found in timeline. "
                f"Available: {self.frame_indices}"
            )

        return self.frame_indices.index(frame_index)


def create_frame_timeline(
    frame_indices: Iterable[int],
    *,
    frame_rate: float = 24.0,
    duration_seconds: float | None = None,
) -> FrameTimeline:
    """Create a deterministic frame timeline.

    Args:
        frame_indices: Iterable of frame indices (will be sorted and deduplicated).
        frame_rate: Frame rate in frames per second (default: 24.0).
            Must be positive and finite.
        duration_seconds: Optional explicit duration. If None, derived from
            frame_count / frame_rate.

    Returns:
        FrameTimeline with immutable, sorted frame indices.

    Raises:
        TimelineError: If parameters are invalid.

    Example:
        >>> timeline = create_frame_timeline([2, 0, 1], frame_rate=24.0)
        >>> timeline.frame_indices
        (0, 1, 2)
        >>> timeline.timestamp_for_frame(0)
        0.0
        >>> timeline.timestamp_for_frame(1)
        0.041666666666666664
    """
    # Convert to tuple and sort
    indices_tuple = tuple(sorted(frame_indices))

    # Validate frame_rate
    if frame_rate <= 0:
        raise TimelineError(
            f"frame_rate must be positive, got {frame_rate}"
        )
    if math.isnan(frame_rate):
        raise TimelineError("frame_rate cannot be NaN")
    if math.isinf(frame_rate):
        raise TimelineError("frame_rate cannot be infinite")

    # Derive or validate duration
    frame_count = len(indices_tuple)
    if duration_seconds is None:
        derived_duration = frame_count / frame_rate
    else:
        if duration_seconds < 0:
            raise TimelineError(
                f"duration_seconds cannot be negative, got {duration_seconds}"
            )
        if math.isnan(duration_seconds):
            raise TimelineError("duration_seconds cannot be NaN")
        if math.isinf(duration_seconds):
            raise TimelineError("duration_seconds cannot be infinite")
        derived_duration = duration_seconds

    return FrameTimeline(
        frame_indices=indices_tuple,
        frame_rate=frame_rate,
        duration_seconds=derived_duration,
    )


def create_frame_timeline_from_preview(
    preview: RenderPreview,
) -> FrameTimeline:
    """Create a frame timeline from an existing RenderPreview.

    Args:
        preview: The RenderPreview to create timeline from.

    Returns:
        FrameTimeline with frame indices and rate from preview.

    Example:
        >>> preview = create_render_preview("output", frame_rate=24.0)
        >>> timeline = create_frame_timeline_from_preview(preview)
    """
    return FrameTimeline(
        frame_indices=preview.frame_indices,
        frame_rate=preview.frame_rate,
        duration_seconds=preview.duration_seconds,
    )


__all__ = [
    "FrameTimeline",
    "TimelineError",
    "create_frame_timeline",
    "create_frame_timeline_from_preview",
]
