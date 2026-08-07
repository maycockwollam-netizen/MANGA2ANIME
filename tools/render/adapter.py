"""Renderer adapter for RenderFrame forwarding.

Provides a minimal adapter layer that forwards RenderFrame to a Renderer
without introducing rendering logic or depending on runtime internals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render import RenderFrame
    from tools.render.protocol import Renderer


class FrameAdapter:
    """Minimal adapter that forwards RenderFrame to a Renderer.

    This adapter provides a clean separation between frame production
    and rendering consumption. It simply forwards frames to the underlying
    Renderer without mutation or transformation.

    The adapter does not:
    - Perform any rendering logic
    - Manage state between frames
    - Transform frame data
    - Access runtime internals
    - Mutate RenderFrame or its transforms

    Example:
        >>> from tools.render import RenderFrame, FrameAdapter
        >>> from tools.frame.models import FrameTransform
        >>>
        >>> class LoggingRenderer:
        ...     def render(self, frame: RenderFrame) -> None:
        ...         print(f"Frame {frame.frame_index}")
        >>>
        >>> adapter = FrameAdapter(LoggingRenderer())
        >>> frame = RenderFrame(
        ...     frame_index=0,
        ...     timestamp_seconds=0.0,
        ...     frame_rate=24.0,
        ...     duration_frames=24,
        ...     transforms={},
        ... )
        >>> adapter.forward(frame)
        Frame 0
    """

    def __init__(self, renderer: Renderer) -> None:
        """Initialize the adapter with a Renderer.

        Args:
            renderer: A Renderer-compatible implementation to forward frames to.
        """
        self._renderer = renderer

    def forward(self, frame: RenderFrame) -> None:
        """Forward a RenderFrame to the underlying Renderer.

        Args:
            frame: The RenderFrame to forward.

        Raises:
            RendererError: If the underlying renderer raises an error.
        """
        self._renderer.render(frame)

    @property
    def renderer(self) -> Renderer:
        """Return the underlying Renderer (read-only).

        Returns:
            The Renderer this adapter forwards frames to.
        """
        return self._renderer
