"""End-to-end render sequence export entry point.

Provides a minimal public entry point that delegates to the existing
PNG sequence export implementation.

Architecture:
    Iterable[RenderFrame]
        ↓
    export_render_frames()
        ↓
    render_frames_to_png()
        ↓
    PNG sequence

This module does NOT:
- Produce RenderFrame (delegates to runtime)
- Implement animation playback
- Implement video encoding
- Access runtime internals
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render import Renderer, RenderFrame


def export_render_frames(
    frames: Iterable[RenderFrame],
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> int:
    """Export a sequence of RenderFrame objects to numbered PNG files.

    This is a public entry point that delegates to the existing PNG sequence
    export implementation. It does not introduce new rendering logic.

    Args:
        frames: Iterable of RenderFrame objects to export in order.
        output_dir: Directory to write PNG files. Created if it doesn't exist.
        prefix: Filename prefix for PNG files (default: "frame").
        canvas_size: Canvas dimensions (width, height). Uses renderer default if None.
        background: RGBA background color. Uses renderer default if None.
        renderer: Optional custom renderer. Creates ConcreteRenderer if None.

    Returns:
        Number of PNG files successfully written.

    Raises:
        RendererError: If canvas_size is invalid or rendering fails.
        OSError: If output directory cannot be created.

    Example:
        >>> from tools.render import export_render_frames
        >>> frames = [frame_0, frame_1, frame_2]  # RenderFrame objects
        >>> count = export_render_frames(frames, "output_frames")
        >>> print(f"Exported {count} frames")
    """
    # Delegate to existing implementation
    from tools.render.sequence import render_frames_to_png

    return render_frames_to_png(
        frames,
        output_dir,
        prefix=prefix,
        canvas_size=canvas_size,
        background=background,
        renderer=renderer,
    )


__all__ = [
    "export_render_frames",
]
