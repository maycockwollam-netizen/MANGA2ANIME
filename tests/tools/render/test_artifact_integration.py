"""Tests for render artifact integration."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_artifact_manifest,
    create_render_artifact,
    create_render_session,
    export_render_frames,
    write_artifact_manifest,
)


class TestOpenArtifact:
    """Tests for opening artifacts."""

    def test_open_valid_single_frame_artifact(self) -> None:
        """Test opening a valid single-frame artifact."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

        assert handle.info.frame_count == 1

    def test_open_valid_multi_frame_artifact(self) -> None:
        """Test opening a valid multi-frame artifact."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

        assert handle.info.frame_count == 5
        assert handle.info.frame_indices == (0, 1, 2, 3, 4)


class TestHandleImmutability:
    """Tests for handle immutability."""

    def test_handle_is_immutable(self) -> None:
        """Test that handle is immutable."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

        with pytest.raises(AttributeError):
            handle.loaded = None  # type: ignore

    def test_info_is_immutable(self) -> None:
        """Test that info property returns immutable data."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            info = handle.info

        with pytest.raises(AttributeError):
            info.frame_count = 99  # type: ignore


class TestDelegation:
    """Tests for delegation to existing APIs."""

    def test_info_delegates_correctly(self) -> None:
        """Test info property delegates to get_artifact_info."""
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
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

        assert handle.info.frame_count == 3
        assert handle.info.frame_rate == 24.0
        assert handle.info.dimensions == (800, 600)

    def test_frame_path_delegates_correctly(self) -> None:
        """Test frame_path delegates to get_artifact_frame_path."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            path = handle.frame_path(0)

            assert path.name == "frame_000000.png"
            assert path.exists()

    def test_frame_image_delegates_correctly(self) -> None:
        """Test frame_image delegates to get_artifact_frame_image."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            image = handle.frame_image(0)

        assert image.size == (800, 600)

    def test_timestamp_access_delegates_correctly(self) -> None:
        """Test frame_at_timestamp delegates to get_artifact_frame_at_timestamp."""
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
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            image = handle.frame_at_timestamp(0.1)

        assert image.size == (800, 600)


class TestInvalidAccess:
    """Tests for invalid access."""

    def test_invalid_frame_index(self) -> None:
        """Test invalid frame index raises error."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

            from tools.render.artifact_access import ArtifactAccessError

            with pytest.raises(ArtifactAccessError, match="Invalid frame_index"):
                handle.frame_path(99)

    def test_invalid_timestamp(self) -> None:
        """Test invalid timestamp raises error."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

            from tools.render.artifact_access import ArtifactAccessError

            with pytest.raises(ArtifactAccessError, match="cannot be negative"):
                handle.frame_at_timestamp(-1.0)


class TestOpenErrors:
    """Tests for open errors."""

    def test_missing_manifest(self) -> None:
        """Test missing manifest raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "nonexistent.json"

            from tools.render.artifact_integration import (
                ArtifactIntegrationError,
                open_render_artifact,
            )

            with pytest.raises(ArtifactIntegrationError, match="Failed to open"):
                open_render_artifact(manifest_path)

    def test_malformed_manifest(self) -> None:
        """Test malformed manifest raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text("not valid json {")

            from tools.render.artifact_integration import (
                ArtifactIntegrationError,
                open_render_artifact,
            )

            with pytest.raises(ArtifactIntegrationError, match="Failed to open"):
                open_render_artifact(manifest_path)

    def test_invalid_png_sequence(self) -> None:
        """Test invalid PNG sequence raises error."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Corrupt PNG file
            (Path(tmpdir) / "frame_000000.png").write_bytes(b"not valid png")

            from tools.render.artifact_integration import (
                ArtifactIntegrationError,
                open_render_artifact,
            )

            with pytest.raises(ArtifactIntegrationError, match="Failed to open"):
                open_render_artifact(manifest_path)

    def test_manifest_artifact_mismatch(self) -> None:
        """Test manifest/artifact mismatch raises error."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"

            # Write manifest with wrong frame_count
            manifest_path.write_text(
                '{"output_dir": "%s", "prefix": "%s", "frame_count": 99, '
                '"frame_indices": [0], "frame_rate": 24.0, "duration_seconds": 1.0, '
                '"dimensions": [800, 600], "mode": "RGBA"}'  # noqa: UP031
                % (tmpdir, manifest.prefix)
            )

            from tools.render.artifact_integration import (
                ArtifactIntegrationError,
                open_render_artifact,
            )

            with pytest.raises(ArtifactIntegrationError, match="Failed to open"):
                open_render_artifact(manifest_path)


class TestValidation:
    """Tests for validation behavior."""

    def test_validate_false_skips_validation(self) -> None:
        """Test validate=False skips validation."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Delete PNG file
            (Path(tmpdir) / "frame_000000.png").unlink()

            from tools.render.artifact_integration import open_render_artifact

            # Should not raise because validate=False
            handle = open_render_artifact(manifest_path, validate=False)
            assert handle.info.frame_count == 1

    def test_explicit_validation(self) -> None:
        """Test explicit validation through validate_render_artifact_handle."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import (
                open_render_artifact,
                validate_render_artifact_handle,
            )

            # Open with validate=False then explicitly validate
            handle = open_render_artifact(manifest_path, validate=False)

            # Should not raise - the handle was created from a valid artifact
            validate_render_artifact_handle(handle)


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_open_deterministic(self) -> None:
        """Test repeated open produces identical results."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            h1 = open_render_artifact(manifest_path)
            h2 = open_render_artifact(manifest_path)

            assert h1.info.frame_count == h2.info.frame_count


class TestNoCaching:
    """Tests for no caching."""

    def test_no_caching(self) -> None:
        """Test no caching is performed."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            h1 = open_render_artifact(manifest_path)
            h2 = open_render_artifact(manifest_path)

            # Each call creates new objects
            assert h1 is not h2
            assert h1.loaded is not h2.loaded


class TestNoMutation:
    """Tests for no mutation."""

    def test_artifact_unchanged(self) -> None:
        """Test artifact is unchanged after operations."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            artifact_id = id(handle.loaded.artifact)

            _ = handle.info
            _ = handle.frame_image(0)

            assert id(handle.loaded.artifact) == artifact_id

    def test_manifest_unchanged(self) -> None:
        """Test manifest is unchanged after operations."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)
            manifest_id = id(handle.loaded.manifest)

            _ = handle.info

            assert id(handle.loaded.manifest) == manifest_id

    def test_png_files_unchanged(self) -> None:
        """Test PNG files are unchanged after operations."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            _ = handle.frame_image(0)

            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_no_files_created(self) -> None:
        """Test no files are created during operations."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

            files_before = set(Path(tmpdir).iterdir())

            _ = handle.info
            _ = handle.frame_image(0)

            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after

    def test_no_files_deleted(self) -> None:
        """Test no files are deleted during operations."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            from tools.render.artifact_integration import open_render_artifact

            handle = open_render_artifact(manifest_path)

            png_path = Path(tmpdir) / "frame_000000.png"
            png_content_before = png_path.read_bytes()

            _ = handle.frame_image(0)

            png_content_after = png_path.read_bytes()

            assert png_content_before == png_content_after


class TestExceptionChaining:
    """Tests for exception chaining."""

    def test_exception_chaining(self) -> None:
        """Test original exception is preserved as __cause__."""
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
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Delete PNG file
            (Path(tmpdir) / "frame_000000.png").unlink()

            from tools.render.artifact_integration import (
                ArtifactIntegrationError,
                open_render_artifact,
            )

            with pytest.raises(ArtifactIntegrationError) as exc_info:
                open_render_artifact(manifest_path)

            assert exc_info.value.__cause__ is not None


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test no forbidden imports."""
        import ast

        with open("tools/render/artifact_integration.py") as f:
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

        forbidden = [
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "AnimationOrchestrator",
            "threading",
            "asyncio",
        ]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"


class TestPublicAPI:
    """Tests for public API."""

    def test_render_artifact_handle_importable(self) -> None:
        """Test RenderArtifactHandle is importable."""
        from tools.render import RenderArtifactHandle
        assert RenderArtifactHandle is not None

    def test_artifact_integration_error_importable(self) -> None:
        """Test ArtifactIntegrationError is importable."""
        from tools.render import ArtifactIntegrationError
        assert ArtifactIntegrationError is not None

    def test_open_render_artifact_importable(self) -> None:
        """Test open_render_artifact is importable."""
        from tools.render import open_render_artifact
        assert open_render_artifact is not None

    def test_validate_render_artifact_handle_importable(self) -> None:
        """Test validate_render_artifact_handle is importable."""
        from tools.render import validate_render_artifact_handle
        assert validate_render_artifact_handle is not None
