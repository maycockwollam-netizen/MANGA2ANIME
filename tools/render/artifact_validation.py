"""Render artifact validation.

Provides integrity verification for RenderArtifact against the PNG sequence on disk.

This module validates that an artifact's metadata still matches the actual PNG files
without modifying anything.

Architecture:
    RenderArtifact
        ↓
    validate_render_artifact()
        ↓
    RenderArtifactValidation (or exception)

This module does NOT:
- Modify files
- Create files
- Delete files
- Calculate checksums
- Use threads or async
- Cache data
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.artifact import RenderArtifact


@dataclass(frozen=True)
class RenderArtifactValidation:
    """Immutable validation result for a RenderArtifact.

    Attributes:
        frame_count: Total number of frames validated.
        frame_indices: Sorted tuple of frame indices validated.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
        valid: Always True for a successful validation result.
    """

    frame_count: int
    frame_indices: tuple[int, ...]
    dimensions: tuple[int, int]
    mode: str
    valid: bool


class ArtifactValidationError(Exception):
    """Error validating a RenderArtifact.

    Raised when artifact validation fails due to mismatch or corruption.
    """

    pass


def validate_render_artifact(
    artifact: RenderArtifact,
) -> RenderArtifactValidation:
    """Verify that a RenderArtifact still matches the PNG sequence on disk.

    Validates:
    1. PNG sequence validity via validate_render_sequence()
    2. Artifact metadata consistency (frame_count, frame_indices, dimensions, mode)

    Args:
        artifact: The RenderArtifact to validate.

    Returns:
        RenderArtifactValidation with validated metadata.

    Raises:
        ArtifactValidationError: If validation fails.

    Example:
        >>> artifact = create_render_artifact(session)
        >>> result = validate_render_artifact(artifact)
        >>> print(f"Valid: {result.valid}")
    """
    from tools.render.validation import (
        RenderSequenceValidation,
        ValidationError,
        validate_render_sequence,
    )

    # Validate underlying PNG sequence
    try:
        sequence_validation: RenderSequenceValidation = validate_render_sequence(
            artifact.output_dir,
            prefix=artifact.prefix,
        )
    except ValidationError as e:
        raise ArtifactValidationError(
            f"PNG sequence validation failed: {e}"
        ) from e

    # Verify artifact metadata consistency
    _verify_metadata_match(
        "Artifact", "Sequence",
        artifact.frame_count, sequence_validation.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Artifact", "Sequence",
        artifact.frame_indices, sequence_validation.frame_indices,
        "frame_indices"
    )
    _verify_metadata_match(
        "Artifact", "Sequence",
        artifact.dimensions, sequence_validation.dimensions,
        "dimensions"
    )
    _verify_metadata_match(
        "Artifact", "Sequence",
        artifact.mode, sequence_validation.mode,
        "mode"
    )

    # Verify artifact metadata internal validity
    _verify_artifact_internal_validity(artifact)

    return RenderArtifactValidation(
        frame_count=artifact.frame_count,
        frame_indices=artifact.frame_indices,
        dimensions=artifact.dimensions,
        mode=artifact.mode,
        valid=True,
    )


def _verify_metadata_match(
    source1: str,
    source2: str,
    value1: int | tuple[int, ...] | tuple[int, int] | str,
    value2: int | tuple[int, ...] | tuple[int, int] | str,
    property_name: str,
) -> None:
    """Verify two metadata values match.

    Raises:
        ArtifactValidationError: If values don't match.
    """
    if value1 != value2:
        raise ArtifactValidationError(
            f"Mismatch in {property_name}: {source1}={value1}, {source2}={value2}"
        )


def _verify_artifact_internal_validity(
    artifact: RenderArtifact,
) -> None:
    """Verify artifact metadata is internally valid.

    Raises:
        ArtifactValidationError: If metadata is invalid.
    """
    if artifact.frame_count <= 0:
        raise ArtifactValidationError(
            f"Invalid frame_count: {artifact.frame_count} (must be > 0)"
        )

    if not artifact.frame_indices:
        raise ArtifactValidationError("frame_indices cannot be empty")

    if len(artifact.frame_indices) != len(set(artifact.frame_indices)):
        raise ArtifactValidationError("frame_indices must be unique")

    if artifact.frame_rate <= 0:
        raise ArtifactValidationError(
            f"Invalid frame_rate: {artifact.frame_rate} (must be > 0)"
        )

    if artifact.duration_seconds < 0:
        raise ArtifactValidationError(
            f"Invalid duration_seconds: {artifact.duration_seconds} (must be >= 0)"
        )


__all__ = [
    "RenderArtifactValidation",
    "ArtifactValidationError",
    "validate_render_artifact",
]
