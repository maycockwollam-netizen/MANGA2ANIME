"""Render sequence validation.

Provides validation for exported PNG sequences from the render pipeline.

This module validates sequences independently of the rendering implementation
and does not couple to runtime/animation systems.

Architecture:
    Exported PNG sequence
        ↓
    validate_render_sequence()
        ↓
    RenderSequenceValidation (or exception)

This module does NOT:
- Perform rendering
- Modify files
- Access runtime/animation
- Implement video encoding
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class RenderSequenceValidation:
    """Immutable validation result for a rendered PNG sequence.

    Attributes:
        frame_count: Total number of valid PNG frames found.
        frame_indices: Sorted tuple of frame indices present in the sequence.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
    """

    frame_count: int
    frame_indices: tuple[int, ...]
    dimensions: tuple[int, int]
    mode: str


class ValidationError(Exception):
    """Error validating a render sequence.

    Raised when sequence validation fails (missing frames, inconsistent metadata, etc.).
    """

    pass


def validate_render_sequence(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    expected_frame_count: int | None = None,
) -> RenderSequenceValidation:
    """Validate an exported PNG sequence.

    Checks that a sequence of PNG files exists at the expected output directory
    with correct naming, complete frame indices, and consistent image properties.

    Args:
        output_dir: Directory containing the PNG sequence.
        prefix: Filename prefix used for PNG files (default: "frame").
        expected_frame_count: Optional expected number of frames. If provided,
            validation fails if the count doesn't match.

    Returns:
        RenderSequenceValidation with sequence metadata.

    Raises:
        ValidationError: If the sequence is invalid (empty, missing frames,
            duplicates, inconsistent properties, etc.).

    Example:
        >>> result = validate_render_sequence("output_frames")
        >>> print(f"Found {result.frame_count} frames")
    """
    output_dir = Path(output_dir)

    # Find all PNG files matching the pattern {prefix}_*.png
    pattern = f"{prefix}_*.png"
    png_files = sorted(output_dir.glob(pattern))

    # Check for empty sequence
    if not png_files:
        raise ValidationError(
            f"Empty sequence: no PNG files matching '{pattern}' found in {output_dir}"
        )

    # Parse frame indices and detect issues
    seen_indices: set[int] = set()
    duplicate_indices: set[int] = set()
    frame_indices: list[int] = []
    unexpected_files: list[Path] = []

    for png_path in png_files:
        # Extract frame index from filename
        # Expected format: {prefix}_{frame_index:06d}.png
        filename = png_path.name
        try:
            # Parse the index part: prefix_000000.png -> 000000 -> 0
            index_str = filename[len(prefix) + 1 : -4]  # Remove prefix_ and .png
            frame_index = int(index_str)
        except (ValueError, IndexError):
            unexpected_files.append(png_path)
            continue

        # Check for duplicates using a set
        if frame_index in seen_indices:
            duplicate_indices.add(frame_index)
        else:
            seen_indices.add(frame_index)
            frame_indices.append(frame_index)

    # Report duplicates
    if duplicate_indices:
        raise ValidationError(
            f"Duplicate frame indices found: {sorted(duplicate_indices)}"
        )

    # Report unexpected files
    if unexpected_files:
        names = [f.name for f in unexpected_files]
        raise ValidationError(
            f"Unexpected PNG files not matching naming convention: {names}"
        )

    # Verify expected frame count
    if expected_frame_count is not None:
        actual_count = len(frame_indices)
        if actual_count != expected_frame_count:
            raise ValidationError(
                f"Frame count mismatch: expected {expected_frame_count}, found {actual_count}"
            )

    # Check for missing frame indices
    if frame_indices:
        expected_range = set(range(min(frame_indices), max(frame_indices) + 1))
        actual_set = set(frame_indices)
        missing = expected_range - actual_set
        if missing:
            raise ValidationError(
                f"Missing frame indices: {sorted(missing)}"
            )

    # Validate image properties (all frames must be readable and consistent)
    dimensions: tuple[int, int] | None = None
    mode: str | None = None

    for png_path in png_files:
        try:
            with Image.open(png_path) as img:
                img.verify()
        except Exception as e:
            raise ValidationError(
                f"Unreadable PNG file: {png_path.name} ({e})"
            ) from e

    # Re-open to get dimensions and mode (verify() requires closing)
    for png_path in png_files:
        with Image.open(png_path) as img:
            img_dimensions = (img.width, img.height)
            img_mode = img.mode

            if dimensions is None:
                dimensions = img_dimensions
            elif img_dimensions != dimensions:
                raise ValidationError(
                    f"Inconsistent dimensions: {png_path.name} has {img_dimensions}, "
                    f"expected {dimensions}"
                )

            if mode is None:
                mode = img_mode
            elif img_mode != mode:
                raise ValidationError(
                    f"Inconsistent image mode: {png_path.name} has {img_mode}, "
                    f"expected {mode}"
                )

    # This should never happen since we already checked for empty sequence
    if dimensions is None or mode is None:
        raise ValidationError("Internal error: could not determine image properties")

    return RenderSequenceValidation(
        frame_count=len(frame_indices),
        frame_indices=tuple(sorted(frame_indices)),
        dimensions=dimensions,
        mode=mode,
    )


__all__ = [
    "RenderSequenceValidation",
    "ValidationError",
    "validate_render_sequence",
]
