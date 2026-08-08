"""Tests for render sequence playback."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    PlaybackError,
    RenderFrame,
    RenderPlayback,
    create_render_preview,
    export_render_frames,
)


class TestConstruction:
    """Tests for RenderPlayback construction."""

    def test_construction_from_valid_render_preview(self) -> None:
        """Test that playback can be constructed from a valid RenderPreview."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

        assert isinstance(playback, RenderPlayback)
        assert playback.preview is preview


class TestInitialState:
    """Tests for initial playback state."""

    def test_initial_frame_index(self) -> None:
        """Test that initial frame index is the first frame."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

        assert playback.current_frame_index == 0

    def test_initial_playing_state(self) -> None:
        """Test that initial playing state is False."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

        assert playback.playing is False


class TestProperties:
    """Tests for playback properties."""

    def test_frame_count(self) -> None:
        """Test frame_count property."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(7)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

        assert playback.frame_count == 7

    def test_frame_rate(self) -> None:
        """Test frame_rate property."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=30.0)
            playback = RenderPlayback(preview=preview, frame_rate=30.0)

        assert playback.frame_rate == 30.0

    def test_frame_duration(self) -> None:
        """Test frame_duration property."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

        assert playback.frame_duration == 1.0 / 24.0


class TestPlayPause:
    """Tests for play() and pause()."""

    def test_play(self) -> None:
        """Test that play() marks playback as playing."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.play()
            assert playback.playing is True

    def test_pause(self) -> None:
        """Test that pause() marks playback as not playing."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.play()
            playback.pause()
            assert playback.playing is False

    def test_pause_preserves_position(self) -> None:
        """Test that pause() preserves current position."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(3)
            playback.pause()
            assert playback.current_frame_index == 3


class TestStop:
    """Tests for stop()."""

    def test_stop_resets_to_first_frame(self) -> None:
        """Test that stop() resets position to first frame."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(4)
            playback.stop()
            assert playback.current_frame_index == 0
            assert playback.playing is False


class TestSeek:
    """Tests for seek()."""

    def test_seek_to_first_frame(self) -> None:
        """Test seeking to the first frame."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(0)
            assert playback.current_frame_index == 0

    def test_seek_to_middle_frame(self) -> None:
        """Test seeking to a middle frame."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(10)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(5)
            assert playback.current_frame_index == 5

    def test_seek_to_final_frame(self) -> None:
        """Test seeking to the final frame."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(4)
            assert playback.current_frame_index == 4

    def test_invalid_seek_raises_error(self) -> None:
        """Test that invalid seek raises PlaybackError."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            with pytest.raises(PlaybackError, match="Invalid frame index"):
                playback.seek(99)


class TestStepping:
    """Tests for step_forward() and step_backward()."""

    def test_step_forward(self) -> None:
        """Test stepping forward."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.step_forward()
            assert playback.current_frame_index == 1

    def test_step_backward(self) -> None:
        """Test stepping backward."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(2)
            playback.step_backward()
            assert playback.current_frame_index == 1

    def test_forward_at_final_frame_is_deterministic(self) -> None:
        """Test that stepping forward at final frame clamps."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.seek(2)
            playback.step_forward()
            assert playback.current_frame_index == 2  # Clamped

    def test_backward_at_first_frame_is_deterministic(self) -> None:
        """Test that stepping backward at first frame clamps."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            playback.step_backward()
            assert playback.current_frame_index == 0  # Clamped


class TestCurrentFrameImage:
    """Tests for current_frame_image()."""

    def test_current_frame_image_delegates_correctly(self) -> None:
        """Test that current_frame_image() delegates to RenderPreview."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            img = playback.current_frame_image()
            assert img is not None

            # Compare with direct preview access
            direct_img = preview.frame_image(0)
            assert img.size == direct_img.size
            assert img.mode == direct_img.mode


class TestNoCaching:
    """Tests verifying no caching behavior."""

    def test_no_image_caching(self) -> None:
        """Test that current_frame_image() does not cache."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)
            playback = RenderPlayback(preview=preview, frame_rate=24.0)

            img1 = playback.current_frame_image()
            img2 = playback.current_frame_image()
            assert img1 is not img2  # Fresh load each call


class TestFrameRateValidation:
    """Tests for frame_rate validation."""

    def test_zero_frame_rate_rejected(self) -> None:
        """Test that zero frame_rate raises PlaybackError."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)

            with pytest.raises(PlaybackError, match="frame_rate must be positive"):
                RenderPlayback(preview=preview, frame_rate=0.0)

    def test_negative_frame_rate_rejected(self) -> None:
        """Test that negative frame_rate raises PlaybackError."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)

            with pytest.raises(PlaybackError, match="frame_rate must be positive"):
                RenderPlayback(preview=preview, frame_rate=-24.0)


class TestNoMutation:
    """Tests verifying no mutation of inputs."""

    def test_render_preview_unchanged(self) -> None:
        """Test that RenderPlayback does not modify RenderPreview."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)

            # Get original state
            original_count = preview.frame_count
            original_indices = preview.frame_indices

            # Use playback
            playback = RenderPlayback(preview=preview, frame_rate=24.0)
            playback.seek(2)
            playback.step_forward()
            playback.step_backward()
            playback.play()
            playback.pause()
            playback.stop()

            # Verify unchanged
            assert preview.frame_count == original_count
            assert preview.frame_indices == original_indices

    def test_png_files_unchanged(self) -> None:
        """Test that playback does not modify PNG files."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)

            # Get file timestamps before
            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Use playback
            playback = RenderPlayback(preview=preview, frame_rate=24.0)
            playback.seek(1)
            playback.current_frame_image()

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after


class TestDeterministicState:
    """Tests for deterministic state transitions."""

    def test_deterministic_state_transitions(self) -> None:
        """Test that state transitions are deterministic."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            preview = create_render_preview(tmpdir, frame_rate=24.0)

            # First playback sequence
            p1 = RenderPlayback(preview=preview, frame_rate=24.0)
            p1.seek(2)
            p1.step_forward()
            state1 = p1.current_frame_index

            # Second playback sequence
            p2 = RenderPlayback(preview=preview, frame_rate=24.0)
            p2.seek(2)
            p2.step_forward()
            state2 = p2.current_frame_index

            assert state1 == state2 == 3


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in playback module."""
        import ast

        with open("tools/render/playback.py") as f:
            source = f.read()

        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check for forbidden imports
        forbidden = [
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "AnimationOrchestrator",
            "threading",
        ]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"


class TestPublicAPI:
    """Tests for public API."""

    def test_render_playback_importable(self) -> None:
        """Test RenderPlayback is importable from tools.render."""
        from tools.render import RenderPlayback

        assert RenderPlayback is not None

    def test_playback_error_importable(self) -> None:
        """Test PlaybackError is importable from tools.render."""
        from tools.render import PlaybackError

        assert PlaybackError is not None


class TestEmptyPreview:
    """Tests for empty/invalid preview behavior."""

    def test_empty_preview_raises_error_at_construction(self) -> None:
        """Test that creating playback with empty preview raises error.

        Note: Empty preview is rejected by create_render_preview(),
        so this test verifies the boundary is correctly enforced.
        """
        from tools.render import PreviewError

        with tempfile.TemporaryDirectory() as tmpdir:
            # No files exported - preview creation will fail
            with pytest.raises(PreviewError):
                create_render_preview(tmpdir)
