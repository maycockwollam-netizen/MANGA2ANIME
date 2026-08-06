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

from dataclasses import dataclass

from runtime.animation import AnimationRuntime
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


class AnimationOrchestrator:
    """Orchestrates the animation pipeline from domain contracts to runtime.

    Coordinates:
        1. Converts CharacterAnimationOutput + CharacterTransformInputSet to clips
        2. Registers clips in AnimationRuntime
        3. Delegates evaluation to AnimationRuntime

    State Management:
        - Explicitly instantiated (not a singleton)
        - No global mutable state
        - Owns one AnimationRuntime instance
        - Deterministic behavior

    Attributes:
        sequence_id: Sequence identifier (from CharacterAnimationOutput)

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
        >>> # Evaluate
        >>> result = orchestrator.evaluate_at_frame(12)
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
    # Exceptions
    "AnimationOrchestratorError",
    "ClipCreationError",
]
