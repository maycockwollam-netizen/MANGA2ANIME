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
    # Timeline
    "FrameTimeline",
    "TimelineError",
    "create_frame_timeline",
    "create_frame_timeline_from_preview",
    # Session
    "RenderSession",
    "SessionError",
    "create_render_session",
    # Session Access
    "RenderSessionInfo",
    "SessionAccessError",
    "get_session_info",
    "get_frame_image",
    "get_frame_path",
    "get_frame_at_timestamp",
    # Session Validation
    "RenderSessionValidation",
    "SessionValidationError",
    "validate_render_session",
    # Artifact
    "RenderArtifact",
    "ArtifactError",
    "create_render_artifact",
    # Artifact Validation
    "RenderArtifactValidation",
    "ArtifactValidationError",
    "validate_render_artifact",
    # Artifact Manifest
    "RenderArtifactManifest",
    "ArtifactManifestError",
    "create_artifact_manifest",
    "artifact_manifest_to_dict",
    "artifact_manifest_from_dict",
    "write_artifact_manifest",
    "read_artifact_manifest",
    # Artifact Manifest Validation
    "RenderArtifactManifestValidation",
    "ArtifactManifestValidationError",
    "validate_artifact_manifest",
    # Artifact Loader
    "LoadedRenderArtifact",
    "ArtifactLoadError",
    "load_render_artifact",
    # Artifact Access
    "RenderArtifactInfo",
    "ArtifactAccessError",
    "get_artifact_info",
    "get_artifact_frame_path",
    "get_artifact_frame_image",
    "get_artifact_frame_at_timestamp",
    # Artifact Integration
    "RenderArtifactHandle",
    "ArtifactIntegrationError",
    "open_render_artifact",
    "validate_render_artifact_handle",
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
    if name == "create_frame_timeline":
        from tools.render.timeline import create_frame_timeline

        return create_frame_timeline
    if name == "FrameTimeline":
        from tools.render.timeline import FrameTimeline

        return FrameTimeline
    if name == "TimelineError":
        from tools.render.timeline import TimelineError

        return TimelineError
    if name == "create_frame_timeline_from_preview":
        from tools.render.timeline import create_frame_timeline_from_preview

        return create_frame_timeline_from_preview
    if name == "create_render_session":
        from tools.render.session import create_render_session

        return create_render_session
    if name == "RenderSession":
        from tools.render.session import RenderSession

        return RenderSession
    if name == "SessionError":
        from tools.render.session import SessionError

        return SessionError
    if name == "get_session_info":
        from tools.render.session_access import get_session_info

        return get_session_info
    if name == "RenderSessionInfo":
        from tools.render.session_access import RenderSessionInfo

        return RenderSessionInfo
    if name == "SessionAccessError":
        from tools.render.session_access import SessionAccessError

        return SessionAccessError
    if name == "get_frame_image":
        from tools.render.session_access import get_frame_image

        return get_frame_image
    if name == "get_frame_path":
        from tools.render.session_access import get_frame_path

        return get_frame_path
    if name == "get_frame_at_timestamp":
        from tools.render.session_access import get_frame_at_timestamp

        return get_frame_at_timestamp
    if name == "validate_render_session":
        from tools.render.session_validation import validate_render_session

        return validate_render_session
    if name == "RenderSessionValidation":
        from tools.render.session_validation import RenderSessionValidation

        return RenderSessionValidation
    if name == "SessionValidationError":
        from tools.render.session_validation import SessionValidationError

        return SessionValidationError
    if name == "create_render_artifact":
        from tools.render.artifact import create_render_artifact

        return create_render_artifact
    if name == "RenderArtifact":
        from tools.render.artifact import RenderArtifact

        return RenderArtifact
    if name == "ArtifactError":
        from tools.render.artifact import ArtifactError

        return ArtifactError
    if name == "validate_render_artifact":
        from tools.render.artifact_validation import validate_render_artifact

        return validate_render_artifact
    if name == "RenderArtifactValidation":
        from tools.render.artifact_validation import RenderArtifactValidation

        return RenderArtifactValidation
    if name == "ArtifactValidationError":
        from tools.render.artifact_validation import ArtifactValidationError

        return ArtifactValidationError
    if name == "create_artifact_manifest":
        from tools.render.artifact_manifest import create_artifact_manifest

        return create_artifact_manifest
    if name == "artifact_manifest_to_dict":
        from tools.render.artifact_manifest import artifact_manifest_to_dict

        return artifact_manifest_to_dict
    if name == "artifact_manifest_from_dict":
        from tools.render.artifact_manifest import artifact_manifest_from_dict

        return artifact_manifest_from_dict
    if name == "write_artifact_manifest":
        from tools.render.artifact_manifest import write_artifact_manifest

        return write_artifact_manifest
    if name == "read_artifact_manifest":
        from tools.render.artifact_manifest import read_artifact_manifest

        return read_artifact_manifest
    if name == "RenderArtifactManifest":
        from tools.render.artifact_manifest import RenderArtifactManifest

        return RenderArtifactManifest
    if name == "ArtifactManifestError":
        from tools.render.artifact_manifest import ArtifactManifestError

        return ArtifactManifestError
    if name == "validate_artifact_manifest":
        from tools.render.artifact_manifest_validation import validate_artifact_manifest

        return validate_artifact_manifest
    if name == "RenderArtifactManifestValidation":
        from tools.render.artifact_manifest_validation import RenderArtifactManifestValidation

        return RenderArtifactManifestValidation
    if name == "ArtifactManifestValidationError":
        from tools.render.artifact_manifest_validation import ArtifactManifestValidationError

        return ArtifactManifestValidationError
    if name == "load_render_artifact":
        from tools.render.artifact_loader import load_render_artifact

        return load_render_artifact
    if name == "LoadedRenderArtifact":
        from tools.render.artifact_loader import LoadedRenderArtifact

        return LoadedRenderArtifact
    if name == "ArtifactLoadError":
        from tools.render.artifact_loader import ArtifactLoadError

        return ArtifactLoadError
    if name == "get_artifact_info":
        from tools.render.artifact_access import get_artifact_info

        return get_artifact_info
    if name == "get_artifact_frame_path":
        from tools.render.artifact_access import get_artifact_frame_path

        return get_artifact_frame_path
    if name == "get_artifact_frame_image":
        from tools.render.artifact_access import get_artifact_frame_image

        return get_artifact_frame_image
    if name == "get_artifact_frame_at_timestamp":
        from tools.render.artifact_access import get_artifact_frame_at_timestamp

        return get_artifact_frame_at_timestamp
    if name == "RenderArtifactInfo":
        from tools.render.artifact_access import RenderArtifactInfo

        return RenderArtifactInfo
    if name == "ArtifactAccessError":
        from tools.render.artifact_access import ArtifactAccessError

        return ArtifactAccessError
    if name == "RenderArtifactHandle":
        from tools.render.artifact_integration import RenderArtifactHandle

        return RenderArtifactHandle
    if name == "ArtifactIntegrationError":
        from tools.render.artifact_integration import ArtifactIntegrationError

        return ArtifactIntegrationError
    if name == "open_render_artifact":
        from tools.render.artifact_integration import open_render_artifact

        return open_render_artifact
    if name == "validate_render_artifact_handle":
        from tools.render.artifact_integration import validate_render_artifact_handle

        return validate_render_artifact_handle
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
