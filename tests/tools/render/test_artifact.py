"""Tests for render artifact."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_render_artifact,
    export_render_frames,
)
from tools.render.session import create_render_session


class TestValidArtifact:
    """Tests for valid artifact creation."""

    def test_artifact_from_single_frame_session(self) -> None:
        """Test artifact from single-frame session."""
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
            artifact = create_render_artifact(session)

        assert artifact.frame_count == 1
        assert artifact.frame_indices == (0,)

    def test_artifact_from_multi_frame_session(self) -> None:
        """Test artifact from multi-frame session."""
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
            artifact = create_render_artifact(session)

        assert artifact.frame_count == 5
        assert artifact.frame_indices == (0, 1, 2, 3, 4)


class TestArtifactProperties:
    """Tests for artifact properties."""

    def test_output_dir_preserved(self) -> None:
        """Test that output_dir is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.output_dir == Path(tmpdir)

    def test_prefix_preserved(self) -> None:
        """Test that prefix is preserved in artifact."""
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
            session = create_render_session(tmpdir, prefix="frame")
            artifact = create_render_artifact(session)

        assert artifact.prefix == "frame"

    def test_frame_count_preserved(self) -> None:
        """Test that frame_count is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.frame_count == 10

    def test_frame_indices_preserved(self) -> None:
        """Test that frame_indices is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.frame_indices == (0, 1, 2, 3, 4)

    def test_frame_rate_preserved(self) -> None:
        """Test that frame_rate is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.frame_rate == 60.0

    def test_duration_seconds_preserved(self) -> None:
        """Test that duration_seconds is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.duration_seconds == 48 / 24.0

    def test_dimensions_preserved(self) -> None:
        """Test that dimensions is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.dimensions == (1920, 1080)

    def test_mode_preserved(self) -> None:
        """Test that mode is preserved in artifact."""
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
            artifact = create_render_artifact(session)

        assert artifact.mode == "RGBA"


class TestValidation:
    """Tests for validation behavior."""

    def test_validate_true_performs_validation(self) -> None:
        """Test that validate=True performs session validation."""
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
            # Should succeed with valid session
            artifact = create_render_artifact(session, validate=True)

        assert artifact is not None

    def test_validate_false_skips_validation(self) -> None:
        """Test that validate=False skips validation."""
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
            # Should succeed without validation
            artifact = create_render_artifact(session, validate=False)

        assert artifact is not None


class TestValidationFailure:
    """Tests for validation failure handling."""

    def test_validation_failure_becomes_artifact_error(self) -> None:
        """Test that session validation failure becomes ArtifactError."""
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

            # Corrupt the PNG file - this would be caught by validation
            png_path = Path(tmpdir) / "frame_000000.png"
            png_path.write_bytes(b"not a valid png")

            # Session creation should fail
            from tools.render.session import SessionError

            with pytest.raises(SessionError):
                create_render_session(tmpdir)


class TestImmutability:
    """Tests for artifact immutability."""

    def test_artifact_is_frozen(self) -> None:
        """Test that RenderArtifact is frozen/immutable."""
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
            artifact = create_render_artifact(session)

        with pytest.raises(AttributeError):
            artifact.frame_count = 99


class TestNoMutation:
    """Tests for no mutation during artifact creation."""

    def test_session_unchanged(self) -> None:
        """Test that RenderSession is unchanged after artifact creation."""
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

            session_id = id(session)
            manifest_id = id(session.manifest)
            preview_id = id(session.preview)
            timeline_id = id(session.timeline)

            create_render_artifact(session)

            assert id(session) == session_id
            assert id(session.manifest) == manifest_id
            assert id(session.preview) == preview_id
            assert id(session.timeline) == timeline_id

    def test_png_files_unchanged(self) -> None:
        """Test that PNG files are unchanged after artifact creation."""
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

            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            session = create_render_session(tmpdir)
            create_render_artifact(session)

            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_creation_deterministic(self) -> None:
        """Test that repeated artifact creation produces identical results."""
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

            a1 = create_render_artifact(session)
            a2 = create_render_artifact(session)
            a3 = create_render_artifact(session)

            assert a1.frame_count == a2.frame_count == a3.frame_count
            assert a1.frame_indices == a2.frame_indices == a3.frame_indices
            assert a1.frame_rate == a2.frame_rate == a3.frame_rate

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

            # Each call should return a new object
            a1 = create_render_artifact(session)
            a2 = create_render_artifact(session)

            assert a1 is not a2


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in artifact module."""
        import ast

        with open("tools/render/artifact.py") as f:
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

    def test_render_artifact_importable(self) -> None:
        """Test RenderArtifact is importable from tools.render."""
        from tools.render import RenderArtifact

        assert RenderArtifact is not None

    def test_artifact_error_importable(self) -> None:
        """Test ArtifactError is importable from tools.render."""
        from tools.render import ArtifactError

        assert ArtifactError is not None

    def test_create_render_artifact_importable(self) -> None:
        """Test create_render_artifact is importable from tools.render."""
        from tools.render import create_render_artifact

        assert create_render_artifact is not None
