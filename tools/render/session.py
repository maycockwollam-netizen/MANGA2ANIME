"""Render session orchestration.

Provides a unified, immutable session grouping render sequence artifacts.

This module creates an orchestration layer that combines:
- RenderSequenceManifest (metadata)
- RenderPreview (frame access)
- FrameTimeline (time/frame mapping)
- Playback (navigation controller)

Architecture:
    PNG sequence
        ↓
    Validation
        ↓
    Manifest + Preview + Timeline
        ↓
    RenderSession
        ↓
    Playback

This module does NOT:
- Render anything
- Modify files
- Encode video
- Use threads or async
- Cache state
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.manifest import RenderSequenceManifest
    from tools.render.playback import RenderPlayback
    from tools.render.preview import RenderPreview
    from tools.render.timeline import FrameTimeline


class SessionError(Exception):
    """Error creating or using a render session.

    Raised when session creation fails or inconsistent metadata is detected.
    """

    pass


@dataclass(frozen=True)
class RenderSession:
    """Immutable session grouping render sequence artifacts.

    Provides unified access to:
    - manifest: Metadata (frame_count, dimensions, mode, etc.)
    - preview: Frame access (paths, images)
    - timeline: Time/frame mapping

    Attributes:
        manifest: The sequence metadata.
        preview: Frame paths and image access.
        timeline: Timestamp/frame mapping.

    Note:
        This is an orchestration layer that delegates to existing abstractions.
        It does not render or modify files.
    """

    manifest: RenderSequenceManifest
    preview: RenderPreview
    timeline: FrameTimeline

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sequence."""
        return self.manifest.frame_count

    @property
    def frame_rate(self) -> float:
        """Frame rate in frames per second."""
        return self.manifest.frame_rate

    @property
    def duration_seconds(self) -> float:
        """Total duration of the sequence in seconds."""
        return self.manifest.duration_seconds

    @property
    def dimensions(self) -> tuple[int, int]:
        """Image dimensions as (width, height)."""
        return self.manifest.dimensions

    @property
    def mode(self) -> str:
        """Image mode (e.g., "RGBA", "RGB")."""
        return self.manifest.mode

    def playback(self) -> RenderPlayback:
        """Get a playback controller for this session.

        Each call returns a fresh RenderPlayback instance.

        Returns:
            RenderPlayback configured with this session's preview and frame rate.
        """
        from tools.render.playback import RenderPlayback

        return RenderPlayback(preview=self.preview, frame_rate=self.frame_rate)


def create_render_session(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    frame_rate: float = 24.0,
) -> RenderSession:
    """Create a read-only session over an existing PNG render sequence.

    Validates the sequence and creates unified access to:
    - RenderSequenceManifest
    - RenderPreview
    - FrameTimeline

    Args:
        output_dir: Directory containing the PNG sequence.
        prefix: Filename prefix for PNG files (default: "frame").
        frame_rate: Frame rate for timeline/playback (default: 24.0).
            Must be positive.

    Returns:
        RenderSession with unified access to sequence artifacts.

    Raises:
        SessionError: If session creation fails or metadata is inconsistent.

    Example:
        >>> session = create_render_session("output_frames")
        >>> print(f"Frames: {session.frame_count}")
        >>> print(f"Duration: {session.duration_seconds}s")
        >>> playback = session.playback()
    """
    from tools.render.manifest import (
        create_render_manifest,
    )
    from tools.render.preview import (
        create_render_preview,
    )
    from tools.render.timeline import (
        create_frame_timeline_from_preview,
    )

    # Create artifacts using existing APIs
    try:
        manifest: RenderSequenceManifest = create_render_manifest(
            output_dir, prefix=prefix, frame_rate=frame_rate
        )
    except Exception as e:
        raise SessionError(f"Failed to create manifest: {e}") from e

    try:
        preview: RenderPreview = create_render_preview(
            output_dir, prefix=prefix, frame_rate=frame_rate
        )
    except Exception as e:
        raise SessionError(f"Failed to create preview: {e}") from e

    try:
        timeline: FrameTimeline = create_frame_timeline_from_preview(preview)
    except Exception as e:
        raise SessionError(f"Failed to create timeline: {e}") from e

    # Verify consistency between artifacts
    _verify_consistency(manifest, preview, timeline)

    return RenderSession(
        manifest=manifest,
        preview=preview,
        timeline=timeline,
    )


def _verify_consistency(
    manifest: RenderSequenceManifest,
    preview: RenderPreview,
    timeline: FrameTimeline,
) -> None:
    """Verify metadata consistency between session artifacts.

    Raises:
        SessionError: If inconsistencies are detected.
    """
    # Frame indices must match
    if manifest.frame_indices != preview.frame_indices:
        raise SessionError(
            f"Inconsistent frame_indices: manifest={manifest.frame_indices}, "
            f"preview={preview.frame_indices}"
        )

    if manifest.frame_indices != timeline.frame_indices:
        raise SessionError(
            f"Inconsistent frame_indices: manifest={manifest.frame_indices}, "
            f"timeline={timeline.frame_indices}"
        )

    # Frame count must match
    if manifest.frame_count != preview.frame_count:
        raise SessionError(
            f"Inconsistent frame_count: manifest={manifest.frame_count}, "
            f"preview={preview.frame_count}"
        )

    if manifest.frame_count != timeline.frame_count:
        raise SessionError(
            f"Inconsistent frame_count: manifest={manifest.frame_count}, "
            f"timeline={timeline.frame_count}"
        )

    # Frame rate must match
    if manifest.frame_rate != preview.frame_rate:
        raise SessionError(
            f"Inconsistent frame_rate: manifest={manifest.frame_rate}, "
            f"preview={preview.frame_rate}"
        )

    if manifest.frame_rate != timeline.frame_rate:
        raise SessionError(
            f"Inconsistent frame_rate: manifest={manifest.frame_rate}, "
            f"timeline={timeline.frame_rate}"
        )

    # Duration must match
    if manifest.duration_seconds != preview.duration_seconds:
        raise SessionError(
            f"Inconsistent duration_seconds: manifest={manifest.duration_seconds}, "
            f"preview={preview.duration_seconds}"
        )

    if manifest.duration_seconds != timeline.duration_seconds:
        raise SessionError(
            f"Inconsistent duration_seconds: manifest={manifest.duration_seconds}, "
            f"timeline={timeline.duration_seconds}"
        )


__all__ = [
    "RenderSession",
    "SessionError",
    "create_render_session",
]
