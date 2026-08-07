"""Renderer protocol for RenderFrame consumption.

Defines the minimal structural contract for renderers that consume RenderFrame.
This module contains no concrete rendering implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tools.render import RenderFrame


@runtime_checkable
class Renderer(Protocol):
    """Minimal renderer protocol consuming RenderFrame.

    This protocol defines the structural contract for rendering a single frame.
    Implementations should be stateless unless state is genuinely required.

    Protocol Requirements:
        - Accept RenderFrame as primary input
        - Do not access runtime internals
        - Do not mutate RenderFrame
        - Use clip_id as entity identity
        - Preserve FrameTransform semantics

    Dependency Constraints:
        Renderer implementations must NOT depend on:
        - runtime.animation (ANY module)
        - AnimationRuntime internals
        - AnimationTimeline
        - AnimationClip
        - tools.manga_frame

    Usage:
        The Renderer is a runtime-checkable Protocol. Use isinstance() to verify
        that an object implements the protocol:

        >>> class LoggingRenderer:
        ...     def render(self, frame: RenderFrame) -> None:
        ...         for clip_id, transform in frame.transforms.items():
        ...             print(f"Render {clip_id} at {frame.frame_index}")
        >>>
        >>> renderer: Renderer = LoggingRenderer()
        >>> assert isinstance(renderer, Renderer)

    Example:
        >>> from tools.render import RenderFrame, Renderer
        >>> from tools.frame.models import FrameTransform
        >>>
        >>> frame = RenderFrame(
        ...     frame_index=12,
        ...     timestamp_seconds=0.5,
        ...     frame_rate=24.0,
        ...     duration_frames=240,
        ...     transforms={"hero_1": FrameTransform(position_x=100)},
        ... )
        >>>
        >>> renderer = LoggingRenderer()
        >>> renderer.render(frame)
        Render hero_1 at 12
    """

    def render(self, frame: RenderFrame) -> None:
        """Render a single frame.

        Args:
            frame: Immutable frame context to render.
                Contains frame_index, timestamp, and transforms.
        """
        ...
