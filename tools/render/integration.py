"""Single-frame render integration.

Provides a minimal integration layer that connects RenderFrame production
to PNG output using the existing renderer boundary.

Architecture:
    RenderFrame
        ↓
    FrameAdapter
        ↓
    ConcreteRenderer
        ↓
    PNG file

This module does NOT:
- Produce RenderFrame (delegates to runtime)
- Implement animation playback
- Implement video rendering
- Access runtime internals
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render import Renderer, RenderFrame


def render_frame_to_png(
    frame: RenderFrame,
    output_path: Path | str,
    *,
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> None:
    """Render a RenderFrame to a PNG file.

    Connects the RenderFrame → FrameAdapter → ConcreteRenderer → PNG pipeline.

    Args:
        frame: The RenderFrame to render.
        output_path: Destination path for PNG output.
        canvas_size: Canvas dimensions (width, height). Uses renderer default if None.
        background: RGBA background color. Uses renderer default if None.
        renderer: Optional custom renderer. Creates ConcreteRenderer if None.

    Raises:
        RendererError: If canvas_size is invalid.
        OSError: If output file cannot be written.

    Example:
        >>> from tools.render import render_frame_to_png
        >>> from tools.render import RenderFrame
        >>> frame = RenderFrame(
        ...     frame_index=0,
        ...     timestamp_seconds=0.0,
        ...     frame_rate=24.0,
        ...     duration_frames=24,
        ...     transforms={},
        ... )
        >>> render_frame_to_png(frame, "output.png")
    """
    # Lazy imports to avoid circular dependency
    from tools.render.adapter import FrameAdapter
    from tools.render.concrete_renderer import ConcreteRenderer

    # Resolve output path
    output_path = Path(output_path)

    # Create renderer if not provided
    if renderer is None:
        renderer_kwargs: dict = {}
        if canvas_size is not None:
            renderer_kwargs["canvas_size"] = canvas_size
        if background is not None:
            renderer_kwargs["background"] = background
        renderer = ConcreteRenderer(**renderer_kwargs)

    # Create adapter
    adapter = FrameAdapter(renderer)

    # Forward the exact RenderFrame
    adapter.forward(frame)

    # Obtain the rendered image
    image = renderer.last_output
    if image is None:
        msg = "Renderer did not produce output"
        raise RuntimeError(msg)

    # Save as PNG
    image.save(output_path, format="PNG")


__all__ = [
    "render_frame_to_png",
]
