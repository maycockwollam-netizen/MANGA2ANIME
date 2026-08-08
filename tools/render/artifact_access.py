"""Render artifact access.

Provides read-only access to information and frames from a LoadedRenderArtifact.

This module provides utilities to inspect artifact metadata and access individual
frames without modifying anything.

Architecture:
    LoadedRenderArtifact
        ↓
    get_artifact_info()
        ↓
    RenderArtifactInfo

    LoadedRenderArtifact
        ↓
    get_artifact_frame_path()
        ↓
    Path

    LoadedRenderArtifact
        ↓
    get_artifact_frame_image()
        ↓
    Image.Image

    LoadedRenderArtifact + timestamp
        ↓
    get_artifact_frame_at_timestamp()
        ↓
    Image.Image

This module does NOT:
- Modify files
- Create files
- Delete files
- Cache data
- Use threads or async
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImage

    from tools.render.artifact_loader import LoadedRenderArtifact


@dataclass(frozen=True)
class RenderArtifactInfo:
    """Immutable information about a render artifact.

    Attributes:
        output_dir: Directory containing PNG frames.
        prefix: Filename prefix for frames.
        frame_count: Total number of frames.
        frame_indices: Sorted tuple of frame indices.
        frame_rate: Frame rate in frames per second.
        duration_seconds: Total duration in seconds.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
        first_frame_index: Index of the first frame.
        last_frame_index: Index of the last frame.
    """

    output_dir: Path
    prefix: str
    frame_count: int
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str
    first_frame_index: int
    last_frame_index: int


class ArtifactAccessError(Exception):
    """Error accessing information from a loaded render artifact.

    Raised when frame access fails due to invalid index or timestamp.
    """

    pass


def get_artifact_info(
    loaded: LoadedRenderArtifact,
) -> RenderArtifactInfo:
    """Get immutable information about a loaded render artifact.

    Args:
        loaded: The loaded render artifact.

    Returns:
        RenderArtifactInfo with artifact metadata.

    Example:
        >>> info = get_artifact_info(loaded)
        >>> print(f"Frames: {info.frame_count}")
    """
    artifact = loaded.artifact

    return RenderArtifactInfo(
        output_dir=artifact.output_dir,
        prefix=artifact.prefix,
        frame_count=artifact.frame_count,
        frame_indices=artifact.frame_indices,
        frame_rate=artifact.frame_rate,
        duration_seconds=artifact.duration_seconds,
        dimensions=artifact.dimensions,
        mode=artifact.mode,
        first_frame_index=artifact.frame_indices[0] if artifact.frame_indices else 0,
        last_frame_index=artifact.frame_indices[-1] if artifact.frame_indices else 0,
    )


def get_artifact_frame_path(
    loaded: LoadedRenderArtifact,
    frame_index: int,
) -> Path:
    """Get the path to a specific frame in the artifact.

    Args:
        loaded: The loaded render artifact.
        frame_index: Index of the frame to retrieve.

    Returns:
        Path to the PNG file for the specified frame.

    Raises:
        ArtifactAccessError: If frame_index is invalid.

    Example:
        >>> path = get_artifact_frame_path(loaded, 0)
        >>> print(f"Frame 0: {path}")
    """
    artifact = loaded.artifact

    if frame_index not in artifact.frame_indices:
        raise ArtifactAccessError(
            f"Invalid frame_index: {frame_index}. "
            f"Valid indices: {artifact.frame_indices}"
        )

    frame_pattern = artifact.prefix + "_" + str(frame_index).zfill(6) + ".png"
    return artifact.output_dir / frame_pattern


def get_artifact_frame_image(
    loaded: LoadedRenderArtifact,
    frame_index: int,
) -> PILImage.Image:
    """Get the image data for a specific frame in the artifact.

    Args:
        loaded: The loaded render artifact.
        frame_index: Index of the frame to retrieve.

    Returns:
        PIL Image for the specified frame.

    Raises:
        ArtifactAccessError: If frame_index is invalid or image cannot be loaded.

    Example:
        >>> image = get_artifact_frame_image(loaded, 0)
        >>> print(f"Frame 0 size: {image.size}")
    """
    from PIL import Image

    frame_path = get_artifact_frame_path(loaded, frame_index)

    try:
        return Image.open(frame_path)
    except Exception as e:
        raise ArtifactAccessError(
            f"Failed to load frame {frame_index}: {e}"
        ) from e


def get_artifact_frame_at_timestamp(
    loaded: LoadedRenderArtifact,
    timestamp: float,
) -> PILImage.Image:
    """Get the frame at a specific timestamp.

    Uses the frame rate from the artifact to calculate which frame
    corresponds to the given timestamp.

    Args:
        loaded: The loaded render artifact.
        timestamp: Timestamp in seconds.

    Returns:
        PIL Image for the frame at the specified timestamp.

    Raises:
        ArtifactAccessError: If timestamp is invalid.

    Example:
        >>> image = get_artifact_frame_at_timestamp(loaded, 0.5)
        >>> print(f"Frame at 0.5s size: {image.size}")
    """
    artifact = loaded.artifact

    if timestamp < 0:
        raise ArtifactAccessError(
            f"Timestamp cannot be negative: {timestamp}"
        )

    if timestamp > artifact.duration_seconds:
        raise ArtifactAccessError(
            f"Timestamp {timestamp} exceeds duration {artifact.duration_seconds}"
        )

    # Calculate frame index from timestamp
    frame_index = int(timestamp * artifact.frame_rate)

    # Clamp to valid range
    frame_index = max(artifact.frame_indices[0], min(frame_index, artifact.frame_indices[-1]))

    return get_artifact_frame_image(loaded, frame_index)


__all__ = [
    "RenderArtifactInfo",
    "ArtifactAccessError",
    "get_artifact_info",
    "get_artifact_frame_path",
    "get_artifact_frame_image",
    "get_artifact_frame_at_timestamp",
]
