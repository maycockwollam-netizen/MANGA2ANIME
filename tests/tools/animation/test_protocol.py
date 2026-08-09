"""Tests for camera animator protocol contract."""

import pytest

from tools.animation import (
    AnimationConfig,
    AnimationConfigError,
    AnimationError,
    AnimationEvalError,
    AnimationKeyframeError,
    CameraAnimator,
    KeyframeAnimator,
)


class TestCameraAnimatorProtocolCompliance:
    """Tests for CameraAnimator protocol structural typing."""

    def test_keyframe_animator_satisfies_protocol(self) -> None:
        """Test that KeyframeAnimator satisfies the CameraAnimator protocol."""
        assert isinstance(KeyframeAnimator(), CameraAnimator)

    def test_class_without_evaluate_does_not_satisfy(self) -> None:
        """Test that a class without evaluate method does not satisfy."""

        class NotAnAnimator:
            def render(self, config: AnimationConfig, time: float):  # pragma: no cover
                ...

        assert not isinstance(NotAnAnimator(), CameraAnimator)

    def test_camera_animator_is_runtime_checkable(self) -> None:
        """Test that isinstance() works at runtime for CameraAnimator."""
        assert isinstance(KeyframeAnimator(), CameraAnimator)
        assert not isinstance("not an animator", CameraAnimator)
        assert not isinstance(123, CameraAnimator)

    def test_camera_animator_protocol_is_type(self) -> None:
        """Test that CameraAnimator itself is a type/class."""
        assert isinstance(CameraAnimator, type)


class TestAnimationImports:
    """Tests for animation module imports."""

    def test_camera_animator_importable(self) -> None:
        """Test CameraAnimator is importable from tools.animation."""
        assert CameraAnimator is not None

    def test_keyframe_animator_importable(self) -> None:
        """Test KeyframeAnimator is importable from tools.animation."""
        assert KeyframeAnimator is not None

    def test_animation_error_hierarchy(self) -> None:
        """Test animation exception hierarchy."""
        assert issubclass(AnimationConfigError, AnimationError)
        assert issubclass(AnimationKeyframeError, AnimationError)
        assert issubclass(AnimationEvalError, AnimationError)

    def test_animation_errors_can_be_raised(self) -> None:
        """Test that animation exceptions can be raised."""
        with pytest.raises(AnimationError):
            raise AnimationError("test")
        with pytest.raises(AnimationConfigError):
            raise AnimationConfigError("config")
        with pytest.raises(AnimationKeyframeError):
            raise AnimationKeyframeError("keyframe")
        with pytest.raises(AnimationEvalError):
            raise AnimationEvalError("eval")
