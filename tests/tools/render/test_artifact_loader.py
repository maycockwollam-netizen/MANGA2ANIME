"""Tests for render artifact loader."""

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


class TestValidLoading:
    """Tests for valid artifact loading."""

    def test_valid_single_frame_artifact_loads(self) -> None:
        """Test loading a valid single-frame artifact."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        assert loaded.artifact.frame_count == 1
        assert loaded.manifest.frame_count == 1

    def test_valid_multi_frame_artifact_loads(self) -> None:
        """Test loading a valid multi-frame artifact."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        assert loaded.artifact.frame_count == 5
        assert loaded.artifact.frame_indices == (0, 1, 2, 3, 4)
        assert loaded.manifest.frame_count == 5


class TestMetadataPreservation:
    """Tests for metadata preservation."""

    def test_manifest_metadata_preserved(self) -> None:
        """Test manifest metadata is preserved after loading."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        assert loaded.manifest.prefix == "frame"
        assert loaded.manifest.frame_rate == 24.0
        assert loaded.manifest.dimensions == (800, 600)
        assert loaded.manifest.mode == "RGBA"

    def test_artifact_metadata_reconstructed_correctly(self) -> None:
        """Test artifact metadata is reconstructed correctly from manifest."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        assert loaded.artifact.prefix == manifest.prefix
        assert loaded.artifact.frame_count == manifest.frame_count
        assert loaded.artifact.frame_indices == manifest.frame_indices
        assert loaded.artifact.frame_rate == manifest.frame_rate
        assert loaded.artifact.dimensions == manifest.dimensions
        assert loaded.artifact.mode == manifest.mode


class TestImmutability:
    """Tests for immutability."""

    def test_loaded_render_artifact_frozen(self) -> None:
        """Test LoadedRenderArtifact is frozen."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        with pytest.raises(AttributeError):
            loaded.artifact = None  # type: ignore

    def test_nested_artifact_remains_immutable(self) -> None:
        """Test nested artifact remains immutable."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        with pytest.raises(AttributeError):
            loaded.artifact.frame_count = 99  # type: ignore

    def test_nested_manifest_remains_immutable(self) -> None:
        """Test nested manifest remains immutable."""
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

            from tools.render.artifact_loader import load_render_artifact

            loaded = load_render_artifact(manifest_path)

        with pytest.raises(AttributeError):
            loaded.manifest.frame_count = 99  # type: ignore


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_manifest_raises_error(self) -> None:
        """Test missing manifest raises ArtifactLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "nonexistent.json"

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Failed to read manifest"):
                load_render_artifact(manifest_path)

    def test_malformed_json_raises_error(self) -> None:
        """Test malformed JSON raises ArtifactLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text("not valid json {")

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Failed to read manifest"):
                load_render_artifact(manifest_path)

    def test_invalid_manifest_raises_error(self) -> None:
        """Test invalid manifest raises ArtifactLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text('{"output_dir": "/tmp", "prefix": "frame", "frame_count": 0}')

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Failed to read manifest"):
                load_render_artifact(manifest_path)

    def test_missing_png_sequence_raises_error(self) -> None:
        """Test missing PNG sequence raises ArtifactLoadError."""
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
            Path(tmpdir, "frame_000000.png").unlink()

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Artifact validation failed"):
                load_render_artifact(manifest_path)

    def test_invalid_png_raises_error(self) -> None:
        """Test invalid PNG raises ArtifactLoadError."""
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
            png_path = Path(tmpdir) / "frame_000000.png"
            png_path.write_bytes(b"not valid png")

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Artifact validation failed"):
                load_render_artifact(manifest_path)

    def test_manifest_artifact_mismatch_raises_error(self) -> None:
        """Test manifest/artifact mismatch raises ArtifactLoadError."""
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
                '"dimensions": [800, 600], "mode": "RGBA"}' % (tmpdir, manifest.prefix)  # noqa: UP031
            )

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Artifact validation failed"):
                load_render_artifact(manifest_path)

    def test_png_metadata_mismatch_raises_error(self) -> None:
        """Test PNG metadata mismatch raises ArtifactLoadError."""
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
            export_render_frames(frames, tmpdir, canvas_size=(800, 600))
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"

            # Write manifest with wrong dimensions
            manifest_path.write_text(
                '{"output_dir": "%s", "prefix": "%s", "frame_count": 1, '
                '"frame_indices": [0], "frame_rate": 24.0, "duration_seconds": 1.0, '
                '"dimensions": [1920, 1080], "mode": "RGBA"}' % (tmpdir, manifest.prefix)  # noqa: UP031
            )

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError, match="Artifact validation failed"):
                load_render_artifact(manifest_path)


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
            Path(tmpdir, "frame_000000.png").unlink()

            from tools.render.artifact_loader import load_render_artifact

            # Should not raise because validate=False
            loaded = load_render_artifact(manifest_path, validate=False)
            assert loaded.artifact.frame_count == 1

    def test_validate_true_performs_validation(self) -> None:
        """Test validate=True performs validation."""
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
            Path(tmpdir, "frame_000000.png").unlink()

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError):
                load_render_artifact(manifest_path, validate=True)


class TestErrorChaining:
    """Tests for error chaining."""

    def test_original_exception_preserved(self) -> None:
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
            Path(tmpdir, "frame_000000.png").unlink()

            from tools.render.artifact_loader import (
                ArtifactLoadError,
                load_render_artifact,
            )

            with pytest.raises(ArtifactLoadError) as exc_info:
                load_render_artifact(manifest_path)
            assert exc_info.value.__cause__ is not None


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_loading_deterministic(self) -> None:
        """Test repeated loading produces identical results."""
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

            from tools.render.artifact_loader import load_render_artifact

            l1 = load_render_artifact(manifest_path)
            l2 = load_render_artifact(manifest_path)
            l3 = load_render_artifact(manifest_path)

            assert l1.artifact.frame_count == l2.artifact.frame_count == l3.artifact.frame_count


class TestNoMutation:
    """Tests for no mutation."""

    def test_no_filesystem_mutation(self) -> None:
        """Test loading does not mutate filesystem."""
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

            files_before = set(Path(tmpdir).iterdir())

            from tools.render.artifact_loader import load_render_artifact

            load_render_artifact(manifest_path)

            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after

    def test_no_files_created(self) -> None:
        """Test no files are created during loading."""
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

            png_files_before = set(Path(tmpdir).glob("*.png"))

            from tools.render.artifact_loader import load_render_artifact

            load_render_artifact(manifest_path)

            png_files_after = set(Path(tmpdir).glob("*.png"))

            assert png_files_before == png_files_after

    def test_no_files_deleted(self) -> None:
        """Test no files are deleted during loading."""
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

            png_path = Path(tmpdir) / "frame_000000.png"
            png_content_before = png_path.read_bytes()

            from tools.render.artifact_loader import load_render_artifact

            load_render_artifact(manifest_path)

            png_content_after = png_path.read_bytes()

            assert png_content_before == png_content_after


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

            from tools.render.artifact_loader import load_render_artifact

            l1 = load_render_artifact(manifest_path)
            l2 = load_render_artifact(manifest_path)

            # Each call creates new objects
            assert l1 is not l2
            assert l1.artifact is not l2.artifact
            assert l1.manifest is not l2.manifest


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test no forbidden imports."""
        import ast

        with open("tools/render/artifact_loader.py") as f:
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

    def test_loaded_render_artifact_importable(self) -> None:
        """Test LoadedRenderArtifact is importable."""
        from tools.render import LoadedRenderArtifact
        assert LoadedRenderArtifact is not None

    def test_artifact_load_error_importable(self) -> None:
        """Test ArtifactLoadError is importable."""
        from tools.render import ArtifactLoadError
        assert ArtifactLoadError is not None

    def test_load_render_artifact_importable(self) -> None:
        """Test load_render_artifact is importable."""
        from tools.render import load_render_artifact
        assert load_render_artifact is not None
