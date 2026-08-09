"""Tests for interpolation easing functions."""


import pytest

from tools.animation import (
    AnimationEvalError,
    EasingType,
    ease_in_out_easing,
    get_easing,
    interpolate_keyframes,
    linear_easing,
    to_frame_transform,
)
from tools.animation.models import CameraKeyframe
from tools.frame.models import FrameTransform


class TestLinearEasing:
    """Tests for linear_easing."""

    def test_identity_at_endpoints(self) -> None:
        """Test that linear easing is the identity at endpoints."""
        assert linear_easing(0.0) == 0.0
        assert linear_easing(1.0) == 1.0

    def test_linear_midpoint(self) -> None:
        """Test that linear easing is linear at the midpoint."""
        assert linear_easing(0.5) == 0.5

    def test_out_of_range_rejected(self) -> None:
        """Test that progress outside [0, 1] is rejected."""
        with pytest.raises(AnimationEvalError):
            linear_easing(-0.1)
        with pytest.raises(AnimationEvalError):
            linear_easing(1.1)


class TestEaseInOutEasing:
    """Tests for ease_in_out_easing."""

    def test_endpoints(self) -> None:
        """Test ease-in-out returns 0 and 1 at the endpoints."""
        assert abs(ease_in_out_easing(0.0) - 0.0) < 1e-9
        assert abs(ease_in_out_easing(1.0) - 1.0) < 1e-9

    def test_midpoint_is_half(self) -> None:
        """Test that the cosine ease passes through 0.5 at the midpoint."""
        assert abs(ease_in_out_easing(0.5) - 0.5) < 1e-9

    def test_smooth_curve_below_linear_first_half(self) -> None:
        """Test ease-in-out is below linear in the first half (slow start)."""
        assert ease_in_out_easing(0.25) < 0.25

    def test_smooth_curve_above_linear_second_half(self) -> None:
        """Test ease-in-out is above linear in the second half."""
        assert ease_in_out_easing(0.75) > 0.75

    def test_symmetry(self) -> None:
        """Test that f(t) + f(1-t) == 1 (symmetric curve)."""
        for t in (0.1, 0.25, 0.4, 0.6, 0.75, 0.9):
            assert abs(ease_in_out_easing(t) + ease_in_out_easing(1 - t) - 1.0) < 1e-9

    def test_out_of_range_rejected(self) -> None:
        """Test that progress outside [0, 1] is rejected."""
        with pytest.raises(AnimationEvalError):
            ease_in_out_easing(-0.01)
        with pytest.raises(AnimationEvalError):
            ease_in_out_easing(1.01)


class TestGetEasing:
    """Tests for get_easing dispatcher."""

    def test_linear_dispatch(self) -> None:
        """Test that LINEAR dispatches to linear_easing."""
        assert get_easing(EasingType.LINEAR) is linear_easing

    def test_ease_in_out_dispatch(self) -> None:
        """Test that EASE_IN_OUT dispatches to ease_in_out_easing."""
        assert get_easing(EasingType.EASE_IN_OUT) is ease_in_out_easing


class TestInterpolateKeyframes:
    """Tests for interpolate_keyframes."""

    def test_at_start_returns_start_values(self) -> None:
        """Test that t=0 yields the start keyframe's values."""
        a = CameraKeyframe(timestamp=0.0, zoom=1.0, focus_x=0.5, focus_y=0.5)
        b = CameraKeyframe(timestamp=1.0, zoom=2.0, focus_x=0.3, focus_y=0.7)
        result = interpolate_keyframes(a, b, 0.0)
        assert result.zoom == 1.0
        assert result.focus_x == 0.5

    def test_at_end_returns_end_values(self) -> None:
        """Test that t=1 yields the end keyframe's values."""
        a = CameraKeyframe(timestamp=0.0, zoom=1.0)
        b = CameraKeyframe(timestamp=1.0, zoom=2.0, focus_x=0.3, focus_y=0.7)
        result = interpolate_keyframes(a, b, 1.0)
        assert result.zoom == 2.0
        assert result.focus_x == 0.3
        assert result.focus_y == 0.7

    def test_linear_midpoint(self) -> None:
        """Test linear interpolation at the midpoint."""
        a = CameraKeyframe(timestamp=0.0, zoom=1.0)
        b = CameraKeyframe(timestamp=1.0, zoom=3.0)
        result = interpolate_keyframes(a, b, 0.5, EasingType.LINEAR)
        assert result.zoom == 2.0

    def test_eased_midpoint(self) -> None:
        """Test ease-in-out interpolation at the midpoint."""
        a = CameraKeyframe(timestamp=0.0, zoom=1.0)
        b = CameraKeyframe(timestamp=1.0, zoom=3.0)
        result = interpolate_keyframes(a, b, 0.5, EasingType.EASE_IN_OUT)
        assert abs(result.zoom - 2.0) < 1e-9

    def test_timestamp_is_absolute(self) -> None:
        """Test that the result timestamp is the absolute interpolated time."""
        a = CameraKeyframe(timestamp=2.0, zoom=1.0)
        b = CameraKeyframe(timestamp=4.0, zoom=2.0)
        result = interpolate_keyframes(a, b, 0.5)
        assert result.timestamp == 3.0

    def test_out_of_range_rejected(self) -> None:
        """Test that progress outside [0, 1] is rejected."""
        a = CameraKeyframe(timestamp=0.0, zoom=1.0)
        b = CameraKeyframe(timestamp=1.0, zoom=2.0)
        with pytest.raises(AnimationEvalError):
            interpolate_keyframes(a, b, -0.1)
        with pytest.raises(AnimationEvalError):
            interpolate_keyframes(a, b, 1.1)


class TestToFrameTransform:
    """Tests for to_frame_transform conversion."""

    def test_zoom_maps_to_scale(self) -> None:
        """Test that zoom maps to FrameTransform.scale."""
        kf = CameraKeyframe(timestamp=0.0, zoom=2.5)
        ft = to_frame_transform(kf)
        assert ft.scale == 2.5

    def test_focus_maps_to_anchor(self) -> None:
        """Test that focus_x/y map to anchor_x/y."""
        kf = CameraKeyframe(timestamp=0.0, focus_x=0.3, focus_y=0.7)
        ft = to_frame_transform(kf)
        assert ft.anchor_x == 0.3
        assert ft.anchor_y == 0.7

    def test_defaults_set(self) -> None:
        """Test that position/rotation/opacity use neutral defaults."""
        kf = CameraKeyframe(timestamp=0.0, zoom=1.0)
        ft = to_frame_transform(kf)
        assert ft.position_x == 0.0
        assert ft.position_y == 0.0
        assert ft.rotation_deg == 0.0
        assert ft.opacity == 1.0
        assert ft.source_path is None

    def test_source_path_attached(self, tmp_path) -> None:
        """Test that a source_path is attached when provided."""
        kf = CameraKeyframe(timestamp=0.0, zoom=1.0)
        path = tmp_path / "img.png"
        ft = to_frame_transform(kf, source_path=path)
        assert ft.source_path == path

    def test_returns_frame_transform_instance(self) -> None:
        """Test that the result is a FrameTransform instance."""
        kf = CameraKeyframe(timestamp=0.0, zoom=1.0)
        ft = to_frame_transform(kf)
        assert isinstance(ft, FrameTransform)
