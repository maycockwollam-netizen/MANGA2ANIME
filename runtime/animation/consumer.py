"""Animation Orchestration Module.

Provides a consumer layer that orchestrates the animation pipeline:
    CharacterAnimationOutput + CharacterTransformInputSet
            ↓
    create_animation_clips()
            ↓
    AnimationRuntime
            ↓
    evaluate_at_frame()

This module coordinates existing components without reimplementing them.

Dependency direction:
    runtime.animation.consumer
            ↓
    runtime.animation
            ↓
    tools.frame
    tools.manga_frame

This module does NOT:
- Generate animation data
- Create keyframes
- Interpolate transforms (delegates to AnimationRuntime)
- Render frames
- Access GPU
- Perform I/O operations
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from runtime.animation import AnimationRuntime, InvalidFrameError
from tools.frame.animation import AnimationClip
from tools.frame.models import FrameTransform
from tools.manga_frame.character_animation import (
    CharacterAnimationOutput,
    CharacterTransformInputSet,
)
from tools.manga_frame.character_animation import (
    create_animation_clips as _create_clips,
)

# ============================================================================
# Exceptions
# ============================================================================


class AnimationOrchestratorError(Exception):
    """Base exception for animation orchestrator errors."""

    pass


class ClipCreationError(AnimationOrchestratorError):
    """Raised when animation clip creation fails."""

    pass


# ============================================================================
# Orchestrator Contract
# ============================================================================


@dataclass(frozen=True)
class OrchestratorState:
    """Immutable state for the orchestrator.

    Attributes:
        sequence_id: Sequence identifier
        clip_count: Number of clips registered in runtime
        runtime_frame_rate: Frame rate of underlying runtime
    """

    sequence_id: str
    clip_count: int
    runtime_frame_rate: float


@dataclass(frozen=True)
class PlaybackState:
    """Immutable playback state snapshot.

    Attributes:
        current_frame: Current frame position
        duration_frames: Total frames from runtime
        frame_rate: Frame rate for time calculations
        current_time_seconds: Current time in seconds (derived from current_frame)
    """

    current_frame: int
    duration_frames: int
    frame_rate: float
    current_time_seconds: float


class AnimationOrchestrator:
    """Orchestrates the animation pipeline from domain contracts to runtime.

    Coordinates:
        1. Converts CharacterAnimationOutput + CharacterTransformInputSet to clips
        2. Registers clips in AnimationRuntime
        3. Delegates evaluation to AnimationRuntime
        4. Provides deterministic playback timing

    State Management:
        - Explicitly instantiated (not a singleton)
        - No global mutable state
        - Owns one AnimationRuntime instance
        - Deterministic behavior (update(delta_time) pattern)

    Playback Timing:
        - current_frame tracks playback position
        - update(delta_time) advances playback by elapsed time
        - seek(frame_index) jumps to specific frame
        - No wall-clock dependency - external loop provides delta_time

    Attributes:
        sequence_id: Sequence identifier (from CharacterAnimationOutput)
        current_frame: Current playback frame position

    Example:
        >>> from tools.manga_frame.character_animation import (
        ...     CharacterAnimationBinding,
        ...     CharacterAnimationOutput,
        ...     CharacterAnimationTarget,
        ...     CharacterAnimationMetadata,
        ...     CharacterTransformInput,
        ...     CharacterTransformInputSet,
        ... )
        >>> from tools.frame.models import FrameTransform
        >>>
        >>> # Create domain data
        >>> output = CharacterAnimationOutput(...)
        >>> transforms = CharacterTransformInputSet(...)
        >>>
        >>> # Create orchestrator and load
        >>> orchestrator = AnimationOrchestrator()
        >>> orchestrator.load(output, transforms)
        >>>
        >>> # Playback timing
        >>> orchestrator.seek(0)
        >>> orchestrator.update(0.5)  # Advance 0.5 seconds
        >>> result = orchestrator.evaluate_current_frame()
    """

    def __init__(
        self,
        *,
        frame_rate: float = 24.0,
    ) -> None:
        """Initialize orchestrator.

        Args:
            frame_rate: Frame rate for runtime (default: 24.0)
        """
        self._frame_rate = frame_rate
        self._sequence_id: str | None = None
        self._runtime = AnimationRuntime(
            sequence_id="internal",  # Internal ID, not exposed
            frame_rate=frame_rate,
        )
        # Playback state
        self._current_frame: int = 0
        self._current_time: float = 0.0

    @property
    def sequence_id(self) -> str | None:
        """Get the sequence ID.

        Returns None if no animation has been loaded.
        """
        return self._sequence_id

    @property
    def frame_rate(self) -> float:
        """Get the frame rate."""
        return self._frame_rate

    @property
    def state(self) -> OrchestratorState:
        """Get immutable orchestrator state."""
        return OrchestratorState(
            sequence_id=self._sequence_id or "",
            clip_count=len(self._runtime),
            runtime_frame_rate=self._frame_rate,
        )

    # ========================================================================
    # Playback Properties
    # ========================================================================

    @property
    def current_frame(self) -> int:
        """Get current playback frame position.

        Returns:
            Current frame index (0-based).
        """
        return self._current_frame

    @property
    def duration_frames(self) -> int:
        """Get total duration in frames from runtime.

        Returns:
            Total frames (0 if no clips registered).
        """
        return self._runtime.duration_frames

    @property
    def playback_state(self) -> PlaybackState:
        """Get immutable playback state snapshot.

        Returns:
            Frozen PlaybackState with current frame info.
        """
        return PlaybackState(
            current_frame=self._current_frame,
            duration_frames=self.duration_frames,
            frame_rate=self._frame_rate,
            current_time_seconds=self._current_time,
        )

    # ========================================================================
    # Playback Methods
    # ========================================================================

    def seek(self, frame_index: int) -> None:
        """Jump to specific frame.

        Clamps to valid range if frame_index is out of bounds.

        Args:
            frame_index: Target frame index
        """
        duration = self.duration_frames
        # Clamp to [0, duration]
        if frame_index < 0:
            self._current_frame = 0
        elif frame_index > duration:
            self._current_frame = duration
        else:
            self._current_frame = frame_index
        # Sync current_time to match frame
        self._current_time = self._current_frame / self._frame_rate

    def update(self, delta_time: float) -> int:
        """Advance playback by delta_time seconds.

        Deterministic: same initial state + same delta_time = same final frame.
        Uses rounding to nearest frame (matches AnimationTimeline semantics).

        Args:
            delta_time: Time elapsed in seconds (must be >= 0)

        Returns:
            New current_frame after update

        Raises:
            ValueError: If delta_time is negative
        """
        if delta_time < 0:
            raise ValueError("delta_time cannot be negative")

        if delta_time == 0:
            return self._current_frame

        # Accumulate time (for frame computation)
        self._current_time += delta_time

        # Convert to frame using rounding (matches AnimationTimeline.frame_index_at)
        new_frame = int(round(self._current_time * self._frame_rate))

        # Clamp to duration
        duration = self.duration_frames
        if new_frame > duration:
            new_frame = duration

        # Always derive _current_time from _current_frame to avoid drift
        # This maintains the invariant: _current_time == _current_frame / frame_rate
        self._current_frame = new_frame
        self._current_time = self._current_frame / self._frame_rate

        return self._current_frame

    def reset(self) -> None:
        """Reset playback to beginning.

        Sets current_frame to 0 and current_time to 0.
        Does not modify runtime state.
        """
        self._current_frame = 0
        self._current_time = 0.0

    def evaluate_current_frame(self) -> dict[str, FrameTransform]:
        """Evaluate all clips at current playback frame.

        Convenience method that delegates to runtime.

        Returns:
            Dictionary mapping clip_id to FrameTransform
        """
        return self._runtime.evaluate_at_frame(self._current_frame)

    def frames(
        self,
        start_frame: int = 0,
        end_frame: int | None = None,
    ) -> Iterator[tuple[int, dict[str, FrameTransform]]]:
        """Iterate through a frame range and evaluate each frame.

        This is a deterministic, read-only evaluation operation that does not
        modify playback state (current_frame, current_time, playback_state).

        By default, iterates from frame 0 through duration_frames (inclusive).
        If end_frame is None, uses duration_frames as the upper bound.

        Args:
            start_frame: Starting frame index (inclusive). Must be >= 0.
            end_frame: Ending frame index (inclusive). Must be >= start_frame.
                If None, uses duration_frames.

        Yields:
            Tuple of (frame_index, transforms) for each frame in the range.

        Raises:
            InvalidFrameError: If start_frame < 0
            InvalidFrameError: If end_frame < 0
            InvalidFrameError: If start_frame > duration_frames
            InvalidFrameError: If end_frame > duration_frames
            ValueError: If start_frame > end_frame

        Example:
            >>> for frame_index, transforms in orchestrator.frames():
            ...     render_frame(frame_index, transforms)
            >>>
            >>> for frame_index, transforms in orchestrator.frames(5, 10):
            ...     print(f"Frame {frame_index}")
        """
        duration = self.duration_frames

        # Validate start_frame
        if start_frame < 0:
            raise InvalidFrameError(
                f"start_frame {start_frame} cannot be negative"
            )

        if start_frame > duration:
            raise InvalidFrameError(
                f"start_frame {start_frame} exceeds duration {duration}"
            )

        # Determine end_frame
        if end_frame is None:
            end_frame = duration
        elif end_frame < 0:
            raise InvalidFrameError(
                f"end_frame {end_frame} cannot be negative"
            )
        elif end_frame > duration:
            raise InvalidFrameError(
                f"end_frame {end_frame} exceeds duration {duration}"
            )

        # Validate range
        if start_frame > end_frame:
            # Empty range - return empty iterator
            return

        # Yield frames lazily
        for frame_index in range(start_frame, end_frame + 1):
            yield (frame_index, self._runtime.evaluate_at_frame(frame_index))

    def load(
        self,
        animation_output: CharacterAnimationOutput,
        transform_inputs: CharacterTransformInputSet,
    ) -> tuple[AnimationClip, ...]:
        """Load and register animation data.

        Atomically:
            1. Creates AnimationClips via create_animation_clips()
            2. Clears existing runtime state
            3. Registers new clips
            4. Resets playback to frame 0

        If clip creation fails, runtime state is unchanged.

        Args:
            animation_output: CharacterAnimationOutput containing structural bindings
            transform_inputs: CharacterTransformInputSet containing animation transforms

        Returns:
            Tuple of created AnimationClips

        Raises:
            ClipCreationError: If clip creation fails
        """
        try:
            clips = _create_clips(animation_output, transform_inputs)
        except ValueError as e:
            raise ClipCreationError(
                f"Failed to create animation clips: {e}"
            ) from e

        # Clear existing state and register new clips atomically
        self._runtime.clear()
        self._runtime.register_many(list(clips))
        self._sequence_id = animation_output.sequence_id

        # Reset playback to beginning
        self._current_frame = 0
        self._current_time = 0.0

        return clips

    def reload(
        self,
        animation_output: CharacterAnimationOutput,
        transform_inputs: CharacterTransformInputSet,
    ) -> tuple[AnimationClip, ...]:
        """Reload animation data, replacing existing state.

        Equivalent to calling load() when data already exists.
        Atomically replaces all existing clips.

        Args:
            animation_output: CharacterAnimationOutput containing structural bindings
            transform_inputs: CharacterTransformInputSet containing animation transforms

        Returns:
            Tuple of created AnimationClips

        Raises:
            ClipCreationError: If clip creation fails
        """
        return self.load(animation_output, transform_inputs)

    def evaluate(self, clip_id: str, frame_index: int) -> FrameTransform:
        """Evaluate a specific clip at a frame.

        Delegates to AnimationRuntime.evaluate().

        Args:
            clip_id: ID of clip to evaluate
            frame_index: Frame to evaluate

        Returns:
            FrameTransform at the specified frame

        Raises:
            ClipNotFoundError: If clip_id not found
            InvalidFrameError: If frame_index is invalid
            UnsupportedInterpolationError: If non-LINEAR interpolation is used
        """
        return self._runtime.evaluate(clip_id, frame_index)

    def evaluate_at_frame(self, frame_index: int) -> dict[str, FrameTransform]:
        """Evaluate all active clips at a specific frame.

        Delegates to AnimationRuntime.evaluate_at_frame().

        Args:
            frame_index: Frame index to evaluate

        Returns:
            Dictionary mapping clip_id to FrameTransform
        """
        return self._runtime.evaluate_at_frame(frame_index)

    def get_clip(self, clip_id: str) -> AnimationClip:
        """Get a registered clip by ID.

        Delegates to AnimationRuntime.get_clip().

        Args:
            clip_id: ID of clip to retrieve

        Returns:
            The AnimationClip

        Raises:
            ClipNotFoundError: If clip_id not found
        """
        return self._runtime.get_clip(clip_id)

    def has_clip(self, clip_id: str) -> bool:
        """Check if a clip is registered.

        Args:
            clip_id: ID to check

        Returns:
            True if clip exists, False otherwise
        """
        return self._runtime.has_clip(clip_id)

    def list_clips(self) -> list[AnimationClip]:
        """List all registered clips.

        Returns:
            List of AnimationClips sorted by clip_id
        """
        return self._runtime.list_clips()

    def count(self) -> int:
        """Get the number of registered clips.

        Returns:
            Number of clips
        """
        return self._runtime.count()

    def get_runtime(self) -> AnimationRuntime:
        """Get the underlying AnimationRuntime.

        Exposes the runtime for advanced use cases.

        Returns:
            The AnimationRuntime instance
        """
        return self._runtime

    def __len__(self) -> int:
        """Get the number of registered clips."""
        return len(self._runtime)

    def __contains__(self, clip_id: str) -> bool:
        """Check if a clip is registered."""
        return clip_id in self._runtime


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Orchestrator
    "AnimationOrchestrator",
    "OrchestratorState",
    "PlaybackState",
    # Exceptions
    "AnimationOrchestratorError",
    "ClipCreationError",
]
