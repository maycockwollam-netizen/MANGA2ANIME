"""Tests for render session access API."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from tools.render import (
    RenderFrame,
    export_render_frames,
    get_frame_at_timestamp,
    get_frame_image,
    get_frame_path,
    get_session_info,
)
from tools.render.session import create_render_session


class TestGetSessionInfo:
    """Tests for get_session_info()."""

    def test_valid_session_info(self) -> None:
        """Test that get_session_info returns correct info."""
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
            info = get_session_info(session)

        assert info.frame_count == 5
        assert info.frame_rate == 24.0
        assert info.duration_seconds == 5 / 24.0
        assert info.dimensions == (800, 600)
        assert info.mode == "RGBA"
        assert info.first_frame_index == 0
        assert info.last_frame_index == 4


class TestSessionInfoProperties:
    """Tests for RenderSessionInfo properties."""

    def test_frame_count(self) -> None:
        """Test frame_count property."""
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
            info = get_session_info(session)

        assert info.frame_count == 10

    def test_frame_rate(self) -> None:
        """Test frame_rate property."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=60.0,
                duration_frames=60,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir, frame_rate=60.0)
            info = get_session_info(session)

        assert info.frame_rate == 60.0

    def test_duration_seconds(self) -> None:
        """Test duration_seconds property."""
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
            info = get_session_info(session)

        assert info.duration_seconds == 48 / 24.0

    def test_dimensions(self) -> None:
        """Test dimensions property."""
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
            info = get_session_info(session)

        assert info.dimensions == (1920, 1080)

    def test_mode(self) -> None:
        """Test mode property."""
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
            info = get_session_info(session)

        assert info.mode == "RGBA"

    def test_first_frame_index(self) -> None:
        """Test first_frame_index property."""
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
            info = get_session_info(session)

        assert info.first_frame_index == 0

    def test_last_frame_index(self) -> None:
        """Test last_frame_index property."""
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
            info = get_session_info(session)

        assert info.last_frame_index == 9


class TestGetFrameImage:
    """Tests for get_frame_image()."""

    def test_returns_correct_image(self) -> None:
        """Test that get_frame_image returns the correct image."""
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

            for i in range(5):
                img = get_frame_image(session, i)
                assert isinstance(img, Image.Image)
                assert img.size == (800, 600)
                assert img.mode == "RGBA"

    def test_invalid_frame_index_raises_error(self) -> None:
        """Test that invalid frame index raises SessionAccessError."""
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

            from tools.render.session_access import SessionAccessError

            with pytest.raises(SessionAccessError, match="Frame index 99 not found"):
                get_frame_image(session, 99)


class TestGetFramePath:
    """Tests for get_frame_path()."""

    def test_returns_correct_path(self) -> None:
        """Test that get_frame_path returns the correct path."""
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

            for i in range(5):
                path = get_frame_path(session, i)
                assert isinstance(path, Path)
                assert path.exists()
                assert path.suffix == ".png"

    def test_invalid_frame_index_raises_error(self) -> None:
        """Test that invalid frame index raises SessionAccessError."""
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

            from tools.render.session_access import SessionAccessError

            with pytest.raises(SessionAccessError, match="Frame index 99 not found"):
                get_frame_path(session, 99)


class TestGetFrameAtTimestamp:
    """Tests for get_frame_at_timestamp()."""

    def test_timestamp_resolves_through_timeline(self) -> None:
        """Test that timestamp resolves to correct frame through timeline."""
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

            # At timestamp 0, should get frame 0
            img0 = get_frame_at_timestamp(session, 0.0)
            assert isinstance(img0, Image.Image)

            # At timestamp of frame 2 (2/24), should get frame 2
            img2 = get_frame_at_timestamp(session, 2 / 24.0)
            assert isinstance(img2, Image.Image)

    def test_timestamp_below_zero_raises_error(self) -> None:
        """Test that negative timestamp raises SessionAccessError."""
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

            from tools.render.session_access import SessionAccessError

            with pytest.raises(SessionAccessError, match="timestamp cannot be negative"):
                get_frame_at_timestamp(session, -0.1)

    def test_timestamp_beyond_duration_raises_error(self) -> None:
        """Test that timestamp beyond duration raises SessionAccessError."""
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

            from tools.render.session_access import SessionAccessError

            with pytest.raises(SessionAccessError, match="exceeds sequence duration"):
                get_frame_at_timestamp(session, 100.0)


class TestSessionImmutability:
    """Tests for session immutability during access."""

    def test_session_remains_unchanged(self) -> None:
        """Test that RenderSession remains unchanged after access."""
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

            # Access session info
            info_before = get_session_info(session)

            # Access frames
            get_frame_image(session, 0)
            get_frame_path(session, 0)
            get_frame_at_timestamp(session, 0.0)

            # Session should be unchanged
            info_after = get_session_info(session)
            assert info_before == info_after

    def test_preview_remains_unchanged(self) -> None:
        """Test that RenderPreview remains unchanged after access."""
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

            preview_before = session.preview

            # Access frames
            get_frame_image(session, 0)
            get_frame_image(session, 1)

            # Preview should be unchanged
            assert session.preview is preview_before

    def test_timeline_remains_unchanged(self) -> None:
        """Test that FrameTimeline remains unchanged after access."""
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

            timeline_before = session.timeline

            # Access frames
            get_frame_at_timestamp(session, 0.0)
            get_frame_at_timestamp(session, 1 / 24.0)

            # Timeline should be unchanged
            assert session.timeline is timeline_before


class TestReadOnly:
    """Tests for read-only behavior."""

    def test_png_files_unchanged(self) -> None:
        """Test that PNG files remain unchanged after access."""
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

            # Get file timestamps before
            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Create session and access frames
            session = create_render_session(tmpdir)
            get_frame_image(session, 0)
            get_frame_image(session, 1)
            get_frame_at_timestamp(session, 0.0)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_no_files_created(self) -> None:
        """Test that access doesn't create new files."""
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

            # Access frames
            session = create_render_session(tmpdir)
            get_session_info(session)
            get_frame_image(session, 0)
            get_frame_path(session, 0)

            # Count files after
            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_access_deterministic(self) -> None:
        """Test that repeated access produces identical results."""
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

            for _ in range(10):
                info = get_session_info(session)
                assert info.frame_count == 5

                img = get_frame_image(session, 2)
                assert img.size == (800, 600)

                path = get_frame_path(session, 2)
                assert path.exists()

    def test_no_caching(self) -> None:
        """Test that no caching is performed."""
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

            # Multiple calls should return independent image objects
            img1 = get_frame_image(session, 0)
            img2 = get_frame_image(session, 0)

            # Images should be separate objects (no caching)
            assert img1 is not img2


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in session_access module."""
        import ast

        with open("tools/render/session_access.py") as f:
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

    def test_render_session_info_importable(self) -> None:
        """Test RenderSessionInfo is importable from tools.render."""
        from tools.render import RenderSessionInfo

        assert RenderSessionInfo is not None

    def test_session_access_error_importable(self) -> None:
        """Test SessionAccessError is importable from tools.render."""
        from tools.render import SessionAccessError

        assert SessionAccessError is not None

    def test_get_session_info_importable(self) -> None:
        """Test get_session_info is importable from tools.render."""
        from tools.render import get_session_info

        assert get_session_info is not None

    def test_get_frame_image_importable(self) -> None:
        """Test get_frame_image is importable from tools.render."""
        from tools.render import get_frame_image

        assert get_frame_image is not None

    def test_get_frame_path_importable(self) -> None:
        """Test get_frame_path is importable from tools.render."""
        from tools.render import get_frame_path

        assert get_frame_path is not None

    def test_get_frame_at_timestamp_importable(self) -> None:
        """Test get_frame_at_timestamp is importable from tools.render."""
        from tools.render import get_frame_at_timestamp

        assert get_frame_at_timestamp is not None
