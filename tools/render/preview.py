"""Render sequence preview.

Provides read-only inspection of exported PNG sequences.

This module creates a preview abstraction that allows consumers to inspect
and retrieve rendered PNG frames in deterministic playback order.

Architecture:
    PNG sequence
        ↓
    create_render_preview()
        ↓
    RenderPreview (inspection abstraction)

This module does NOT:
- Render anything
- Modify files
- Encode video
- Launch a UI
- Add caching
- Introduce async behavior

Preview is an inspection/playback abstraction over existing PNG sequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class RenderPreview:
    """Immutable preview of a rendered PNG sequence.

    Provides read-only access to frame paths and image data without
    modifying the filesystem or caching images.

    Attributes:
        frame_paths: Immutable tuple of PNG file paths in frame index order.
        frame_indices: Immutable tuple of frame indices in sorted order.
        frame_rate: Frame rate in frames per second (must be positive).
        duration_seconds: Total duration computed from frame_count / frame_rate.
    """

    frame_paths: tuple[Path, ...]
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sequence."""
        return len(self.frame_indices)

    def frame_path(self, frame_index: int) -> Path:
        """Get the PNG path for a specific frame index.

        Args:
            frame_index: The frame index to look up.

        Returns:
            Path to the PNG file for that frame.

        Raises:
            ValueError: If frame_index is not in the sequence.
        """
        try:
            idx = self.frame_indices.index(frame_index)
            return self.frame_paths[idx]
        except ValueError:
            raise ValueError(
                f"Frame index {frame_index} not found in sequence. "
                f"Available indices: {self.frame_indices}"
            ) from None

    def frame_image(self, frame_index: int) -> Image.Image:
        """Load and return the PNG image for a specific frame index.

        The image is loaded fresh each call (no caching). The returned
        image is not modified.

        Args:
            frame_index: The frame index to load.

        Returns:
            PIL Image in its original mode and dimensions.

        Raises:
            ValueError: If frame_index is not in the sequence.
        """
        path = self.frame_path(frame_index)
        return Image.open(path)


class PreviewError(Exception):
    """Error creating or using a render preview.

    Raised when preview creation fails (e.g., validation failure)
    or when invalid operations are attempted.
    """

    pass


def create_render_preview(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    frame_rate: float = 24.0,
) -> RenderPreview:
    """Create a preview for an exported PNG sequence.

    Validates the sequence using the existing validation layer and
    creates an immutable preview object for inspection.

    Args:
        output_dir: Directory containing the PNG sequence.
        prefix: Filename prefix used for PNG files (default: "frame").
        frame_rate: Frame rate in frames per second (default: 24.0).
            Must be positive.

    Returns:
        RenderPreview with immutable frame metadata.

    Raises:
        PreviewError: If frame_rate is not positive.
        ValidationError: If the sequence validation fails.

    Example:
        >>> preview = create_render_preview("output_frames")
        >>> print(f"Duration: {preview.duration_seconds}s")
        >>> img = preview.frame_image(0)
    """
    if frame_rate <= 0:
        raise PreviewError(
            f"frame_rate must be positive, got {frame_rate}"
        )

    # Delegate validation to existing validation layer
    from tools.render.validation import (
        RenderSequenceValidation,
        ValidationError,
        validate_render_sequence,
    )

    try:
        validation: RenderSequenceValidation = validate_render_sequence(
            output_dir, prefix=prefix
        )
    except ValidationError as e:
        raise PreviewError(f"Sequence validation failed: {e}") from e

    # Build frame paths in the same order as frame_indices
    output_path = Path(output_dir)
    frame_paths: list[Path] = []
    for idx in validation.frame_indices:
        frame_paths.append(output_path / f"{prefix}_{idx:06d}.png")

    duration = len(validation.frame_indices) / frame_rate

    return RenderPreview(
        frame_paths=tuple(frame_paths),
        frame_indices=validation.frame_indices,
        frame_rate=frame_rate,
        duration_seconds=duration,
    )


__all__ = [
    "RenderPreview",
    "PreviewError",
    "create_render_preview",
]
