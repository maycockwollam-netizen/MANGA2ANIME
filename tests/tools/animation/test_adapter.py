"""Tests for camera animator source adapter."""

from pathlib import Path

import pytest

from tools.animation import (
    AnimationConfig,
    AnimationError,
    CameraKeyframe,
    KeyframeAnimator,
    SourceAdapter,
)
from tools.frame.models import FrameTransform


class TestSourceAdapterBasics:
    """Tests for SourceAdapter basic functionality."""

    def test_adapter_binds_animator_and_path(self, tmp_path: Path) -> None:
        """Test that adapter exposes the bound animator and source path."""
        animator = KeyframeAnimator()
        path = tmp_path / "img.png"
        adapter = SourceAdapter(animator, path)

        assert adapter.animator is animator
        assert adapter.source_path == path

    def test_adapter_source_path_coerced_to_path(self) -> None:
        """Test that a string source path is coerced to Path."""
        adapter = SourceAdapter(KeyframeAnimator(), "img.png")
        assert isinstance(adapter.source_path, Path)
        assert adapter.source_path == Path("img.png")


class TestSourceAdapterForwarding:
    """Tests for SourceAdapter forwarding behavior."""

    def test_adapter_attaches_source_path(self, tmp_path: Path) -> None:
        """Test that the adapter attaches the bound path to results."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.0),
            CameraKeyframe(timestamp=1.0, zoom=2.0),
        ])
        path = tmp_path / "frame.png"
        adapter = SourceAdapter(KeyframeAnimator(), path)

        result = adapter.evaluate(config, 0.5)

        assert isinstance(result, FrameTransform)
        assert result.source_path == path

    def test_adapter_preserves_interpolated_values(self, tmp_path: Path) -> None:
        """Test that the adapter preserves interpolated transform values."""
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.0, focus_x=0.5, focus_y=0.5),
            CameraKeyframe(timestamp=1.0, zoom=3.0, focus_x=0.3, focus_y=0.7),
        ])
        adapter = SourceAdapter(KeyframeAnimator(), tmp_path / "img.png")

        result = adapter.evaluate(config, 0.5)

        assert result.scale == 2.0
        assert result.anchor_x == 0.4
        assert result.anchor_y == 0.6

    def test_adapter_does_not_mutate_underlying(self, tmp_path: Path) -> None:
        """Test that adapter does not mutate the underlying animator's output."""
        animator = KeyframeAnimator()
        config = AnimationConfig(keyframes=[
            CameraKeyframe(timestamp=0.0, zoom=1.0),
            CameraKeyframe(timestamp=1.0, zoom=2.0),
        ])
        raw = animator.evaluate(config, 0.5)
        assert raw.source_path is None

        adapter = SourceAdapter(animator, tmp_path / "img.png")
        adapted = adapter.evaluate(config, 0.5)
        assert adapted.source_path == tmp_path / "img.png"
        # Underlying raw output unchanged.
        assert raw.source_path is None


class TestSourceAdapterExceptions:
    """Tests for SourceAdapter exception propagation."""

    def test_animation_error_propagates(self, tmp_path: Path) -> None:
        """Test that AnimationError propagates from the underlying animator."""

        class FailingAnimator:
            def evaluate(self, config: AnimationConfig, time: float):
                raise AnimationError("eval failed")

        adapter = SourceAdapter(FailingAnimator(), tmp_path / "img.png")
        with pytest.raises(AnimationError, match="eval failed"):
            adapter.evaluate(AnimationConfig(keyframes=[CameraKeyframe(timestamp=0.0)]), 0.0)
