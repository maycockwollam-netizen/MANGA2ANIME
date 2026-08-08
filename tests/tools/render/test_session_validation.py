"""Tests for render session validation."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    export_render_frames,
    validate_render_session,
)
from tools.render.session import create_render_session


class TestValidSessionValidation:
    """Tests for valid session validation."""

    def test_valid_single_frame_session(self) -> None:
        """Test validation of single-frame session."""
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
            result = validate_render_session(session)

        assert result.frame_count == 1
        assert result.frame_indices == (0,)
        assert result.frame_rate == 24.0

    def test_valid_multi_frame_session(self) -> None:
        """Test validation of multi-frame session."""
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
            result = validate_render_session(session)

        assert result.frame_count == 5
        assert result.frame_indices == (0, 1, 2, 3, 4)
        assert result.frame_rate == 24.0


class TestValidationResultProperties:
    """Tests for RenderSessionValidation properties."""

    def test_frame_count(self) -> None:
        """Test frame_count in validation result."""
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
            result = validate_render_session(session)

        assert result.frame_count == 10

    def test_frame_indices(self) -> None:
        """Test frame_indices in validation result."""
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
            result = validate_render_session(session)

        assert result.frame_indices == (0, 1, 2, 3, 4)

    def test_frame_rate(self) -> None:
        """Test frame_rate in validation result."""
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
            result = validate_render_session(session)

        assert result.frame_rate == 60.0

    def test_duration_seconds(self) -> None:
        """Test duration_seconds in validation result."""
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
            result = validate_render_session(session)

        assert result.duration_seconds == 48 / 24.0

    def test_dimensions(self) -> None:
        """Test dimensions in validation result."""
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
            result = validate_render_session(session)

        assert result.dimensions == (1920, 1080)

    def test_mode(self) -> None:
        """Test mode in validation result."""
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
            result = validate_render_session(session)

        assert result.mode == "RGBA"


class TestValidationResultImmutability:
    """Tests for validation result immutability."""

    def test_validation_result_is_frozen(self) -> None:
        """Test that RenderSessionValidation is immutable."""
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
            result = validate_render_session(session)

        with pytest.raises(AttributeError):
            result.frame_count = 99


class TestManifestPreviewMismatch:
    """Tests for Manifest/Preview mismatch detection."""

    def test_detects_frame_count_mismatch(self) -> None:
        """Test that _verify_metadata_match detects frame_count mismatch."""
        from tools.render.session_validation import (
            SessionValidationError,
            _verify_metadata_match,
        )

        with pytest.raises(SessionValidationError, match="frame_count"):
            _verify_metadata_match("Manifest", "Preview", 5, 10, "frame_count")


class TestManifestTimelineMismatch:
    """Tests for Manifest/Timeline mismatch detection."""

    def test_detects_frame_count_mismatch(self) -> None:
        """Test that _verify_metadata_match detects frame_count mismatch."""
        from tools.render.session_validation import (
            SessionValidationError,
            _verify_metadata_match,
        )

        with pytest.raises(SessionValidationError, match="frame_count"):
            _verify_metadata_match("Manifest", "Timeline", 5, 10, "frame_count")


class TestPreviewTimelineMismatch:
    """Tests for Preview/Timeline mismatch detection."""

    def test_detects_frame_indices_mismatch(self) -> None:
        """Test that _verify_metadata_match detects frame_indices mismatch."""
        from tools.render.session_validation import (
            SessionValidationError,
            _verify_metadata_match,
        )

        with pytest.raises(SessionValidationError, match="frame_indices"):
            _verify_metadata_match(
                "Preview", "Timeline",
                (0, 1, 2), (0, 1, 3),
                "frame_indices"
            )


class TestSessionPropertyMismatch:
    """Tests for Session property mismatch detection."""

    def test_detects_frame_rate_mismatch(self) -> None:
        """Test that _verify_metadata_match detects frame_rate mismatch."""
        from tools.render.session_validation import (
            SessionValidationError,
            _verify_metadata_match,
        )

        with pytest.raises(SessionValidationError, match="frame_rate"):
            _verify_metadata_match("Session", "Manifest", 24.0, 30.0, "frame_rate")


class TestInvalidPNGDetection:
    """Tests for invalid PNG detection."""

    def test_invalid_png_raises_session_error(self) -> None:
        """Test that invalid PNG sequence raises SessionError during creation."""
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

            # Corrupt the PNG file
            png_path = Path(tmpdir) / "frame_000000.png"
            png_path.write_bytes(b"not a valid png")

            # Session creation should fail
            from tools.render.session import SessionError

            with pytest.raises(SessionError):
                create_render_session(tmpdir)


class TestTimelineMappingConsistency:
    """Tests for timeline mapping consistency."""

    def test_timeline_roundtrip_consistency(self) -> None:
        """Test that timeline timestamp mapping is internally consistent."""
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
            result = validate_render_session(session)

        # If we got here, timeline is consistent
        assert result.frame_count == 5


class TestNoMutation:
    """Tests for no mutation during validation."""

    def test_png_files_unchanged(self) -> None:
        """Test that PNG files are unchanged after validation."""
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

            # Validate session
            session = create_render_session(tmpdir)
            validate_render_session(session)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_session_unchanged(self) -> None:
        """Test that RenderSession is unchanged after validation."""
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

            # Get session properties before
            session_id = id(session)
            manifest_id = id(session.manifest)
            preview_id = id(session.preview)
            timeline_id = id(session.timeline)

            # Validate
            validate_render_session(session)

            # Verify nothing changed
            assert id(session) == session_id
            assert id(session.manifest) == manifest_id
            assert id(session.preview) == preview_id
            assert id(session.timeline) == timeline_id


class TestDeterminism:
    """Tests for deterministic validation."""

    def test_repeated_validation_deterministic(self) -> None:
        """Test that repeated validation produces identical results."""
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

            result1 = validate_render_session(session)
            result2 = validate_render_session(session)
            result3 = validate_render_session(session)

            assert result1.frame_count == result2.frame_count == result3.frame_count
            assert result1.frame_indices == result2.frame_indices == result3.frame_indices
            assert result1.frame_rate == result2.frame_rate == result3.frame_rate


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in session_validation module."""
        import ast

        with open("tools/render/session_validation.py") as f:
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

    def test_render_session_validation_importable(self) -> None:
        """Test RenderSessionValidation is importable from tools.render."""
        from tools.render import RenderSessionValidation

        assert RenderSessionValidation is not None

    def test_session_validation_error_importable(self) -> None:
        """Test SessionValidationError is importable from tools.render."""
        from tools.render import SessionValidationError

        assert SessionValidationError is not None

    def test_validate_render_session_importable(self) -> None:
        """Test validate_render_session is importable from tools.render."""
        from tools.render import validate_render_session

        assert validate_render_session is not None
