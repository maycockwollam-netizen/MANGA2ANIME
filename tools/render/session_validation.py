"""Render session validation.

Provides validation for an already-created RenderSession by verifying internal
consistency between all components.

This module orchestrates existing validation APIs rather than reimplementing them:
- validate_render_sequence() for PNG/image validation
- Direct comparison for metadata consistency

Architecture:
    RenderSession
        ↓
    validate_render_session()
        ↓
    RenderSessionValidation (or exception)

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.manifest import RenderSequenceManifest
    from tools.render.preview import RenderPreview
    from tools.render.session import RenderSession
    from tools.render.timeline import FrameTimeline


@dataclass(frozen=True)
class RenderSessionValidation:
    """Immutable validation result for a RenderSession.

    Attributes:
        frame_count: Total number of frames in the sequence.
        frame_indices: Sorted tuple of frame indices.
        frame_rate: Frame rate in frames per second.
        duration_seconds: Total duration in seconds.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
    """

    frame_count: int
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str


class SessionValidationError(Exception):
    """Error validating a RenderSession.

    Raised when session validation fails due to inconsistency or corruption.
    """

    pass


def validate_render_session(
    session: RenderSession,
) -> RenderSessionValidation:
    """Validate consistency between all components of a RenderSession.

    Verifies:
    1. Manifest ↔ Preview metadata consistency
    2. Manifest ↔ Timeline metadata consistency
    3. Preview ↔ Timeline metadata consistency
    4. Session properties match underlying components
    5. PNG files are valid and accessible via validate_render_sequence()
    6. Timeline mapping is internally consistent

    Args:
        session: The RenderSession to validate.

    Returns:
        RenderSessionValidation with validated session metadata.

    Raises:
        SessionValidationError: If validation fails.

    Example:
        >>> session = create_render_session("output_frames")
        >>> result = validate_render_session(session)
        >>> print(f"Validated: {result.frame_count} frames")
    """
    # Extract components for clarity
    manifest = session.manifest
    preview = session.preview
    timeline = session.timeline

    # 1. Verify Manifest ↔ Preview consistency
    _verify_metadata_match(
        "Manifest", "Preview",
        manifest.frame_count, preview.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Manifest", "Preview",
        manifest.frame_indices, preview.frame_indices,
        "frame_indices"
    )
    _verify_metadata_match(
        "Manifest", "Preview",
        manifest.frame_rate, preview.frame_rate,
        "frame_rate"
    )
    _verify_metadata_match(
        "Manifest", "Preview",
        manifest.duration_seconds, preview.duration_seconds,
        "duration_seconds"
    )

    # 2. Verify Manifest ↔ Timeline consistency
    _verify_metadata_match(
        "Manifest", "Timeline",
        manifest.frame_count, timeline.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Manifest", "Timeline",
        manifest.frame_indices, timeline.frame_indices,
        "frame_indices"
    )
    _verify_metadata_match(
        "Manifest", "Timeline",
        manifest.frame_rate, timeline.frame_rate,
        "frame_rate"
    )
    _verify_metadata_match(
        "Manifest", "Timeline",
        manifest.duration_seconds, timeline.duration_seconds,
        "duration_seconds"
    )

    # 3. Verify Preview ↔ Timeline consistency
    _verify_metadata_match(
        "Preview", "Timeline",
        preview.frame_count, timeline.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Preview", "Timeline",
        preview.frame_indices, timeline.frame_indices,
        "frame_indices"
    )
    _verify_metadata_match(
        "Preview", "Timeline",
        preview.frame_rate, timeline.frame_rate,
        "frame_rate"
    )
    _verify_metadata_match(
        "Preview", "Timeline",
        preview.duration_seconds, timeline.duration_seconds,
        "duration_seconds"
    )

    # 4. Verify Session properties match underlying components
    _verify_metadata_match(
        "Session", "Manifest",
        session.frame_count, manifest.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Session", "Manifest",
        session.frame_rate, manifest.frame_rate,
        "frame_rate"
    )
    _verify_metadata_match(
        "Session", "Manifest",
        session.duration_seconds, manifest.duration_seconds,
        "duration_seconds"
    )
    _verify_metadata_match(
        "Session", "Manifest",
        session.dimensions, manifest.dimensions,
        "dimensions"
    )
    _verify_metadata_match(
        "Session", "Manifest",
        session.mode, manifest.mode,
        "mode"
    )

    # 5. Verify Timeline internal consistency
    _verify_timeline_consistency(timeline)

    # 6. Delegate PNG/image validation to existing validation layer
    # We need to get the output_dir from the manifest to use validate_render_sequence
    _verify_png_sequences(manifest, preview)

    return RenderSessionValidation(
        frame_count=manifest.frame_count,
        frame_indices=manifest.frame_indices,
        frame_rate=manifest.frame_rate,
        duration_seconds=manifest.duration_seconds,
        dimensions=manifest.dimensions,
        mode=manifest.mode,
    )


def _verify_metadata_match(
    source1: str,
    source2: str,
    value1: int | float | tuple[int, ...] | str,
    value2: int | float | tuple[int, ...] | str,
    property_name: str,
) -> None:
    """Verify two metadata values match.

    Raises:
        SessionValidationError: If values don't match.
    """
    if value1 != value2:
        raise SessionValidationError(
            f"Mismatch in {property_name}: {source1}={value1}, {source2}={value2}"
        )


def _verify_timeline_consistency(
    timeline: FrameTimeline,
) -> None:
    """Verify timeline internal consistency.

    Raises:
        SessionValidationError: If timeline is inconsistent.
    """
    from tools.render.timeline import TimelineError

    # Verify first/last frame positions
    if timeline.frame_indices:
        first_index = timeline.frame_indices[0]
        last_index = timeline.frame_indices[-1]

        # Verify frame_position for first and last
        try:
            first_position = timeline.frame_position(first_index)
            if first_position != 0:
                raise SessionValidationError(
                    f"Timeline first frame position should be 0, got {first_position}"
                )
        except TimelineError as e:
            raise SessionValidationError(
                f"Timeline first frame validation failed: {e}"
            ) from e

        try:
            last_position = timeline.frame_position(last_index)
            expected_last_position = timeline.frame_count - 1
            if last_position != expected_last_position:
                raise SessionValidationError(
                    f"Timeline last frame position should be {expected_last_position}, "
                    f"got {last_position}"
                )
        except TimelineError as e:
            raise SessionValidationError(
                f"Timeline last frame validation failed: {e}"
            ) from e

        # Verify timestamp_for_frame for first and last
        try:
            first_ts = timeline.timestamp_for_frame(first_index)
            if first_ts != 0.0:
                raise SessionValidationError(
                    f"Timeline first frame timestamp should be 0.0, got {first_ts}"
                )
        except TimelineError as e:
            raise SessionValidationError(
                f"Timeline first frame timestamp validation failed: {e}"
            ) from e

        try:
            last_ts = timeline.timestamp_for_frame(last_index)
            expected_last_ts = last_position * timeline.frame_duration
            if last_ts != expected_last_ts:
                raise SessionValidationError(
                    f"Timeline last frame timestamp mismatch: expected {expected_last_ts}, "
                    f"got {last_ts}"
                )
        except TimelineError as e:
            raise SessionValidationError(
                f"Timeline last frame timestamp validation failed: {e}"
            ) from e

        # Verify timestamp mapping is internally consistent
        # (frame positions, first/last frame timestamps are already checked above)
        # The FrameTimeline validates its own structure in __post_init__


def _verify_png_sequences(
    manifest: RenderSequenceManifest,
    preview: RenderPreview,
) -> None:
    """Verify PNG sequences are valid using validate_render_sequence().

    Raises:
        SessionValidationError: If PNG validation fails.
    """
    from tools.render.validation import (
        RenderSequenceValidation,
        ValidationError,
        validate_render_sequence,
    )

    # Get output directory from manifest
    output_dir = manifest.output_dir

    # Delegate PNG validation to existing layer
    try:
        validation: RenderSequenceValidation = validate_render_sequence(
            output_dir,
            prefix=manifest.prefix,
        )
    except ValidationError as e:
        raise SessionValidationError(
            f"PNG sequence validation failed: {e}"
        ) from e

    # Verify validation results match manifest and preview
    _verify_metadata_match(
        "Validation", "Manifest",
        validation.frame_count, manifest.frame_count,
        "frame_count"
    )
    _verify_metadata_match(
        "Validation", "Manifest",
        validation.frame_indices, manifest.frame_indices,
        "frame_indices"
    )
    _verify_metadata_match(
        "Validation", "Manifest",
        validation.dimensions, manifest.dimensions,
        "dimensions"
    )
    _verify_metadata_match(
        "Validation", "Manifest",
        validation.mode, manifest.mode,
        "mode"
    )


__all__ = [
    "RenderSessionValidation",
    "SessionValidationError",
    "validate_render_session",
]
