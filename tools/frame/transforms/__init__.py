"""Frame transforms module V1.

Pure, deterministic transformation logic for frame/layer transforms.
Converts FrameTransform data into transformation results for consumption
by future animation/rendering layers.

This module does NOT:
- Perform image manipulation
- Execute rendering
- Access GPU
- Perform I/O operations
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.frame.models import FrameTransform


@dataclass(frozen=True, slots=True)
class TransformResult:
    """Result of applying a transformation.

    Immutable result containing computed transformation parameters.

    Attributes:
        position_x: Final X position
        position_y: Final Y position
        scale: Final scale factor
        rotation_deg: Final rotation in degrees
        opacity: Final opacity (0-1)
        anchor_x: Anchor X point used
        anchor_y: Anchor Y point used
    """

    position_x: float
    position_y: float
    scale: float
    rotation_deg: float
    opacity: float
    anchor_x: float
    anchor_y: float

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "position_x": self.position_x,
            "position_y": self.position_y,
            "scale": self.scale,
            "rotation_deg": self.rotation_deg,
            "opacity": self.opacity,
            "anchor_x": self.anchor_x,
            "anchor_y": self.anchor_y,
        }


def _get_value(current: float | None, default: float) -> float:
    """Get value or default."""
    return current if current is not None else default


def apply_transform(
    transform: FrameTransform,
    *,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> TransformResult:
    """Apply a FrameTransform to calculate the final transformation.

    Performs mathematical transformation calculation based on the provided
    FrameTransform parameters. The transformation is applied around the
    anchor point, which is relative to the origin.

    Composition order:
        1. Translate to anchor
        2. Apply scale
        3. Apply rotation
        4. Apply opacity
        5. Translate to final position

    Args:
        transform: FrameTransform data contract
        origin_x: Origin X coordinate (default: 0.0)
        origin_y: Origin Y coordinate (default: 0.0)

    Returns:
        TransformResult with computed transformation parameters

    Example:
        >>> transform = FrameTransform(position_x=100, scale=2.0)
        >>> result = apply_transform(transform)
        >>> result.position_x
        100.0
        >>> result.scale
        2.0
    """
    # Extract transform parameters with defaults
    pos_x = _get_value(transform.position_x, 0.0)
    pos_y = _get_value(transform.position_y, 0.0)
    scale = _get_value(transform.scale, 1.0)
    rotation = _get_value(transform.rotation_deg, 0.0)
    opacity = _get_value(transform.opacity, 1.0)
    anchor_x = _get_value(transform.anchor_x, 0.5)
    anchor_y = _get_value(transform.anchor_y, 0.5)

    # Calculate final position relative to origin and anchor
    # Translate origin to anchor, apply transforms, translate back
    final_x = origin_x + pos_x
    final_y = origin_y + pos_y

    return TransformResult(
        position_x=final_x,
        position_y=final_y,
        scale=scale,
        rotation_deg=rotation,
        opacity=opacity,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )


def compose_transforms(
    transforms: list[FrameTransform],
    *,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> TransformResult:
    """Compose multiple transforms into a single result.

    Transforms are applied in order from first to last in the list.
    Each subsequent transform builds upon the result of previous transforms.

    Composition order:
        For each transform T_i in order:
            1. Apply T_i's scale to cumulative scale
            2. Add T_i's rotation to cumulative rotation
            3. Add T_i's position to cumulative position
            4. Use T_i's opacity (last wins) and anchor (last wins)

    Args:
        transforms: List of FrameTransform to compose (applied in order)
        origin_x: Origin X coordinate (default: 0.0)
        origin_y: Origin Y coordinate (default: 0.0)

    Returns:
        TransformResult with composed transformation parameters

    Example:
        >>> t1 = FrameTransform(position_x=50)
        >>> t2 = FrameTransform(position_x=50, scale=2.0)
        >>> result = compose_transforms([t1, t2])
        >>> result.position_x
        100.0
        >>> result.scale
        2.0
    """
    if not transforms:
        # Identity transform
        return TransformResult(
            position_x=origin_x,
            position_y=origin_y,
            scale=1.0,
            rotation_deg=0.0,
            opacity=1.0,
            anchor_x=0.5,
            anchor_y=0.5,
        )

    cumulative_x = origin_x
    cumulative_y = origin_y
    cumulative_scale = 1.0
    cumulative_rotation = 0.0
    final_opacity = 1.0
    final_anchor_x = 0.5
    final_anchor_y = 0.5

    for transform in transforms:
        # Accumulate position
        pos_x = _get_value(transform.position_x, 0.0)
        pos_y = _get_value(transform.position_y, 0.0)
        cumulative_x += pos_x
        cumulative_y += pos_y

        # Accumulate scale (multiply)
        scale = _get_value(transform.scale, 1.0)
        cumulative_scale *= scale

        # Accumulate rotation (add)
        rotation = _get_value(transform.rotation_deg, 0.0)
        cumulative_rotation += rotation

        # Last opacity and anchor win
        final_opacity = _get_value(transform.opacity, 1.0)
        final_anchor_x = _get_value(transform.anchor_x, 0.5)
        final_anchor_y = _get_value(transform.anchor_y, 0.5)

    return TransformResult(
        position_x=cumulative_x,
        position_y=cumulative_y,
        scale=cumulative_scale,
        rotation_deg=cumulative_rotation,
        opacity=final_opacity,
        anchor_x=final_anchor_x,
        anchor_y=final_anchor_y,
    )


def interpolate_transform(
    start: FrameTransform,
    end: FrameTransform,
    t: float,
) -> FrameTransform:
    """Interpolate between two transforms.

    Performs linear interpolation between start and end transforms.
    The parameter t should be in range [0.0, 1.0]:
        t=0.0 returns start transform
        t=1.0 returns end transform
        0<t<1 returns interpolated transform

    Interpolation semantics:
        - position_x/y: linear interpolation
        - scale: linear interpolation
        - rotation_deg: direct numeric linear interpolation
        - opacity: linear interpolation
        - anchor_x/y: linear interpolation

    Note: Rotation uses direct numeric interpolation, not shortest-angle.
          For example, interpolating 350° to 10° gives 180° at t=0.5.

    Args:
        start: Starting FrameTransform
        end: Ending FrameTransform
        t: Interpolation parameter (0.0 to 1.0)

    Returns:
        Interpolated FrameTransform

    Raises:
        ValueError: If t is outside [0.0, 1.0] range

    Example:
        >>> t1 = FrameTransform(position_x=0, scale=1.0)
        >>> t2 = FrameTransform(position_x=100, scale=2.0)
        >>> result = interpolate_transform(t1, t2, 0.5)
        >>> result.position_x
        50.0
        >>> result.scale
        1.5
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"t must be in range [0.0, 1.0], got {t}")

    # Handle edge cases
    if t == 0.0:
        return start.model_copy()
    if t == 1.0:
        return end.model_copy()

    # Linear interpolation helper
    def lerp(a: float | None, b: float | None, t: float, default: float) -> float | None:
        if a is None and b is None:
            return None
        a_val = a if a is not None else default
        b_val = b if b is not None else default
        return a_val + (b_val - a_val) * t

    return FrameTransform(
        position_x=lerp(start.position_x, end.position_x, t, 0.0),
        position_y=lerp(start.position_y, end.position_y, t, 0.0),
        scale=lerp(start.scale, end.scale, t, 1.0),
        rotation_deg=lerp(start.rotation_deg, end.rotation_deg, t, 0.0),
        opacity=lerp(start.opacity, end.opacity, t, 1.0),
        anchor_x=lerp(start.anchor_x, end.anchor_x, t, 0.5),
        anchor_y=lerp(start.anchor_y, end.anchor_y, t, 0.5),
    )


def lerp_float(a: float, b: float, t: float) -> float:
    """Linear interpolation between two floats.

    Args:
        a: Start value
        b: End value
        t: Interpolation parameter (0.0 to 1.0)

    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def identity_transform() -> FrameTransform:
    """Create an identity transform (no transformation).

    Returns:
        FrameTransform with default values (identity)
    """
    return FrameTransform()


__all__ = [
    "TransformResult",
    "apply_transform",
    "compose_transforms",
    "interpolate_transform",
    "lerp_float",
    "identity_transform",
]
