"""Concrete VFX effect implementation: basic speed lines.

V1 implementation that renders speed lines onto an RGBA image using Pillow.

Speed lines are radiating lines drawn from a focal point toward the canvas
edges — a staple manga/anime motion cue. Placement is deterministic given the
seed in the configuration.

This module does NOT:
- Implement GPU effects
- Access runtime animation internals
- Implement caching or batching
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from tools.vfx.exceptions import VfxConfigError, VfxRenderError
from tools.vfx.models import SpeedLineDirection, SpeedLinesConfig

if TYPE_CHECKING:
    from PIL import Image as PILImage


class SpeedLinesEffect:
    """Concrete VFX effect rendering basic speed lines using Pillow.

    V1 supports three emanation directions:
    - RADIAL: lines radiate outward from the focal point at random angles.
    - HORIZONTAL: lines extend horizontally from the focal point.
    - VERTICAL: lines extend vertically from the focal point.

    Line placement is deterministic given the config seed, enabling
    reproducible compositing across runs.

    Attributes:
        None (stateless). All parameters come from the per-call configuration.

    Example:
        >>> from PIL import Image
        >>> from tools.vfx import SpeedLinesConfig
        >>> from tools.vfx.concrete_effect import SpeedLinesEffect
        >>>
        >>> canvas = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        >>> config = SpeedLinesConfig(line_count=16, line_length=80)
        >>> effect = SpeedLinesEffect()
        >>> result = effect.apply(canvas, config)
        >>> result.mode
        'RGBA'
    """

    def apply(self, base: PILImage.Image, config: SpeedLinesConfig) -> PILImage.Image:
        """Apply speed lines to a base image.

        Args:
            base: The base RGBA Image to apply speed lines onto. Must not be
                mutated by this call.
            config: Speed lines configuration.

        Returns:
            A new RGBA Image with speed lines composited on top.

        Raises:
            VfxConfigError: If the configuration is inconsistent.
            VfxRenderError: If the base image is not RGBA or has invalid size.
        """
        if base.mode != "RGBA":
            raise VfxRenderError(f"base image must be RGBA, got mode '{base.mode}'")
        width, height = base.size
        if width <= 0 or height <= 0:
            raise VfxRenderError(f"base image must have positive size, got {base.size}")

        # Work on a copy so the input is never mutated.
        result = base.copy()

        # No-op fast path: zero lines or zero alpha.
        effective_alpha = self._effective_alpha(config)
        if config.line_count == 0 or config.line_length == 0 or effective_alpha == 0:
            return result

        focal_px = (config.focal_x * width, config.focal_y * height)
        lines = self._compute_lines(config, focal_px, width, height)

        if not lines:
            return result

        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        color = self._scaled_color(config, effective_alpha)
        thickness = config.line_thickness
        for (start, end) in lines:
            draw.line([start, end], fill=color, width=thickness)

        # Composite the overlay onto the copy using alpha blending.
        return Image.alpha_composite(result, overlay)

    def _compute_lines(
        self,
        config: SpeedLinesConfig,
        focal_px: tuple[float, float],
        width: int,
        height: int,
    ) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        """Compute the list of line segments for the configured direction.

        Args:
            config: Speed lines configuration.
            focal_px: Focal point in pixel coordinates (fx, fy).
            width: Canvas width in pixels.
            height: Canvas height in pixels.

        Returns:
            List of (start, end) pixel coordinate pairs.

        Raises:
            VfxConfigError: If the direction is unsupported.
        """
        rng = random.Random(config.seed)
        length = config.line_length
        fx, fy = focal_px

        if config.direction == SpeedLineDirection.RADIAL:
            return self._radial_lines(rng, fx, fy, length, config.line_count)
        if config.direction == SpeedLineDirection.HORIZONTAL:
            return self._axis_lines(rng, fx, fy, length, config.line_count, axis="x")
        if config.direction == SpeedLineDirection.VERTICAL:
            return self._axis_lines(rng, fx, fy, length, config.line_count, axis="y")

        raise VfxConfigError(f"unsupported speed line direction: {config.direction}")

    def _radial_lines(
        self,
        rng: random.Random,
        fx: float,
        fy: float,
        length: int,
        count: int,
    ) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        """Compute radial speed line segments around the focal point.

        Lines start just outside the focal point and extend outward by `length`
        pixels along a random angle. A small inner offset avoids a clumped
        center.
        """
        lines: list[tuple[tuple[float, float], tuple[float, float]]] = []
        inner_offset = 4.0
        for _ in range(count):
            angle = rng.uniform(0.0, 2.0 * math.pi)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            start = (fx + cos_a * inner_offset, fy + sin_a * inner_offset)
            end = (fx + cos_a * (inner_offset + length), fy + sin_a * (inner_offset + length))
            lines.append((start, end))
        return lines

    def _axis_lines(
        self,
        rng: random.Random,
        fx: float,
        fy: float,
        length: int,
        count: int,
        axis: str,
    ) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        """Compute horizontal or vertical speed line segments.

        For axis "x", lines extend left or right from the focal point along the
        horizontal axis at random vertical offsets. For axis "y", lines extend
        up or down at random horizontal offsets.
        """
        lines: list[tuple[tuple[float, float], tuple[float, float]]] = []
        for _ in range(count):
            direction = 1 if rng.random() >= 0.5 else -1
            if axis == "x":
                jitter = rng.uniform(-8.0, 8.0)
                start = (fx, fy + jitter)
                end = (fx + direction * length, fy + jitter)
            else:
                jitter = rng.uniform(-8.0, 8.0)
                start = (fx + jitter, fy)
                end = (fx + jitter, fy + direction * length)
            lines.append((start, end))
        return lines

    def _effective_alpha(self, config: SpeedLinesConfig) -> float:
        """Compute the effective alpha combining config intensity and color alpha.

        Args:
            config: Speed lines configuration.

        Returns:
            Effective alpha in [0.0, 1.0].
        """
        base_alpha = config.line_color[3] / 255.0
        return max(0.0, min(1.0, base_alpha * config.intensity))

    def _scaled_color(self, config: SpeedLinesConfig, alpha: float) -> tuple[int, int, int, int]:
        """Return the line color with the effective alpha applied.

        Args:
            config: Speed lines configuration.
            alpha: Effective alpha in [0.0, 1.0].

        Returns:
            RGBA tuple with scaled alpha (0-255).
        """
        r, g, b, _ = config.line_color
        return (r, g, b, int(alpha * 255))
