"""VFX effect protocol.

Defines the minimal structural contract for VFX effects that consume a
configuration and an optional base image. This module contains no concrete
effect implementation.

Scope:
    A VfxEffect applies a visual effect (speed lines, motion blur, etc.) onto
    a target RGBA image. Effects are expected to be stateless unless state is
    genuinely required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from PIL import Image

    from tools.vfx.models import SpeedLinesConfig


@runtime_checkable
class VfxEffect(Protocol):
    """Minimal VFX effect protocol.

    A VfxEffect applies a visual effect onto a base RGBA image and returns a
    new image with the effect composited on top. The input image must not be
    mutated.

    Protocol Requirements:
        - Accept a base RGBA Image (may be a blank canvas).
        - Accept an effect configuration describing the effect parameters.
        - Return a new RGBA Image with the effect applied.
        - Do not mutate the input image.

    Dependency Constraints:
        VfxEffect implementations must NOT depend on:
        - runtime.animation (ANY module)
        - AnimationRuntime internals
        - AnimationTimeline / AnimationClip
        - tools.manga_frame

    Usage:
        The VfxEffect is a runtime-checkable Protocol. Use isinstance() to
        verify that an object implements the protocol:

        >>> class NoopEffect:
        ...     def apply(self, base, config):
        ...         return base.copy()
        >>>
        >>> effect: VfxEffect = NoopEffect()
        >>> assert isinstance(effect, VfxEffect)

    Example:
        >>> from PIL import Image
        >>> from tools.vfx import VfxEffect, SpeedLinesConfig
        >>> from tools.vfx.concrete_effect import SpeedLinesEffect
        >>>
        >>> canvas = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        >>> config = SpeedLinesConfig(line_count=16, line_length=80)
        >>> effect = SpeedLinesEffect()
        >>> result = effect.apply(canvas, config)
        >>> result.size == (200, 200)
        True
    """

    def apply(self, base: Image.Image, config: SpeedLinesConfig) -> Image.Image:
        """Apply the effect to a base image.

        Args:
            base: The base RGBA Image to apply the effect onto. Must not be
                mutated by this call.
            config: Effect configuration describing the effect parameters.

        Returns:
            A new RGBA Image with the effect composited on top of the base.
        """
        ...
