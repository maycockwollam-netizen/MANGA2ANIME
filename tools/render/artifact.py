"""Render artifact snapshot.

Provides an immutable snapshot of a RenderSession's validated state.

This module creates a read-only artifact object that captures the essential
metadata of a render sequence without modification.

Architecture:
    RenderSession
        ↓
    create_render_artifact()
        ↓
    RenderArtifact (immutable snapshot)

This module does NOT:
- Modify files
- Create files
- Delete files
- Render anything
- Use threads or async
- Cache data
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.session import RenderSession


@dataclass(frozen=True)
class RenderArtifact:
    """Immutable snapshot of a render sequence's validated state.

    Attributes:
        output_dir: Directory containing the PNG sequence.
        prefix: Filename prefix used for PNG files.
        frame_count: Total number of frames in the sequence.
        frame_indices: Sorted tuple of frame indices.
        frame_rate: Frame rate in frames per second.
        duration_seconds: Total duration in seconds.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
    """

    output_dir: Path
    prefix: str
    frame_count: int
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str


class ArtifactError(Exception):
    """Error creating or accessing a render artifact.

    Raised when artifact creation fails due to validation errors or invalid input.
    """

    pass


def create_render_artifact(
    session: RenderSession,
    *,
    validate: bool = True,
) -> RenderArtifact:
    """Create an immutable artifact snapshot from a RenderSession.

    Args:
        session: The RenderSession to snapshot.
        validate: If True, validate the session before creating the artifact.
            If False, skip validation.

    Returns:
        RenderArtifact with immutable session metadata.

    Raises:
        ArtifactError: If validation fails or session is invalid.

    Example:
        >>> session = create_render_session("output_frames")
        >>> artifact = create_render_artifact(session)
        >>> print(f"Frames: {artifact.frame_count}")
    """
    # Optionally validate the session first
    if validate:
        from tools.render.session_validation import (
            SessionValidationError,
            validate_render_session,
        )

        try:
            validate_render_session(session)
        except SessionValidationError as e:
            raise ArtifactError(
                f"Session validation failed: {e}"
            ) from e

    # Extract metadata from session
    manifest = session.manifest

    return RenderArtifact(
        output_dir=manifest.output_dir,
        prefix=manifest.prefix,
        frame_count=manifest.frame_count,
        frame_indices=manifest.frame_indices,
        frame_rate=manifest.frame_rate,
        duration_seconds=manifest.duration_seconds,
        dimensions=manifest.dimensions,
        mode=manifest.mode,
    )


__all__ = [
    "RenderArtifact",
    "ArtifactError",
    "create_render_artifact",
]
