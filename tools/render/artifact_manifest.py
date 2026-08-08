"""Render artifact manifest.

Provides deterministic metadata serialization for RenderArtifact.

This module serializes RenderArtifact metadata to/from JSON without
modifying any PNG files or introducing external dependencies.

Architecture:
    RenderArtifact
        ↓
    create_artifact_manifest()
        ↓
    RenderArtifactManifest
        ↓
    artifact_manifest_to_dict() / artifact_manifest_to_json()
        ↓
    JSON (deterministic)
        ↓
    artifact_manifest_from_dict() / read_artifact_manifest()
        ↓
    RenderArtifactManifest

This module does NOT:
- Modify PNG files
- Serialize image data
- Create parent directories
- Use external dependencies
- Cache data
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

if True:
    from tools.render.artifact import RenderArtifact


@dataclass(frozen=True)
class RenderArtifactManifest:
    """Immutable manifest of RenderArtifact metadata.

    Attributes:
        output_dir: Directory containing the PNG sequence (as string).
        prefix: Filename prefix used for PNG files.
        frame_count: Total number of frames in the sequence.
        frame_indices: Sorted tuple of frame indices.
        frame_rate: Frame rate in frames per second.
        duration_seconds: Total duration in seconds.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
    """

    output_dir: str
    prefix: str
    frame_count: int
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str


class ArtifactManifestError(Exception):
    """Error creating or reading a render artifact manifest.

    Raised when manifest operations fail due to invalid data or I/O errors.
    """

    pass


def create_artifact_manifest(
    artifact: RenderArtifact,
) -> RenderArtifactManifest:
    """Create an immutable metadata manifest from a RenderArtifact.

    Args:
        artifact: The RenderArtifact to serialize.

    Returns:
        RenderArtifactManifest with all metadata.

    Example:
        >>> manifest = create_artifact_manifest(artifact)
        >>> print(f"Frames: {manifest.frame_count}")
    """
    return RenderArtifactManifest(
        output_dir=str(artifact.output_dir),
        prefix=artifact.prefix,
        frame_count=artifact.frame_count,
        frame_indices=artifact.frame_indices,
        frame_rate=artifact.frame_rate,
        duration_seconds=artifact.duration_seconds,
        dimensions=artifact.dimensions,
        mode=artifact.mode,
    )


def artifact_manifest_to_dict(
    manifest: RenderArtifactManifest,
) -> dict[str, object]:
    """Convert an artifact manifest to deterministic JSON-compatible data.

    Args:
        manifest: The manifest to convert.

    Returns:
        Dictionary with JSON-compatible values and deterministic ordering.

    Example:
        >>> data = artifact_manifest_to_dict(manifest)
        >>> json_str = json.dumps(data, sort_keys=True)
    """
    return {
        "output_dir": manifest.output_dir,
        "prefix": manifest.prefix,
        "frame_count": manifest.frame_count,
        "frame_indices": list(manifest.frame_indices),
        "frame_rate": manifest.frame_rate,
        "duration_seconds": manifest.duration_seconds,
        "dimensions": list(manifest.dimensions),
        "mode": manifest.mode,
    }


def artifact_manifest_from_dict(
    data: Mapping[str, object],
) -> RenderArtifactManifest:
    """Reconstruct an artifact manifest from JSON-compatible data.

    Args:
        data: Dictionary with manifest data.

    Returns:
        RenderArtifactManifest reconstructed from data.

    Raises:
        ArtifactManifestError: If data is invalid or incomplete.

    Example:
        >>> manifest = artifact_manifest_from_dict(data)
    """
    # Check for required fields
    required_fields = {
        "output_dir", "prefix", "frame_count", "frame_indices",
        "frame_rate", "duration_seconds", "dimensions", "mode"
    }
    actual_keys = set(data.keys())
    missing = required_fields - actual_keys
    if missing:
        raise ArtifactManifestError(
            f"Missing required fields: {sorted(missing)}"
        )
    extra = actual_keys - required_fields
    if extra:
        raise ArtifactManifestError(
            f"Unexpected fields: {sorted(extra)}"
        )

    # Validate output_dir
    output_dir = data.get("output_dir")
    if not isinstance(output_dir, str):
        raise ArtifactManifestError(
            f"output_dir must be a string, got {type(output_dir).__name__}"
        )

    # Validate prefix
    prefix = data.get("prefix")
    if not isinstance(prefix, str):
        raise ArtifactManifestError(
            f"prefix must be a string, got {type(prefix).__name__}"
        )

    # Validate frame_count
    frame_count = data.get("frame_count")
    if not isinstance(frame_count, int) or isinstance(frame_count, bool):
        raise ArtifactManifestError(
            f"frame_count must be an int, got {type(frame_count).__name__}"
        )
    if frame_count <= 0:
        raise ArtifactManifestError(
            f"frame_count must be > 0, got {frame_count}"
        )

    # Validate frame_indices
    frame_indices = data.get("frame_indices")
    if not isinstance(frame_indices, (list, tuple)):
        raise ArtifactManifestError(
            f"frame_indices must be a list or tuple, got {type(frame_indices).__name__}"
        )
    if not frame_indices:
        raise ArtifactManifestError("frame_indices cannot be empty")
    for idx in frame_indices:
        if not isinstance(idx, int) or isinstance(idx, bool):
            raise ArtifactManifestError(
                f"frame_indices must contain ints, found {type(idx).__name__}"
            )
    if len(frame_indices) != len(set(frame_indices)):
        raise ArtifactManifestError("frame_indices must be unique")

    # Validate frame_rate
    frame_rate = data.get("frame_rate")
    if not isinstance(frame_rate, (int, float)) or isinstance(frame_rate, bool):
        raise ArtifactManifestError(
            f"frame_rate must be a number, got {type(frame_rate).__name__}"
        )
    if frame_rate <= 0:
        raise ArtifactManifestError(
            f"frame_rate must be > 0, got {frame_rate}"
        )
    import math
    if math.isnan(frame_rate):
        raise ArtifactManifestError("frame_rate cannot be NaN")
    if math.isinf(frame_rate):
        raise ArtifactManifestError("frame_rate cannot be infinite")

    # Validate duration_seconds
    duration_seconds = data.get("duration_seconds")
    if not isinstance(duration_seconds, (int, float)) or isinstance(duration_seconds, bool):
        raise ArtifactManifestError(
            f"duration_seconds must be a number, got {type(duration_seconds).__name__}"
        )
    if duration_seconds < 0:
        raise ArtifactManifestError(
            f"duration_seconds must be >= 0, got {duration_seconds}"
        )
    if math.isnan(duration_seconds):
        raise ArtifactManifestError("duration_seconds cannot be NaN")
    if math.isinf(duration_seconds):
        raise ArtifactManifestError("duration_seconds cannot be infinite")

    # Validate dimensions
    dimensions = data.get("dimensions")
    if not isinstance(dimensions, (list, tuple)) or len(dimensions) != 2:
        raise ArtifactManifestError(
            f"dimensions must be a [width, height] tuple, got {dimensions}"
        )
    for dim in dimensions:
        if not isinstance(dim, int) or isinstance(dim, bool) or dim <= 0:
            raise ArtifactManifestError(
                f"dimensions must contain positive ints, got {dimensions}"
            )

    # Validate mode
    mode = data.get("mode")
    if not isinstance(mode, str):
        raise ArtifactManifestError(
            f"mode must be a string, got {type(mode).__name__}"
        )
    if not mode:
        raise ArtifactManifestError("mode cannot be empty")

    return RenderArtifactManifest(
        output_dir=output_dir,
        prefix=prefix,
        frame_count=frame_count,
        frame_indices=tuple(frame_indices),
        frame_rate=float(frame_rate),
        duration_seconds=float(duration_seconds),
        dimensions=(dimensions[0], dimensions[1]),
        mode=mode,
    )


def write_artifact_manifest(
    manifest: RenderArtifactManifest,
    output_path: Path | str,
) -> None:
    """Write the artifact manifest as deterministic JSON.

    Args:
        manifest: The manifest to write.
        output_path: Path to write the JSON file.

    Raises:
        ArtifactManifestError: If writing fails or file exists.

    Note:
        Does not create parent directories. Caller must ensure
        the parent directory exists.
    """
    output_path = Path(output_path)

    # Check if file already exists
    if output_path.exists():
        raise ArtifactManifestError(
            f"Destination file already exists: {output_path}"
        )

    # Convert to dict and serialize
    data = artifact_manifest_to_dict(manifest)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except OSError as e:
        raise ArtifactManifestError(
            f"Failed to write manifest: {e}"
        ) from e


def read_artifact_manifest(
    input_path: Path | str,
) -> RenderArtifactManifest:
    """Read and validate an artifact manifest from JSON.

    Args:
        input_path: Path to read the JSON file from.

    Returns:
        RenderArtifactManifest reconstructed from the file.

    Raises:
        ArtifactManifestError: If reading or validation fails.

    Note:
        This is a read-only operation that does not modify the filesystem.
    """
    input_path = Path(input_path)

    try:
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise ArtifactManifestError(
            f"Failed to read manifest: {e}"
        ) from e
    except json.JSONDecodeError as e:
        raise ArtifactManifestError(
            f"Invalid JSON: {e}"
        ) from e

    if not isinstance(data, dict):
        raise ArtifactManifestError(
            f"Manifest must be a JSON object, got {type(data).__name__}"
        )

    try:
        return artifact_manifest_from_dict(data)
    except ArtifactManifestError:
        raise
    except Exception as e:
        raise ArtifactManifestError(
            f"Failed to parse manifest: {e}"
        ) from e


__all__ = [
    "RenderArtifactManifest",
    "ArtifactManifestError",
    "create_artifact_manifest",
    "artifact_manifest_to_dict",
    "artifact_manifest_from_dict",
    "write_artifact_manifest",
    "read_artifact_manifest",
]
