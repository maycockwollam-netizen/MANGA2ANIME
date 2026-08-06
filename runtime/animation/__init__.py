"""Runtime Animation Module.

Provides runtime execution for character animation evaluation.

This module bridges the gap between domain contracts (AnimationClip, FrameTransform)
and runtime execution (evaluation at specific frames).

Dependency direction:
    tools/manga_frame
            ↓
    tools/frame
            ↓
    runtime.animation  (THIS MODULE)

This module does NOT:
- Generate animation
- Create keyframes
- Interpolate transforms (delegates to tools/frame/animation)
- Render frames
- Access GPU
- Perform I/O operations
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.frame.animation import (
    AnimationClip,
    AnimationTimeline,
)
from tools.frame.animation import (
    evaluate_keyframe_at_frame as _evaluate,
)
from tools.frame.models import FrameTransform

# ============================================================================
# Exceptions
# ============================================================================


class AnimationRuntimeError(Exception):
    """Base exception for animation runtime errors."""

    pass


class ClipNotFoundError(AnimationRuntimeError):
    """Raised when a clip is not found in the runtime."""

    pass


class DuplicateClipError(AnimationRuntimeError):
    """Raised when attempting to register a clip with a duplicate ID."""

    pass


class InvalidFrameError(AnimationRuntimeError):
    """Raised when an invalid frame index is provided."""

    pass


class UnsupportedInterpolationError(AnimationRuntimeError):
    """Raised when attempting to use unsupported interpolation."""

    pass


# ============================================================================
# Runtime Contract
# ============================================================================


@dataclass(frozen=True)
class RuntimeAnimationState:
    """Immutable state for animation runtime.

    Attributes:
        sequence_id: Identifier for the animation sequence
        registered_clips: Number of clips currently registered
        frame_rate: Frame rate for time calculations
    """

    sequence_id: str
    registered_clips: int
    frame_rate: float


class AnimationRuntime:
    """Runtime for character animation evaluation.

    This runtime provides a deterministic, explicit interface for evaluating
    AnimationClip objects at specific frames.

    State Management:
        - Explicitly instantiated (not a singleton)
        - No global mutable state
        - Deterministic behavior

    Attributes:
        sequence_id: Identifier for this runtime instance
        frame_rate: Frame rate for time calculations

    Example:
        >>> runtime = AnimationRuntime(sequence_id="intro")
        >>> runtime.register(clip)
        >>> transform = runtime.evaluate("hero_1", 12)
    """

    def __init__(
        self,
        sequence_id: str,
        *,
        frame_rate: float = 24.0,
    ) -> None:
        """Initialize animation runtime.

        Args:
            sequence_id: Identifier for this runtime instance
            frame_rate: Frame rate for time calculations (default: 24.0)
        """
        if not sequence_id or not sequence_id.strip():
            raise ValueError("sequence_id cannot be empty")

        self._sequence_id = sequence_id.strip()
        self._frame_rate = frame_rate
        self._clips: dict[str, AnimationClip] = {}
        self._timeline = AnimationTimeline(
            frame_rate=frame_rate,
            duration_frames=0,  # Will be updated as clips are registered
        )

    @property
    def sequence_id(self) -> str:
        """Get the runtime sequence ID."""
        return self._sequence_id

    @property
    def frame_rate(self) -> float:
        """Get the frame rate."""
        return self._frame_rate

    @property
    def duration_frames(self) -> int:
        """Get the duration in frames from the timeline.

        Returns 0 if no clips are registered.
        """
        return self._timeline.duration_frames

    @property
    def state(self) -> RuntimeAnimationState:
        """Get immutable runtime state."""
        return RuntimeAnimationState(
            sequence_id=self._sequence_id,
            registered_clips=len(self._clips),
            frame_rate=self._frame_rate,
        )

    def register(self, clip: AnimationClip) -> AnimationClip:
        """Register an AnimationClip in the runtime.

        Args:
            clip: AnimationClip to register

        Returns:
            The registered clip

        Raises:
            DuplicateClipError: If clip_id already exists
        """
        if clip.clip_id in self._clips:
            raise DuplicateClipError(
                f"Clip with ID '{clip.clip_id}' already exists in runtime "
                f"for sequence '{self._sequence_id}'"
            )

        self._clips[clip.clip_id] = clip
        self._update_timeline_duration()
        return clip

    def register_many(self, clips: list[AnimationClip]) -> tuple[AnimationClip, ...]:
        """Register multiple AnimationClips.

        Args:
            clips: List of AnimationClips to register

        Returns:
            Tuple of registered clips

        Raises:
            DuplicateClipError: If any clip_id already exists
        """
        registered: list[AnimationClip] = []
        for clip in clips:
            if clip.clip_id in self._clips:
                raise DuplicateClipError(
                    f"Clip with ID '{clip.clip_id}' already exists"
                )
            self._clips[clip.clip_id] = clip
            registered.append(clip)

        self._update_timeline_duration()
        return tuple(registered)

    def get_clip(self, clip_id: str) -> AnimationClip:
        """Get a registered clip by ID.

        Args:
            clip_id: ID of clip to retrieve

        Returns:
            The AnimationClip

        Raises:
            ClipNotFoundError: If clip_id not found
        """
        if clip_id not in self._clips:
            raise ClipNotFoundError(
                f"Clip '{clip_id}' not found in runtime "
                f"for sequence '{self._sequence_id}'"
            )
        return self._clips[clip_id]

    def has_clip(self, clip_id: str) -> bool:
        """Check if a clip is registered.

        Args:
            clip_id: ID to check

        Returns:
            True if clip exists, False otherwise
        """
        return clip_id in self._clips

    def list_clips(self) -> list[AnimationClip]:
        """List all registered clips.

        Returns:
            List of AnimationClips sorted by clip_id
        """
        return sorted(self._clips.values(), key=lambda c: c.clip_id)

    def evaluate(self, clip_id: str, frame_index: int) -> FrameTransform:
        """Evaluate an animation clip at a specific frame.

        This method delegates to the existing evaluate_keyframe_at_frame()
        function from tools/frame/animation.

        Args:
            clip_id: ID of clip to evaluate
            frame_index: Frame index to evaluate at

        Returns:
            FrameTransform at the specified frame

        Raises:
            ClipNotFoundError: If clip_id not found
            InvalidFrameError: If frame_index is invalid
            UnsupportedInterpolationError: If non-LINEAR interpolation is used
        """
        clip = self.get_clip(clip_id)

        if frame_index < 0:
            raise InvalidFrameError(
                f"frame_index {frame_index} cannot be negative"
            )

        try:
            return _evaluate(clip, frame_index, self._timeline)
        except ValueError as e:
            error_msg = str(e)
            if "out of clip range" in error_msg:
                raise InvalidFrameError(error_msg) from e
            if "Only LINEAR interpolation is supported" in error_msg:
                raise UnsupportedInterpolationError(error_msg) from e
            raise

    def evaluate_at_frame(self, frame_index: int) -> dict[str, FrameTransform]:
        """Evaluate all active clips at a specific frame.

        Args:
            frame_index: Frame index to evaluate at

        Returns:
            Dictionary mapping clip_id to FrameTransform
        """
        if frame_index < 0:
            raise InvalidFrameError(
                f"frame_index {frame_index} cannot be negative"
            )

        results: dict[str, FrameTransform] = {}
        for clip_id, clip in self._clips.items():
            if clip.start_frame <= frame_index <= clip.end_frame:
                try:
                    results[clip_id] = _evaluate(clip, frame_index, self._timeline)
                except ValueError:
                    # Skip clips that fail evaluation (e.g., unsupported interpolation)
                    pass

        return results

    def get_clip_frame_range(self, clip_id: str) -> tuple[int, int]:
        """Get the frame range for a clip.

        Args:
            clip_id: ID of clip

        Returns:
            Tuple of (start_frame, end_frame)

        Raises:
            ClipNotFoundError: If clip_id not found
        """
        clip = self.get_clip(clip_id)
        return (clip.start_frame, clip.end_frame)

    def unregister(self, clip_id: str) -> AnimationClip:
        """Unregister a clip from the runtime.

        Args:
            clip_id: ID of clip to unregister

        Returns:
            The unregistered AnimationClip

        Raises:
            ClipNotFoundError: If clip_id not found
        """
        if clip_id not in self._clips:
            raise ClipNotFoundError(f"Clip '{clip_id}' not found")

        clip = self._clips.pop(clip_id)
        self._update_timeline_duration()
        return clip

    def replace(self, clip: AnimationClip) -> AnimationClip:
        """Replace an existing clip with a new one.

        Allows updating animation data for an existing clip_id.
        The replacement must have the same clip_id as the existing clip.

        Args:
            clip: Replacement AnimationClip (must have same clip_id)

        Returns:
            The new (replacement) AnimationClip

        Raises:
            ClipNotFoundError: If clip_id not found in runtime
            ValueError: If replacement clip has different clip_id
        """
        existing_clip_id = clip.clip_id
        if existing_clip_id not in self._clips:
            raise ClipNotFoundError(
                f"Clip '{existing_clip_id}' not found - cannot replace non-existent clip"
            )

        self._clips[existing_clip_id] = clip
        self._update_timeline_duration()
        return clip

    def replace_many(self, clips: list[AnimationClip]) -> tuple[AnimationClip, ...]:
        """Replace multiple clips atomically.

        All replacements must be valid (clip_id must exist).
        If any replacement is invalid, no changes are made.

        Args:
            clips: List of replacement AnimationClips

        Returns:
            Tuple of replacement AnimationClips

        Raises:
            ClipNotFoundError: If any clip_id not found in runtime
            ValueError: If any replacement clip has duplicate clip_ids
        """
        # Validate all clips first
        clip_ids = [c.clip_id for c in clips]
        seen: set[str] = set()

        for clip_id in clip_ids:
            if clip_id in seen:
                raise ValueError(
                    f"Replacement clips contain duplicate clip_id '{clip_id}'"
                )
            seen.add(clip_id)

            if clip_id not in self._clips:
                raise ClipNotFoundError(
                    f"Clip '{clip_id}' not found - cannot replace non-existent clip"
                )

        # Apply replacements
        for clip in clips:
            self._clips[clip.clip_id] = clip

        self._update_timeline_duration()
        return tuple(clips)

    def clear(self) -> None:
        """Remove all registered clips."""
        self._clips.clear()
        self._timeline = AnimationTimeline(
            frame_rate=self._frame_rate,
            duration_frames=0,
        )

    def count(self) -> int:
        """Get the number of registered clips.

        Returns:
            Number of registered clips
        """
        return len(self._clips)

    def __len__(self) -> int:
        """Get the number of registered clips."""
        return len(self._clips)

    def __contains__(self, clip_id: str) -> bool:
        """Check if a clip is registered."""
        return clip_id in self._clips

    def _update_timeline_duration(self) -> None:
        """Update timeline duration based on registered clips."""
        if not self._clips:
            max_frame = 0
        else:
            max_frame = max(clip.end_frame for clip in self._clips.values())
        self._timeline = AnimationTimeline(
            frame_rate=self._frame_rate,
            duration_frames=max_frame,
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Runtime
    "AnimationRuntime",
    "RuntimeAnimationState",
    # Exceptions
    "AnimationRuntimeError",
    "ClipNotFoundError",
    "DuplicateClipError",
    "InvalidFrameError",
    "UnsupportedInterpolationError",
]
