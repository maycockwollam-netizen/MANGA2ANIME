"""Camera animator protocol contract.

Defines the minimal interface that a camera animator must implement, without
knowing how interpolation is performed or which rendering backend is used.

This module does NOT:
- Implement animation (delegated to concrete animators)
- Access GPU
- Depend on runtime.animation internals
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from tools.frame.models import FrameTransform

if TYPE_CHECKING:
    from tools.animation.models import AnimationConfig


@runtime_checkable
class CameraAnimator(Protocol):
    """Protocol for camera animation evaluation.

    A CameraAnimator evaluates an AnimationConfig at a given time and returns
    a FrameTransform suitable for rendering a single frame.

    Implementations may vary in interpolation strategy (linear, eased, spline)
    but must conform to this contract.
    """

    def evaluate(self, config: AnimationConfig, time: float) -> FrameTransform:
        """Evaluate the animation at a specific time.

        Args:
            config: The animation configuration describing keyframes.
            time: Time in seconds at which to evaluate the animation.

        Returns:
            A FrameTransform representing the camera state at the given time.

        Raises:
            AnimationConfigError: If the configuration is invalid.
            AnimationEvalError: If evaluation fails (e.g. time out of range).
        """
        ...
