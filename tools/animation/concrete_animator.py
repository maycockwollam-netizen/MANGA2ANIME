"""Concrete camera animator implementation.

V1 keyframe-based camera animator. Evaluates an AnimationConfig at a given
time by locating the surrounding keyframes, computing the normalized
progress, applying the configured easing, and converting the interpolated
state into a FrameTransform.

This module does NOT:
- Implement spline/catmull-rom interpolation (V2 scope)
- Access GPU
- Access runtime.animation internals
- Implement caching or batching
"""

from __future__ import annotations

from tools.animation.exceptions import AnimationConfigError, AnimationEvalError
from tools.animation.interpolation import interpolate_keyframes, to_frame_transform
from tools.animation.models import AnimationConfig
from tools.frame.models import FrameTransform


class KeyframeAnimator:
    """Camera animator that interpolates between keyframes.

    V1 uses linear or ease-in-out interpolation between consecutive
    CameraKeyframes on a non-decreasing timeline.

    Example:
        >>> from tools.animation import AnimationConfig, CameraKeyframe, KeyframeAnimator
        >>> config = AnimationConfig(keyframes=[
        ...     CameraKeyframe(timestamp=0.0, zoom=1.0),
        ...     CameraKeyframe(timestamp=1.0, zoom=2.0),
        ... ])
        >>> animator = KeyframeAnimator()
        >>> transform = animator.evaluate(config, 0.5)
        >>> round(transform.scale, 2)
        1.5
    """

    def evaluate(self, config: AnimationConfig, time: float) -> FrameTransform:
        """Evaluate the animation at a specific time.

        Args:
            config: The animation configuration describing keyframes.
            time: Time in seconds at which to evaluate.

        Returns:
            A FrameTransform representing the camera state at the given time.

        Raises:
            AnimationConfigError: If the configuration has no keyframes.
            AnimationEvalError: If time is negative or before the first
                keyframe / after the last with no extrapolation.
        """
        keyframes = config.keyframes
        if not keyframes:
            raise AnimationConfigError("animation config has no keyframes")

        if time < 0:
            raise AnimationEvalError(f"time must be >= 0, got {time}")

        first_ts = keyframes[0].timestamp
        last_ts = keyframes[-1].timestamp

        # Clamp to the first keyframe if before/at the start.
        if time <= first_ts:
            return to_frame_transform(keyframes[0])

        # Clamp to the last keyframe if at/after the end.
        if time >= last_ts:
            return to_frame_transform(keyframes[-1])

        # Locate the surrounding keyframe pair.
        kf_a, kf_b = self._find_segment(keyframes, time)

        # Compute normalized progress within the segment.
        span = kf_b.timestamp - kf_a.timestamp
        if span <= 0:
            # Degenerate (shouldn't happen — duplicates rejected by config).
            t = 0.0
        else:
            t = (time - kf_a.timestamp) / span

        interpolated = interpolate_keyframes(kf_a, kf_b, t, config.easing)
        return to_frame_transform(interpolated)

    @staticmethod
    def _find_segment(
        keyframes, time: float
    ):
        """Find the two keyframes bracketing the given time.

        Args:
            keyframes: Ordered list of CameraKeyframe.
            time: Time in seconds.

        Returns:
            Tuple of (start_keyframe, end_keyframe) bracketing time.

        Raises:
            AnimationEvalError: If no bracketing segment is found.
        """
        for i in range(len(keyframes) - 1):
            if keyframes[i].timestamp <= time < keyframes[i + 1].timestamp:
                return keyframes[i], keyframes[i + 1]
        raise AnimationEvalError(f"no keyframe segment found for time {time}")
