"""Tests for animation data models."""

import math

import pytest
from pydantic import ValidationError

from tools.animation import (
    AnimationConfig,
    CameraKeyframe,
    EasingType,
)


class TestCameraKeyframe:
    """Tests for CameraKeyframe model."""

    def test_defaults(self) -> None:
        """Test CameraKeyframe default values."""
        kf = CameraKeyframe(timestamp=1.0)
        assert kf.zoom == 1.0
        assert kf.focus_x == 0.5
        assert kf.focus_y == 0.5

    def test_is_frozen(self) -> None:
        """Test that CameraKeyframe is immutable."""
        kf = CameraKeyframe(timestamp=1.0)
        with pytest.raises(ValidationError):
            kf.zoom = 2.0  # type: ignore[misc]

    def test_negative_timestamp_rejected(self) -> None:
        """Test that a negative timestamp is rejected."""
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=-0.1)

    def test_negative_zoom_rejected(self) -> None:
        """Test that a negative zoom is rejected."""
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=0.0, zoom=-0.5)

    def test_zero_zoom_allowed(self) -> None:
        """Test that a zero zoom is allowed."""
        kf = CameraKeyframe(timestamp=0.0, zoom=0.0)
        assert kf.zoom == 0.0

    def test_focus_out_of_range_rejected(self) -> None:
        """Test that focus values outside [0, 1] are rejected."""
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=0.0, focus_x=-0.1)
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=0.0, focus_y=1.1)

    def test_nan_zoom_rejected(self) -> None:
        """Test that NaN zoom is rejected."""
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=0.0, zoom=math.nan)

    def test_inf_zoom_rejected(self) -> None:
        """Test that infinite zoom is rejected."""
        with pytest.raises(ValidationError):
            CameraKeyframe(timestamp=0.0, zoom=math.inf)


class TestEasingType:
    """Tests for EasingType enum."""

    def test_linear_value(self) -> None:
        """Test LINEAR member value."""
        assert EasingType.LINEAR == "linear"

    def test_ease_in_out_value(self) -> None:
        """Test EASE_IN_OUT member value."""
        assert EasingType.EASE_IN_OUT == "ease_in_out"

    def test_is_string_enum(self) -> None:
        """Test that EasingType behaves as a string."""
        assert EasingType.LINEAR == "linear"
        assert isinstance(EasingType.LINEAR.value, str)


class TestAnimationConfig:
    """Tests for AnimationConfig model."""

    def test_defaults(self) -> None:
        """Test AnimationConfig default easing."""
        kf = CameraKeyframe(timestamp=0.0)
        config = AnimationConfig(keyframes=[kf])
        assert config.easing == EasingType.LINEAR
        assert config.duration_seconds is None

    def test_requires_at_least_one_keyframe(self) -> None:
        """Test that an empty keyframe list is rejected."""
        with pytest.raises(ValidationError, match="at least one keyframe"):
            AnimationConfig(keyframes=[])

    def test_is_frozen(self) -> None:
        """Test that AnimationConfig is immutable."""
        kf = CameraKeyframe(timestamp=0.0)
        config = AnimationConfig(keyframes=[kf])
        with pytest.raises(ValidationError):
            config.easing = EasingType.EASE_IN_OUT  # type: ignore[misc]

    def test_decreasing_timestamps_rejected(self) -> None:
        """Test that out-of-order timestamps are rejected."""
        with pytest.raises(ValidationError, match="non-decreasing"):
            AnimationConfig(keyframes=[
                CameraKeyframe(timestamp=1.0),
                CameraKeyframe(timestamp=0.0),
            ])

    def test_duplicate_timestamps_rejected(self) -> None:
        """Test that duplicate timestamps are rejected."""
        with pytest.raises(ValidationError, match="duplicate"):
            AnimationConfig(keyframes=[
                CameraKeyframe(timestamp=0.0),
                CameraKeyframe(timestamp=0.0),
            ])

    def test_dict_keyframes_coerced(self) -> None:
        """Test that dict entries are coerced into CameraKeyframe."""
        config = AnimationConfig(keyframes=[
            {"timestamp": 0.0, "zoom": 1.0},
            {"timestamp": 1.0, "zoom": 2.0},
        ])
        assert all(isinstance(kf, CameraKeyframe) for kf in config.keyframes)
        assert config.keyframes[1].zoom == 2.0

    def test_invalid_keyframe_entry_rejected(self) -> None:
        """Test that non-dict/keyframe entries are rejected."""
        with pytest.raises(ValidationError):
            AnimationConfig(keyframes=[42])  # type: ignore[list-item]

    def test_negative_duration_rejected(self) -> None:
        """Test that a negative duration is rejected."""
        kf = CameraKeyframe(timestamp=0.0)
        with pytest.raises(ValidationError):
            AnimationConfig(keyframes=[kf], duration_seconds=-1.0)

    def test_none_keyframes_coerced_to_empty(self) -> None:
        """Test that None keyframes coerces to an empty (rejected) list."""
        with pytest.raises(ValidationError):
            AnimationConfig(keyframes=None)  # type: ignore[arg-type]

    def test_equal_timestamps_after_coerce_still_rejected(self) -> None:
        """Test that coerced dicts with equal timestamps are rejected."""
        with pytest.raises(ValidationError, match="duplicate"):
            AnimationConfig(keyframes=[
                {"timestamp": 1.0},
                {"timestamp": 1.0},
            ])
