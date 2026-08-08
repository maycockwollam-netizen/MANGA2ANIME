"""Render sequence manifest.

Provides immutable metadata describing an already-exported and validated PNG sequence.

This module creates a manifest that describes the existing artifact,
not a new artifact. It delegates validation to the existing layer.

Architecture:
    PNG sequence
        ↓
    create_render_manifest()
        ↓
    RenderSequenceManifest (metadata description)

This module does NOT:
- Create new artifacts
- Modify files
- Encode video
- Launch a UI
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderSequenceManifest:
    """Immutable metadata describing a rendered PNG sequence.

    This manifest describes an already-exported sequence without
    modifying the filesystem or creating new artifacts.

    Attributes:
        output_dir: Directory containing the rendered sequence.
        prefix: Filename prefix used for PNG files.
        frame_count: Total number of frames in the sequence.
        frame_indices: Sorted tuple of frame indices present.
        frame_rate: Frame rate in frames per second (always positive).
        duration_seconds: Total duration computed from frame_count / frame_rate.
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


def create_render_manifest(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    frame_rate: float = 24.0,
) -> RenderSequenceManifest:
    """Create immutable metadata for a validated PNG sequence.

    Validates the sequence using the existing validation layer and
    creates an immutable manifest object describing the sequence.

    Args:
        output_dir: Directory containing the PNG sequence.
        prefix: Filename prefix used for PNG files (default: "frame").
        frame_rate: Frame rate in frames per second (default: 24.0).
            Must be positive.

    Returns:
        RenderSequenceManifest with immutable metadata.

    Raises:
        PreviewError: If frame_rate is not positive.
        ValidationError: If the sequence validation fails.

    Example:
        >>> manifest = create_render_manifest("output_frames")
        >>> print(f"Duration: {manifest.duration_seconds}s")
        >>> print(f"Frames: {manifest.frame_count}")
    """
    if frame_rate <= 0:
        from tools.render.preview import PreviewError

        raise PreviewError(
            f"frame_rate must be positive, got {frame_rate}"
        )

    # Normalize output directory
    output_path = Path(output_dir)

    # Delegate validation to existing validation layer
    from tools.render.validation import (
        RenderSequenceValidation,
        ValidationError,
        validate_render_sequence,
    )

    try:
        validation: RenderSequenceValidation = validate_render_sequence(
            output_path, prefix=prefix
        )
    except ValidationError as e:
        from tools.render.preview import PreviewError

        raise PreviewError(f"Sequence validation failed: {e}") from e

    # Build manifest from validation result
    frame_count = len(validation.frame_indices)
    duration = frame_count / frame_rate

    return RenderSequenceManifest(
        output_dir=output_path,
        prefix=prefix,
        frame_count=frame_count,
        frame_indices=validation.frame_indices,
        frame_rate=frame_rate,
        duration_seconds=duration,
        dimensions=validation.dimensions,
        mode=validation.mode,
    )


__all__ = [
    "RenderSequenceManifest",
    "create_render_manifest",
]
