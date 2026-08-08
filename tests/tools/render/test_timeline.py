"""Tests for frame timeline mapping."""

import math
import tempfile
from pathlib import Path

import pytest

from tools.render import (
    FrameTimeline,
    RenderFrame,
    TimelineError,
    create_frame_timeline,
    create_frame_timeline_from_preview,
    create_render_preview,
    export_render_frames,
)


class TestValidTimelines:
    """Tests for valid timeline creation."""

    def test_valid_single_frame_timeline(self) -> None:
        """Test timeline with a single frame."""
        timeline = create_frame_timeline([0], frame_rate=24.0)

        assert isinstance(timeline, FrameTimeline)
        assert timeline.frame_count == 1

    def test_valid_multi_frame_timeline(self) -> None:
        """Test timeline with multiple frames."""
        timeline = create_frame_timeline([0, 1, 2, 3, 4], frame_rate=24.0)

        assert timeline.frame_count == 5


class TestProperties:
    """Tests for timeline properties."""

    def test_frame_count(self) -> None:
        """Test frame_count property."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.frame_count == 3

    def test_frame_duration(self) -> None:
        """Test frame_duration property."""
        timeline = create_frame_timeline([0, 1], frame_rate=24.0)
        assert timeline.frame_duration == 1.0 / 24.0

    def test_start_timestamp(self) -> None:
        """Test start_timestamp property."""
        timeline = create_frame_timeline([5, 6, 7], frame_rate=24.0)
        assert timeline.start_timestamp == 0.0

    def test_end_timestamp(self) -> None:
        """Test end_timestamp property."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # 3 frames at 24 fps = 0.125 seconds
        assert timeline.end_timestamp == 3 / 24.0


class TestTimestampForFrame:
    """Tests for timestamp_for_frame()."""

    def test_timestamp_for_first_frame(self) -> None:
        """Test timestamp for first frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.timestamp_for_frame(0) == 0.0

    def test_timestamp_for_middle_frame(self) -> None:
        """Test timestamp for middle frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # Frame 1 is at position 1, timestamp = 1 * (1/24)
        assert math.isclose(timeline.timestamp_for_frame(1), 1 / 24.0)

    def test_timestamp_for_last_frame(self) -> None:
        """Test timestamp for last frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # Frame 2 is at position 2, timestamp = 2 * (1/24)
        assert math.isclose(timeline.timestamp_for_frame(2), 2 / 24.0)

    def test_timestamp_with_offset_indices(self) -> None:
        """Test timestamp for frames with non-zero starting index."""
        timeline = create_frame_timeline([10, 11, 12], frame_rate=24.0)
        # Frame 10 is at position 0, timestamp = 0
        assert timeline.timestamp_for_frame(10) == 0.0
        # Frame 11 is at position 1, timestamp = 1/24
        assert math.isclose(timeline.timestamp_for_frame(11), 1 / 24.0)
        # Frame 12 is at position 2, timestamp = 2/24
        assert math.isclose(timeline.timestamp_for_frame(12), 2 / 24.0)


class TestFramePosition:
    """Tests for frame_position()."""

    def test_position_first(self) -> None:
        """Test position of first frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.frame_position(0) == 0

    def test_position_middle(self) -> None:
        """Test position of middle frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.frame_position(1) == 1

    def test_position_last(self) -> None:
        """Test position of last frame."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.frame_position(2) == 2

    def test_position_with_offset_indices(self) -> None:
        """Test position with non-zero starting index."""
        timeline = create_frame_timeline([10, 11, 12], frame_rate=24.0)
        assert timeline.frame_position(10) == 0
        assert timeline.frame_position(11) == 1
        assert timeline.frame_position(12) == 2


class TestFrameForTimestamp:
    """Tests for frame_for_timestamp()."""

    def test_timestamp_zero(self) -> None:
        """Test frame for timestamp 0."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        assert timeline.frame_for_timestamp(0.0) == 0

    def test_timestamp_midpoint(self) -> None:
        """Test frame for midpoint timestamp."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # Midpoint between frame 0 and 1: floor(0.5) = 0
        assert timeline.frame_for_timestamp(0.5 / 24.0) == 0

    def test_timestamp_last_frame(self) -> None:
        """Test frame for last frame timestamp."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # Timestamp of frame 2 is 2/24
        assert math.isclose(timeline.frame_for_timestamp(2 / 24.0), 2)

    def test_exact_frame_boundary(self) -> None:
        """Test exact frame boundary behavior."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        # At exactly frame 1's timestamp
        assert timeline.frame_for_timestamp(1 / 24.0) == 1

    def test_timestamp_beyond_last_frame(self) -> None:
        """Test timestamp beyond sequence raises error."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)
        with pytest.raises(TimelineError, match="exceeds sequence duration"):
            timeline.frame_for_timestamp(10.0)


class TestFrameIndexValidation:
    """Tests for frame index validation."""

    def test_invalid_frame_index_rejected(self) -> None:
        """Test that invalid frame index raises error."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(TimelineError, match="not found"):
            timeline.timestamp_for_frame(99)

    def test_timestamp_for_invalid_index_rejected(self) -> None:
        """Test that invalid frame index in timestamp_for_frame raises error."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(TimelineError, match="Frame index 99 not found"):
            timeline.timestamp_for_frame(99)

    def test_position_for_invalid_index_rejected(self) -> None:
        """Test that invalid frame index in frame_position raises error."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(TimelineError, match="Frame index 99 not found"):
            timeline.frame_position(99)


class TestTimestampValidation:
    """Tests for timestamp validation."""

    def test_negative_timestamp_rejected(self) -> None:
        """Test that negative timestamp raises error."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(TimelineError, match="timestamp cannot be negative"):
            timeline.frame_for_timestamp(-0.1)


class TestSequenceValidation:
    """Tests for sequence validation."""

    def test_empty_sequence_rejected(self) -> None:
        """Test that empty sequence raises error."""
        with pytest.raises(TimelineError, match="frame_indices cannot be empty"):
            create_frame_timeline([], frame_rate=24.0)

    def test_duplicate_indices_rejected(self) -> None:
        """Test that duplicate indices raise error."""
        with pytest.raises(TimelineError, match="frame_indices must be unique"):
            create_frame_timeline([0, 1, 1, 2], frame_rate=24.0)


class TestSorting:
    """Tests for input sorting."""

    def test_unsorted_input_sorted(self) -> None:
        """Test that unsorted input is sorted deterministically."""
        timeline = create_frame_timeline([2, 0, 1], frame_rate=24.0)
        assert timeline.frame_indices == (0, 1, 2)


class TestImmutability:
    """Tests for immutability."""

    def test_timeline_is_frozen(self) -> None:
        """Test that FrameTimeline is immutable."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(AttributeError):
            timeline.frame_rate = 30.0

    def test_tuple_immutability(self) -> None:
        """Test that frame_indices tuple is immutable."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        with pytest.raises(TypeError):
            timeline.frame_indices[0] = 99

    def test_caller_iterable_not_mutated(self) -> None:
        """Test that caller's iterable is not mutated."""
        original = [2, 0, 1]
        create_frame_timeline(original, frame_rate=24.0)
        assert original == [2, 0, 1]


class TestFrameRateValidation:
    """Tests for frame rate validation."""

    def test_zero_frame_rate_rejected(self) -> None:
        """Test that zero frame_rate raises error."""
        with pytest.raises(TimelineError, match="frame_rate must be positive"):
            create_frame_timeline([0, 1], frame_rate=0.0)

    def test_negative_frame_rate_rejected(self) -> None:
        """Test that negative frame_rate raises error."""
        with pytest.raises(TimelineError, match="frame_rate must be positive"):
            create_frame_timeline([0, 1], frame_rate=-24.0)

    def test_nan_frame_rate_rejected(self) -> None:
        """Test that NaN frame_rate raises error."""
        with pytest.raises(TimelineError, match="frame_rate cannot be NaN"):
            create_frame_timeline([0, 1], frame_rate=float("nan"))

    def test_infinite_frame_rate_rejected(self) -> None:
        """Test that infinite frame_rate raises error."""
        with pytest.raises(TimelineError, match="frame_rate cannot be infinite"):
            create_frame_timeline([0, 1], frame_rate=float("inf"))


class TestDurationValidation:
    """Tests for duration validation."""

    def test_negative_duration_rejected(self) -> None:
        """Test that negative duration raises error."""
        with pytest.raises(
            TimelineError, match="duration_seconds cannot be negative"
        ):
            create_frame_timeline([0, 1], frame_rate=24.0, duration_seconds=-1.0)

    def test_nan_duration_rejected(self) -> None:
        """Test that NaN duration raises error."""
        with pytest.raises(TimelineError, match="duration_seconds cannot be NaN"):
            create_frame_timeline([0, 1], frame_rate=24.0, duration_seconds=float("nan"))

    def test_infinite_duration_rejected(self) -> None:
        """Test that infinite duration raises error."""
        with pytest.raises(TimelineError, match="duration_seconds cannot be infinite"):
            create_frame_timeline(
                [0, 1], frame_rate=24.0, duration_seconds=float("inf")
            )


class TestDeterministicBehavior:
    """Tests for deterministic behavior."""

    def test_repeated_lookups_deterministic(self) -> None:
        """Test that repeated lookups produce identical results."""
        timeline = create_frame_timeline([0, 1, 2], frame_rate=24.0)

        for _ in range(10):
            assert timeline.timestamp_for_frame(1) == 1 / 24.0
            assert timeline.frame_for_timestamp(0.5 / 24.0) == 0


class TestPreviewIntegration:
    """Tests for RenderPreview integration."""

    def test_create_timeline_from_preview(self) -> None:
        """Test creating timeline from RenderPreview."""
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
            timeline = create_frame_timeline_from_preview(preview)

        assert isinstance(timeline, FrameTimeline)
        assert timeline.frame_indices == (0, 1, 2, 3, 4)
        assert timeline.frame_rate == 24.0
        assert timeline.frame_count == 5


class TestNoMutation:
    """Tests verifying no mutation."""

    def test_no_filesystem_mutation(self) -> None:
        """Test that timeline creation doesn't mutate files."""
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

            # Get file timestamps before
            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Create timeline from preview (verifies no mutation)
            preview = create_render_preview(tmpdir)
            create_frame_timeline_from_preview(preview)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in timeline module."""
        import ast

        with open("tools/render/timeline.py") as f:
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

    def test_frame_timeline_importable(self) -> None:
        """Test FrameTimeline is importable from tools.render."""
        from tools.render import FrameTimeline

        assert FrameTimeline is not None

    def test_timeline_error_importable(self) -> None:
        """Test TimelineError is importable from tools.render."""
        from tools.render import TimelineError

        assert TimelineError is not None

    def test_create_frame_timeline_importable(self) -> None:
        """Test create_frame_timeline is importable from tools.render."""
        from tools.render import create_frame_timeline

        assert create_frame_timeline is not None

    def test_create_timeline_from_preview_importable(self) -> None:
        """Test create_frame_timeline_from_preview is importable."""
        from tools.render import create_frame_timeline_from_preview

        assert create_frame_timeline_from_preview is not None
