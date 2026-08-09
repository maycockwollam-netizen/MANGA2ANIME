"""VFX effect adapter for configuration forwarding.

Provides a minimal adapter layer that forwards a base image and configuration
to a VfxEffect without introducing effect logic or depending on runtime
internals.

Scope:
    The adapter composes a VfxEffect with a fixed configuration, exposing a
    simpler apply(base) surface. It does not perform any rendering logic,
    manage state between calls, transform configuration, or access runtime
    internals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

    from tools.vfx.models import SpeedLinesConfig
    from tools.vfx.protocol import VfxEffect


class EffectAdapter:
    """Minimal adapter that binds a VfxEffect to a fixed configuration.

    Composes a VfxEffect with a SpeedLinesConfig so callers can apply the
    effect to any base image without re-supplying the configuration each call.

    The adapter does not:
    - Perform any effect logic
    - Manage state between calls
    - Transform the configuration or image data
    - Access runtime internals
    - Mutate the input image

    Example:
        >>> from PIL import Image
        >>> from tools.vfx import EffectAdapter, SpeedLinesConfig
        >>> from tools.vfx.concrete_effect import SpeedLinesEffect
        >>>
        >>> adapter = EffectAdapter(SpeedLinesEffect(), SpeedLinesConfig(line_count=8))
        >>> canvas = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        >>> result = adapter.apply(canvas)
        >>> result.size == (100, 100)
        True
    """

    def __init__(self, effect: VfxEffect, config: SpeedLinesConfig) -> None:
        """Initialize the adapter with a VfxEffect and configuration.

        Args:
            effect: A VfxEffect-compatible implementation to forward to.
            config: The fixed effect configuration to bind.
        """
        self._effect = effect
        self._config = config

    def apply(self, base: Image.Image) -> Image.Image:
        """Apply the bound effect to a base image.

        Args:
            base: The base RGBA Image to apply the effect onto.

        Returns:
            A new RGBA Image with the effect composited on top.

        Raises:
            VfxError: If the underlying effect raises an error.
        """
        return self._effect.apply(base, self._config)

    @property
    def effect(self) -> VfxEffect:
        """Return the underlying VfxEffect (read-only).

        Returns:
            The VfxEffect this adapter forwards to.
        """
        return self._effect

    @property
    def config(self) -> SpeedLinesConfig:
        """Return the bound configuration (read-only).

        Returns:
            The SpeedLinesConfig bound to this adapter.
        """
        return self._config
