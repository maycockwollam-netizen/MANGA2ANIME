"""Renderer Integration Contract.

Defines the minimal contract between AnimationRuntime and a renderer.
This module specifies what data a renderer receives, without knowing how rendering is performed.

This module does NOT:
- Implement rendering
- Perform image manipulation
- Access GPU
- Execute animation logic
- Manage playback state

Architecture:
    tools/frame/models.py (FrameTransform)
            ↓
    tools/render/__init__.py (RenderFrame)
            ↓
    tools/render/protocol.py (Renderer Protocol)
            ↓
    [Concrete Renderer Implementations]

Dependency Constraints:
    The Renderer protocol and RenderFrame must NOT depend on:
    - runtime.animation (ANY module)
    - AnimationRuntime internals
    - AnimationTimeline
    - AnimationClip
    - tools.manga_frame
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tools.frame.models import FrameTransform


@dataclass(frozen=True)
class RenderFrame:
    """Immutable frame context for renderer consumption.

    Represents the animation state at a specific frame, suitable for
    renderer consumption. This is a pure data contract - the runtime
    produces this, a renderer consumes it.

    Timing Attributes:
        frame_index: Zero-based frame index in the animation sequence.
            Range: [0, duration_frames]
        timestamp_seconds: Elapsed time from animation start to this frame.
            Computed as: frame_index / frame_rate
        duration_frames: Total animation duration in frames.
            This is the last valid frame index + 1.
        duration_seconds: Total animation duration in seconds.
            Computed as: duration_frames / frame_rate
        frame_rate: Frame rate used for timestamp computation (FPS).

    Transform Attributes:
        transforms: Read-only mapping from authoritative entity/clip identity (clip_id)
            to the evaluated FrameTransform at this frame.
        entity_count: Number of entities with transforms in this frame.

    Entity Lifecycle:
        The transforms mapping uses clip_id as the entity identity key.
        - Keys are authoritative clip identifiers from AnimationClip.clip_id
        - Values are FrameTransform instances evaluated at this frame
        - An entity is present in a frame if its clip_id appears in the keys
        - An entity is absent from a frame if its clip_id is not in the keys

    Immutability:
        RenderFrame is a frozen dataclass - fields cannot be reassigned.
        The transforms mapping is wrapped by the producer to prevent
        in-place mutation (add/delete keys). However, the FrameTransform
        values themselves remain mutable (Pydantic BaseModel).

    Coordinate System:
        The RenderFrame contract does NOT specify a coordinate system.
        Transform values (position_x, position_y, scale, rotation_deg, etc.)
        are provided as-is from FrameTransform. The renderer is responsible
        for interpreting these values according to its own coordinate conventions.

        Important: The animation system uses:
        - position_x, position_y: offset from origin (units unspecified)
        - scale: relative to original size (1.0 = unchanged)
        - rotation_deg: clockwise positive
        - opacity: 0.0 (transparent) to 1.0 (opaque)
        - anchor_x, anchor_y: normalized pivot points (0-1 range)

    Determinism:
        Given identical runtime state and frame_index, RenderFrame construction
        is deterministic. Same input produces identical output.

    Example:
        >>> from tools.frame.models import FrameTransform
        >>> from tools.render import RenderFrame
        >>>
        >>> frame = RenderFrame(
        ...     frame_index=12,
        ...     timestamp_seconds=0.5,
        ...     frame_rate=24.0,
        ...     duration_frames=240,
        ...     transforms={"hero_1": FrameTransform(position_x=100)},
        ... )
        >>>
        >>> # Timing information
        >>> print(f"Frame {frame.frame_index} at {frame.timestamp_seconds}s")
        Frame 12 at 0.5s
        >>> print(f"Animation duration: {frame.duration_seconds}s")
        Animation duration: 10.0s
        >>>
        >>> # Entity presence check
        >>> if "hero_1" in frame.transforms:
        ...     transform = frame.transforms["hero_1"]
        ...     render_entity("hero_1", transform)
    """

    frame_index: int
    timestamp_seconds: float
    frame_rate: float
    duration_frames: int
    transforms: Mapping[str, FrameTransform]

    @property
    def duration_seconds(self) -> float:
        """Total animation duration in seconds.

        Returns:
            Animation duration in seconds = duration_frames / frame_rate
        """
        return self.duration_frames / self.frame_rate

    @property
    def entity_count(self) -> int:
        """Number of entities with transforms in this frame.

        Returns:
            Count of clip_ids with transforms in this frame.
        """
        return len(self.transforms)


# Renderer Adapter - must be imported after RenderFrame to avoid circular dependency
from tools.render.adapter import FrameAdapter as FrameAdapter  # noqa: E402

# Concrete Renderer - must be imported after RenderFrame to avoid circular dependency
from tools.render.concrete_renderer import ConcreteRenderer as ConcreteRenderer  # noqa: E402

# Renderer Exceptions - must be imported after RenderFrame to avoid circular dependency
from tools.render.exceptions import (  # noqa: E402
    RendererError,
    RenderFrameError,
    TransformError,
)

# Renderer Protocol - must be imported after RenderFrame to avoid circular dependency
from tools.render.protocol import Renderer as Renderer  # noqa: E402

__all__ = [
    # Core data contract
    "RenderFrame",
    # Renderer protocol
    "Renderer",
    # Renderer adapter
    "FrameAdapter",
    # Concrete renderer
    "ConcreteRenderer",
    # Renderer errors
    "RendererError",
    "RenderFrameError",
    "TransformError",
    # Validation
    "RenderSequenceValidation",
    "ValidationError",
    "validate_render_sequence",
    # Preview
    "RenderPreview",
    "PreviewError",
    "create_render_preview",
    # Manifest
    "RenderSequenceManifest",
    "create_render_manifest",
    # Playback
    "RenderPlayback",
    "PlaybackError",
]


def __getattr__(name: str):
    """Lazy import for render functions to avoid circular dependency."""
    if name == "render_frame_to_png":
        from tools.render.integration import render_frame_to_png

        return render_frame_to_png
    if name == "render_frames_to_png":
        from tools.render.sequence import render_frames_to_png

        return render_frames_to_png
    if name == "export_render_frames":
        from tools.render.export import export_render_frames

        return export_render_frames
    if name == "validate_render_sequence":
        from tools.render.validation import validate_render_sequence

        return validate_render_sequence
    if name == "RenderSequenceValidation":
        from tools.render.validation import RenderSequenceValidation

        return RenderSequenceValidation
    if name == "ValidationError":
        from tools.render.validation import ValidationError

        return ValidationError
    if name == "create_render_preview":
        from tools.render.preview import create_render_preview

        return create_render_preview
    if name == "RenderPreview":
        from tools.render.preview import RenderPreview

        return RenderPreview
    if name == "PreviewError":
        from tools.render.preview import PreviewError

        return PreviewError
    if name == "create_render_manifest":
        from tools.render.manifest import create_render_manifest

        return create_render_manifest
    if name == "RenderSequenceManifest":
        from tools.render.manifest import RenderSequenceManifest

        return RenderSequenceManifest
    if name == "RenderPlayback":
        from tools.render.playback import RenderPlayback

        return RenderPlayback
    if name == "PlaybackError":
        from tools.render.playback import PlaybackError

        return PlaybackError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
