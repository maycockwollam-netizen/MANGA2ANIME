"""Camera keyframe interpolation.

V1 interpolation between CameraKeyframe instances. Given two keyframes and
a normalized progress value t in [0, 1], this module computes an interpolated
CameraKeyframe-like state and converts it into a FrameTransform suitable for
the ConcreteRenderer.

This module does NOT:
- Implement GPU-accelerated interpolation
- Access runtime.animation internals
- Implement spline/catmull-rom interpolation (V2 scope)
"""

from __future__ import annotations

import math

from tools.animation.exceptions import AnimationEvalError
from tools.animation.models import CameraKeyframe, EasingType
from tools.frame.models import FrameTransform


def linear_easing(t: float) -> float:
    """Linear easing: returns t unchanged.

    Args:
        t: Normalized progress in [0, 1].

    Returns:
        The same progress value (constant speed).

    Raises:
        AnimationEvalError: If t is outside [0, 1].
    """
    if not (0.0 <= t <= 1.0):
        raise AnimationEvalError(f"progress must be in [0, 1], got {t}")
    return t


def ease_in_out_easing(t: float) -> float:
    """Smooth ease-in-out using a cosine curve.

    Implements the standard smoothstep-like mapping:
        f(t) = 0.5 * (1 - cos(pi * t))

    This produces slow acceleration near t=0 and slow deceleration near t=1.

    Args:
        t: Normalized progress in [0, 1].

    Returns:
        Eased progress in [0, 1].

    Raises:
        AnimationEvalError: If t is outside [0, 1].
    """
    if not (0.0 <= t <= 1.0):
        raise AnimationEvalError(f"progress must be in [0, 1], got {t}")
    return 0.5 * (1.0 - math.cos(math.pi * t))


_EASING_FUNCTIONS = {
    EasingType.LINEAR: linear_easing,
    EasingType.EASE_IN_OUT: ease_in_out_easing,
}


def get_easing(easing: EasingType):
    """Return the easing callable for a given EasingType.

    Args:
        easing: The desired easing type.

    Returns:
        A callable ``(t: float) -> float``.

    Raises:
        AnimationEvalError: If the easing type is not supported.
    """
    func = _EASING_FUNCTIONS.get(easing)
    if func is None:
        raise AnimationEvalError(f"unsupported easing type: {easing!r}")
    return func


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two scalars.

    Args:
        a: Start value.
        b: End value.
        t: Normalized progress in [0, 1].

    Returns:
        Interpolated value.
    """
    return a + (b - a) * t


def interpolate_keyframes(
    kf_a: CameraKeyframe,
    kf_b: CameraKeyframe,
    t: float,
    easing: EasingType = EasingType.LINEAR,
) -> CameraKeyframe:
    """Interpolate between two camera keyframes at normalized progress t.

    Args:
        kf_a: Start keyframe.
        kf_b: End keyframe.
        t: Normalized progress in [0, 1] between the two keyframes.
        easing: Easing function to apply before interpolation.

    Returns:
        A new CameraKeyframe at the interpolated state. Its timestamp is set
        to the absolute time corresponding to t between the two keyframes.

    Raises:
        AnimationEvalError: If t is outside [0, 1] or the easing is invalid.
    """
    eased = get_easing(easing)(t)
    timestamp = _lerp(kf_a.timestamp, kf_b.timestamp, t)
    zoom = _lerp(kf_a.zoom, kf_b.zoom, eased)
    focus_x = _lerp(kf_a.focus_x, kf_b.focus_x, eased)
    focus_y = _lerp(kf_a.focus_y, kf_b.focus_y, eased)
    return CameraKeyframe(
        timestamp=timestamp,
        zoom=zoom,
        focus_x=focus_x,
        focus_y=focus_y,
    )


def to_frame_transform(
    keyframe: CameraKeyframe,
    source_path=None,
) -> FrameTransform:
    """Convert a CameraKeyframe into a FrameTransform for the renderer.

    The mapping is:
        - zoom      -> scale       (1.0 zoom = 1.0 scale)
        - focus_x   -> anchor_x    (focus point becomes the transform anchor)
        - focus_y   -> anchor_y
        - position_x/y, rotation, opacity -> defaults (no pan/rotate/fade)

    Args:
        keyframe: The camera keyframe to convert.
        source_path: Optional path to the image asset to attach to the
            resulting FrameTransform. If None, source_path is left unset.

    Returns:
        A FrameTransform ready to be passed to a renderer.
    """
    return FrameTransform(
        scale=keyframe.zoom,
        anchor_x=keyframe.focus_x,
        anchor_y=keyframe.focus_y,
        position_x=0.0,
        position_y=0.0,
        rotation_deg=0.0,
        opacity=1.0,
        source_path=source_path,
    )
