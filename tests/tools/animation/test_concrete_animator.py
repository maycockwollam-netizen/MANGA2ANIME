"""Tests for concrete KeyframeAnimator."""

import pytest

from tools.animation import (
    AnimationConfig,
    AnimationConfigError,
    AnimationEvalError,
    CameraKeyframe,
    EasingType,
    KeyframeAnimator,
)
from tools.frame.models import FrameTransform


def _two_kf_config(zoom_a=1.0, zoom_b=2.0, easing=EasingType.LINEAR):
    return AnimationConfig(
        keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=zoom_a, focus_x=0.5, focus_y=0.5),
            CameraKeyframe(timestamp=1.0, zoom=zoom_b, focus_x=0.3, focus_y=0.7),
        ],
        easing=easing,
    )


class TestKeyframeAnimatorBasics:
    """Tests for KeyframeAnimator basic functionality."""

    def test_returns_frame_transform(self) -> None:
        """Test that evaluate returns a FrameTransform."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), 0.5)
        assert isinstance(result, FrameTransform)

    def test_at_start_keyframe(self) -> None:
        """Test evaluation at the first keyframe's timestamp."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), 0.0)
        assert result.scale == 1.0
        assert result.anchor_x == 0.5
        assert result.anchor_y == 0.5

    def test_at_end_keyframe(self) -> None:
        """Test evaluation at the last keyframe's timestamp."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), 1.0)
        assert result.scale == 2.0
        assert result.anchor_x == 0.3
        assert result.anchor_y == 0.7

    def test_linear_midpoint(self) -> None:
        """Test linear interpolation at the midpoint."""
        result = KeyframeAnimator().evaluate(_two_kf_config(1.0, 3.0), 0.5)
        assert result.scale == 2.0
        assert result.anchor_x == 0.4
        assert result.anchor_y == 0.6


class TestKeyframeAnimatorClamping:
    """Tests for boundary clamping behavior."""

    def test_before_start_clamps_to_first(self) -> None:
        """Test that a time before the first keyframe clamps to it."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), -0.0)
        assert result.scale == 1.0
        # A negative time is rejected separately (see test_negative_time).

    def test_after_end_clamps_to_last(self) -> None:
        """Test that a time after the last keyframe clamps to it."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), 2.0)
        assert result.scale == 2.0

    def test_negative_time_rejected(self) -> None:
        """Test that a strictly negative time raises AnimationEvalError."""
        with pytest.raises(AnimationEvalError):
            KeyframeAnimator().evaluate(_two_kf_config(), -0.1)


class TestKeyframeAnimatorEasing:
    """Tests for easing selection."""

    def test_ease_in_out_midpoint(self) -> None:
        """Test ease-in-out produces the same midpoint as linear (symmetric)."""
        config = _two_kf_config(1.0, 3.0, EasingType.EASE_IN_OUT)
        result = KeyframeAnimator().evaluate(config, 0.5)
        assert abs(result.scale - 2.0) < 1e-9

    def test_ease_in_out_quarter_below_linear(self) -> None:
        """Test ease-in-out at t=0.25 is below the linear value (slow start)."""
        linear = KeyframeAnimator().evaluate(_two_kf_config(1.0, 3.0), 0.25)
        eased = KeyframeAnimator().evaluate(
            _two_kf_config(1.0, 3.0, EasingType.EASE_IN_OUT), 0.25
        )
        assert eased.scale < linear.scale


class TestKeyframeAnimatorMultipleKeyframes:
    """Tests for animations with more than two keyframes."""

    def test_three_keyframe_segment_selection(self) -> None:
        """Test that the correct segment is selected across three keyframes."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.0),
            CameraKeyframe(timestamp=1.0, zoom=2.0),
            CameraKeyframe(timestamp=2.0, zoom=4.0),
        ])
        animator = KeyframeAnimator()
        # In the second segment (1.0 -> 2.0), at t=1.5 midpoint -> 3.0.
        result = animator.evaluate(config, 1.5)
        assert result.scale == 3.0

    def test_three_keyframe_boundary(self) -> None:
        """Test evaluation exactly at a middle keyframe boundary."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.0),
            CameraKeyframe(timestamp=1.0, zoom=2.0),
            CameraKeyframe(timestamp=2.0, zoom=4.0),
        ])
        animator = KeyframeAnimator()
        # Exactly at 1.0 -> should return the middle keyframe value.
        result = animator.evaluate(config, 1.0)
        assert result.scale == 2.0


class TestKeyframeAnimatorSingleKeyframe:
    """Tests for animations with a single keyframe."""

    def test_single_keyframe_constant(self) -> None:
        """Test that a single keyframe produces a constant transform."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.5, focus_x=0.2, focus_y=0.8),
        ])
        animator = KeyframeAnimator()
        result = animator.evaluate(config, 0.0)
        assert result.scale == 1.5
        assert result.anchor_x == 0.2
        assert result.anchor_y == 0.8

    def test_single_keyframe_any_time(self) -> None:
        """Test that a single keyframe clamps for any time."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=5.0, zoom=1.5),
        ])
        animator = KeyframeAnimator()
        # time 0.0 < 5.0 -> clamps to first keyframe.
        result = animator.evaluate(config, 0.0)
        assert result.scale == 1.5
        # time 10.0 > 5.0 -> clamps to last (same) keyframe.
        result_late = animator.evaluate(config, 10.0)
        assert result_late.scale == 1.5


class TestKeyframeAnimatorErrors:
    """Tests for error handling in KeyframeAnimator."""

    def test_empty_keyframes_raises_config_error(self) -> None:
        """Test that evaluate raises AnimationConfigError on empty keyframes.

        AnimationConfig rejects empty keyframes at construction, so bypass
        validation via __dict__ to exercise the defensive path in evaluate.
        """
        animator = KeyframeAnimator()
        config = AnimationConfig(keyframes=[CameraKeyframe(timestamp=0.0)])
        object.__setattr__(config, "keyframes", [])
        with pytest.raises(AnimationConfigError):
            animator.evaluate(config, 0.0)

    def test_default_opacity_and_rotation(self) -> None:
        """Test that opacity is 1.0 and rotation is 0.0 by default."""
        result = KeyframeAnimator().evaluate(_two_kf_config(), 0.5)
        assert result.opacity == 1.0
        assert result.rotation_deg == 0.0


class TestKeyframeAnimatorDeterminism:
    """Tests for deterministic evaluation."""

    def test_repeated_evaluation_identical(self) -> None:
        """Test that repeated evaluation produces identical results."""
        config = _two_kf_config(1.0, 3.0)
        animator = KeyframeAnimator()
        r1 = animator.evaluate(config, 0.37)
        r2 = animator.evaluate(config, 0.37)
        assert r1.model_dump() == r2.model_dump()
