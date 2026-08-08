"""Render artifact manifest validation.

Provides integrity verification for RenderArtifactManifest against
RenderArtifact and its PNG sequence.

This module validates that a manifest's metadata matches both the artifact
and the actual PNG files on disk.

Architecture:
    RenderArtifact + RenderArtifactManifest
        ↓
    validate_artifact_manifest()
        ↓
    RenderArtifactManifestValidation (or exception)

This module does NOT:
- Modify files
- Create files
- Delete files
- Use threads or async
- Cache data
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.artifact import RenderArtifact
    from tools.render.artifact_manifest import RenderArtifactManifest


@dataclass(frozen=True)
class RenderArtifactManifestValidation:
    """Immutable validation result for RenderArtifactManifest.

    Attributes:
        valid: Always True for a successful validation result.
        frame_count: Total number of frames validated.
        frame_indices: Sorted tuple of frame indices validated.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
    """

    valid: bool
    frame_count: int
    frame_indices: tuple[int, ...]
    dimensions: tuple[int, int]
    mode: str


class ArtifactManifestValidationError(Exception):
    """Error validating a RenderArtifactManifest.

    Raised when manifest validation fails due to mismatch or corruption.
    """

    pass


def validate_artifact_manifest(
    artifact: RenderArtifact,
    manifest: RenderArtifactManifest,
) -> RenderArtifactManifestValidation:
    """Validate a manifest against an artifact and its PNG sequence.

    Verifies:
    1. Manifest metadata consistency
    2. Manifest vs Artifact metadata match
    3. Manifest vs PNG sequence match

    Args:
        artifact: The RenderArtifact to validate against.
        manifest: The RenderArtifactManifest to verify.

    Returns:
        RenderArtifactManifestValidation with validated metadata.

    Raises:
        ArtifactManifestValidationError: If validation fails.

    Example:
        >>> artifact = create_render_artifact(session)
        >>> manifest = create_artifact_manifest(artifact)
        >>> result = validate_artifact_manifest(artifact, manifest)
        >>> print(f"Valid: {result.valid}")
    """
    from tools.render.artifact_validation import (
        ArtifactValidationError,
        validate_render_artifact,
    )

    # Step 1: Validate the artifact itself
    try:
        validate_render_artifact(artifact)
    except ArtifactValidationError as e:
        raise ArtifactManifestValidationError(
            f"Artifact validation failed: {e}"
        ) from e

    # Step 2: Verify manifest vs artifact metadata
    _verify_match(
        "Manifest", "Artifact", "output_dir",
        manifest.output_dir, str(artifact.output_dir)
    )
    _verify_match(
        "Manifest", "Artifact", "prefix",
        manifest.prefix, artifact.prefix
    )
    _verify_match(
        "Manifest", "Artifact", "frame_count",
        manifest.frame_count, artifact.frame_count
    )
    _verify_match(
        "Manifest", "Artifact", "frame_indices",
        manifest.frame_indices, artifact.frame_indices
    )
    _verify_match(
        "Manifest", "Artifact", "frame_rate",
        manifest.frame_rate, artifact.frame_rate
    )
    _verify_match(
        "Manifest", "Artifact", "duration_seconds",
        manifest.duration_seconds, artifact.duration_seconds
    )
    _verify_match(
        "Manifest", "Artifact", "dimensions",
        manifest.dimensions, artifact.dimensions
    )
    _verify_match(
        "Manifest", "Artifact", "mode",
        manifest.mode, artifact.mode
    )

    # Step 3: Verify manifest vs PNG sequence
    from tools.render.validation import (
        RenderSequenceValidation,
        ValidationError,
        validate_render_sequence,
    )

    try:
        sequence_validation: RenderSequenceValidation = validate_render_sequence(
            artifact.output_dir,
            prefix=artifact.prefix,
        )
    except ValidationError as e:
        raise ArtifactManifestValidationError(
            f"PNG sequence validation failed: {e}"
        ) from e

    # Compare manifest against sequence
    _verify_match(
        "Manifest", "Sequence", "frame_count",
        manifest.frame_count, sequence_validation.frame_count
    )
    _verify_match(
        "Manifest", "Sequence", "frame_indices",
        manifest.frame_indices, sequence_validation.frame_indices
    )
    _verify_match(
        "Manifest", "Sequence", "dimensions",
        manifest.dimensions, sequence_validation.dimensions
    )
    _verify_match(
        "Manifest", "Sequence", "mode",
        manifest.mode, sequence_validation.mode
    )

    # Step 4: Verify manifest internal validity
    _verify_manifest_validity(manifest)

    return RenderArtifactManifestValidation(
        valid=True,
        frame_count=manifest.frame_count,
        frame_indices=manifest.frame_indices,
        dimensions=manifest.dimensions,
        mode=manifest.mode,
    )


def _verify_match(
    source1: str,
    source2: str,
    property_name: str,
    value1: int | float | tuple[int, ...] | tuple[int, int] | str,
    value2: int | float | tuple[int, ...] | tuple[int, int] | str,
) -> None:
    """Verify two values match.

    Raises:
        ArtifactManifestValidationError: If values don't match.
    """
    if value1 != value2:
        raise ArtifactManifestValidationError(
            f"Mismatch in {property_name}: {source1}={value1}, {source2}={value2}"
        )


def _verify_manifest_validity(
    manifest: RenderArtifactManifest,
) -> None:
    """Verify manifest metadata is internally valid.

    Raises:
        ArtifactManifestValidationError: If metadata is invalid.
    """
    import math

    if manifest.frame_count <= 0:
        raise ArtifactManifestValidationError(
            f"Invalid frame_count: {manifest.frame_count} (must be > 0)"
        )

    if not manifest.frame_indices:
        raise ArtifactManifestValidationError("frame_indices cannot be empty")

    if len(manifest.frame_indices) != len(set(manifest.frame_indices)):
        raise ArtifactManifestValidationError("frame_indices must be unique")

    if manifest.frame_rate <= 0:
        raise ArtifactManifestValidationError(
            f"Invalid frame_rate: {manifest.frame_rate} (must be > 0)"
        )

    if math.isnan(manifest.frame_rate) or math.isinf(manifest.frame_rate):
        raise ArtifactManifestValidationError(
            f"Invalid frame_rate: {manifest.frame_rate} (must be finite)"
        )

    if manifest.duration_seconds < 0:
        raise ArtifactManifestValidationError(
            f"Invalid duration_seconds: {manifest.duration_seconds} (must be >= 0)"
        )

    if math.isnan(manifest.duration_seconds) or math.isinf(manifest.duration_seconds):
        raise ArtifactManifestValidationError(
            f"Invalid duration_seconds: {manifest.duration_seconds} (must be finite)"
        )

    if not manifest.mode:
        raise ArtifactManifestValidationError("mode cannot be empty")

    if not manifest.prefix:
        raise ArtifactManifestValidationError("prefix cannot be empty")


__all__ = [
    "RenderArtifactManifestValidation",
    "ArtifactManifestValidationError",
    "validate_artifact_manifest",
]
