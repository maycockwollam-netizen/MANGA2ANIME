"""Tests for render session orchestration."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    RenderPlayback,
    RenderSession,
    SessionError,
    create_render_session,
    export_render_frames,
)


class TestConstruction:
    """Tests for session construction."""

    def test_valid_single_frame_session(self) -> None:
        """Test session with a single frame."""
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
            session = create_render_session(tmpdir)

        assert isinstance(session, RenderSession)
        assert session.frame_count == 1

    def test_valid_multi_frame_session(self) -> None:
        """Test session with multiple frames."""
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
            session = create_render_session(tmpdir)

        assert session.frame_count == 5


class TestSessionArtifacts:
    """Tests for session artifact containment."""

    def test_session_contains_manifest(self) -> None:
        """Test that session contains a manifest."""
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
            session = create_render_session(tmpdir)

        assert session.manifest is not None

    def test_session_contains_preview(self) -> None:
        """Test that session contains a preview."""
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
            session = create_render_session(tmpdir)

        assert session.preview is not None

    def test_session_contains_timeline(self) -> None:
        """Test that session contains a timeline."""
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
            session = create_render_session(tmpdir)

        assert session.timeline is not None


class TestConsistency:
    """Tests for metadata consistency."""

    def test_manifest_preview_frame_indices_match(self) -> None:
        """Test that manifest and preview have matching frame indices."""
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
            session = create_render_session(tmpdir)

        assert session.manifest.frame_indices == session.preview.frame_indices

    def test_manifest_timeline_frame_indices_match(self) -> None:
        """Test that manifest and timeline have matching frame indices."""
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
            session = create_render_session(tmpdir)

        assert session.manifest.frame_indices == session.timeline.frame_indices

    def test_frame_count_identical(self) -> None:
        """Test that all artifacts report identical frame count."""
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
            session = create_render_session(tmpdir)

        assert session.manifest.frame_count == session.preview.frame_count
        assert session.manifest.frame_count == session.timeline.frame_count

    def test_frame_rate_identical(self) -> None:
        """Test that all artifacts report identical frame rate."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 30.0,
                frame_rate=30.0,
                duration_frames=30,
                transforms={},
            )
            for i in range(10)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir, frame_rate=30.0)

        assert session.manifest.frame_rate == session.preview.frame_rate
        assert session.manifest.frame_rate == session.timeline.frame_rate

    def test_duration_identical(self) -> None:
        """Test that all artifacts report identical duration."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(48)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

        assert session.manifest.duration_seconds == session.preview.duration_seconds
        assert session.manifest.duration_seconds == session.timeline.duration_seconds

    def test_dimensions_from_manifest(self) -> None:
        """Test that dimensions are available from manifest."""
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
            export_render_frames(frames, tmpdir, canvas_size=(640, 480))
            session = create_render_session(tmpdir)

        assert session.dimensions == (640, 480)

    def test_mode_from_manifest(self) -> None:
        """Test that mode is available from manifest."""
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
            session = create_render_session(tmpdir)

        assert session.mode == "RGBA"


class TestConvenienceProperties:
    """Tests for session convenience properties."""

    def test_frame_count_property(self) -> None:
        """Test frame_count convenience property."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(8)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

        assert session.frame_count == 8

    def test_frame_rate_property(self) -> None:
        """Test frame_rate convenience property."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=30.0,
                duration_frames=30,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir, frame_rate=30.0)

        assert session.frame_rate == 30.0

    def test_duration_seconds_property(self) -> None:
        """Test duration_seconds convenience property."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(24)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

        assert session.duration_seconds == 24 / 24.0

    def test_dimensions_property(self) -> None:
        """Test dimensions convenience property."""
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
            export_render_frames(frames, tmpdir, canvas_size=(1920, 1080))
            session = create_render_session(tmpdir)

        assert session.dimensions == (1920, 1080)

    def test_mode_property(self) -> None:
        """Test mode convenience property."""
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
            session = create_render_session(tmpdir)

        assert session.mode == "RGBA"


class TestPlayback:
    """Tests for session playback integration."""

    def test_playback_returns_render_playback(self) -> None:
        """Test that playback() returns a RenderPlayback."""
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
            session = create_render_session(tmpdir)
            playback = session.playback()

        assert isinstance(playback, RenderPlayback)

    def test_playback_uses_session_preview(self) -> None:
        """Test that playback uses the session's preview."""
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
            session = create_render_session(tmpdir)
            playback = session.playback()

        assert playback.preview is session.preview

    def test_playback_starts_at_first_frame(self) -> None:
        """Test that playback starts at the first frame."""
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
            session = create_render_session(tmpdir)
            playback = session.playback()

        assert playback.current_frame_index == 0

    def test_playback_independent_between_calls(self) -> None:
        """Test that playback instances are independent."""
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
            session = create_render_session(tmpdir)

            p1 = session.playback()
            p1.seek(3)
            p2 = session.playback()

            assert p2.current_frame_index == 0
            assert p1.current_frame_index == 3

    def test_playback_manipulation_does_not_mutate_session(self) -> None:
        """Test that manipulating playback doesn't mutate the session."""
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
            session = create_render_session(tmpdir)

            # Get original preview reference
            original_preview = session.preview

            # Manipulate playback
            playback = session.playback()
            playback.seek(3)

            # Session should be unchanged
            assert session.preview is original_preview
            assert session.frame_count == 5

    def test_playback_can_seek_and_step(self) -> None:
        """Test that playback can seek and step correctly."""
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
            session = create_render_session(tmpdir)
            playback = session.playback()

            playback.seek(5)
            assert playback.current_frame_index == 5

            playback.step_forward()
            assert playback.current_frame_index == 6

            playback.step_backward()
            assert playback.current_frame_index == 5


class TestErrors:
    """Tests for session error handling."""

    def test_empty_sequence_rejected(self) -> None:
        """Test that empty sequence raises SessionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SessionError):
                create_render_session(tmpdir)

    def test_invalid_png_sequence_rejected(self) -> None:
        """Test that invalid PNG sequence raises SessionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bad PNG file
            bad_png = Path(tmpdir) / "frame_000000.png"
            bad_png.write_bytes(b"not a valid png")

            with pytest.raises(SessionError):
                create_render_session(tmpdir)

    def test_invalid_frame_rate_rejected(self) -> None:
        """Test that invalid frame_rate is handled appropriately."""
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

            # Zero frame rate should raise error
            with pytest.raises(SessionError):
                create_render_session(tmpdir, frame_rate=0.0)


class TestImmutability:
    """Tests for session immutability."""

    def test_session_is_frozen(self) -> None:
        """Test that RenderSession is frozen."""
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
            session = create_render_session(tmpdir)

        with pytest.raises(AttributeError):
            session.manifest = None

    def test_manifest_cannot_be_replaced(self) -> None:
        """Test that manifest cannot be replaced."""
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
            session = create_render_session(tmpdir)

        with pytest.raises(AttributeError):
            session.manifest = None

    def test_preview_cannot_be_replaced(self) -> None:
        """Test that preview cannot be replaced."""
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
            session = create_render_session(tmpdir)

        with pytest.raises(AttributeError):
            session.preview = None

    def test_timeline_cannot_be_replaced(self) -> None:
        """Test that timeline cannot be replaced."""
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
            session = create_render_session(tmpdir)

        with pytest.raises(AttributeError):
            session.timeline = None


class TestReadOnly:
    """Tests for read-only behavior."""

    def test_png_files_unchanged(self) -> None:
        """Test that session creation doesn't modify PNG files."""
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

            # Create session
            create_render_session(tmpdir)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_no_files_created(self) -> None:
        """Test that session creation doesn't create new files."""
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

            # Count files before
            files_before = set(Path(tmpdir).iterdir())

            # Create session
            create_render_session(tmpdir)

            # Count files after
            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after

    def test_no_files_deleted(self) -> None:
        """Test that session creation doesn't delete files."""
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

            # Count files before
            files_before = set(Path(tmpdir).iterdir())

            # Create session
            create_render_session(tmpdir)

            # Count files after
            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_produces_equivalent_metadata(self) -> None:
        """Test that same input produces equivalent session metadata."""
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

            session1 = create_render_session(tmpdir)
            session2 = create_render_session(tmpdir)

            assert session1.frame_count == session2.frame_count
            assert session1.frame_rate == session2.frame_rate
            assert session1.duration_seconds == session2.duration_seconds
            assert session1.manifest.frame_indices == session2.manifest.frame_indices


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in session module."""
        import ast

        with open("tools/render/session.py") as f:
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

    def test_render_session_importable(self) -> None:
        """Test RenderSession is importable from tools.render."""
        from tools.render import RenderSession

        assert RenderSession is not None

    def test_session_error_importable(self) -> None:
        """Test SessionError is importable from tools.render."""
        from tools.render import SessionError

        assert SessionError is not None

    def test_create_render_session_importable(self) -> None:
        """Test create_render_session is importable from tools.render."""
        from tools.render import create_render_session

        assert create_render_session is not None
