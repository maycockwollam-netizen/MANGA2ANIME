"""Multi-frame PNG sequence export.

Provides a minimal integration layer that exports RenderFrame sequences
to numbered PNG files using the existing single-frame rendering boundary.

Architecture:
    Iterable[RenderFrame]
        ↓
    render_frames_to_png()
        ↓
    PNG sequence (frame_000000.png, frame_000001.png, ...)

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


def render_frames_to_png(
    frames: Iterable[RenderFrame],
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> int:
    """Render a sequence of RenderFrame objects to numbered PNG files.

    Connects the RenderFrame sequence → PNG sequence pipeline.

    Args:
        frames: Iterable of RenderFrame objects to render in order.
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
        >>> from tools.render import render_frames_to_png
        >>> frames = [frame_0, frame_1, frame_2]  # RenderFrame objects
        >>> count = render_frames_to_png(frames, "output_frames")
        >>> print(f"Wrote {count} frames")
    """
    from tools.render.integration import render_frame_to_png

    # Resolve output directory
    output_dir = Path(output_dir)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Count of successfully written frames
    count = 0

    # Process each frame
    for frame in frames:
        # Construct filename using frame_index with zero-padding
        filename = f"{prefix}_{frame.frame_index:06d}.png"
        output_path = output_dir / filename

        # Render the frame using the existing single-frame integration
        render_frame_to_png(
            frame,
            output_path,
            canvas_size=canvas_size,
            background=background,
            renderer=renderer,
        )

        count += 1

    return count


__all__ = [
    "render_frames_to_png",
]
