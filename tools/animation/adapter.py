"""Camera animator adapter.

OutputAdapter-style class that binds a CameraAnimator to a fixed source
asset path and exposes a simplified evaluate entrypoint. This mirrors the
OutputAdapter pattern used in tools/render, tools/vfx, and tools/audio.

This module does NOT:
- Implement interpolation (delegated to the bound animator)
- Access GPU
- Depend on runtime.animation internals
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tools.frame.models import FrameTransform

if TYPE_CHECKING:
    from tools.animation.models import AnimationConfig
    from tools.animation.protocol import CameraAnimator


class SourceAdapter:
    """Bind a CameraAnimator to a fixed source asset path.

    The adapter forwards evaluate() calls to the bound animator and attaches
    the bound source_path to the resulting FrameTransform.

    Attributes:
        animator: The wrapped CameraAnimator.
        source_path: The image asset path attached to every evaluated
            FrameTransform.
    """

    def __init__(self, animator: CameraAnimator, source_path: Path) -> None:
        """Initialize the adapter with an animator and source path.

        Args:
            animator: The CameraAnimator to delegate evaluation to.
            source_path: The image asset path to attach to results.
        """
        self.animator = animator
        self.source_path = Path(source_path)

    def evaluate(self, config: AnimationConfig, time: float) -> FrameTransform:
        """Evaluate the animation and attach the bound source path.

        Args:
            config: The animation configuration describing keyframes.
            time: Time in seconds at which to evaluate.

        Returns:
            A FrameTransform with source_path set to the adapter's bound path.
        """
        transform = self.animator.evaluate(config, time)
        return transform.model_copy(update={"source_path": self.source_path})
