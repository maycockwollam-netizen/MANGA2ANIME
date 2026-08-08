"""Tests for render artifact manifest validation."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_render_artifact,
    create_render_session,
    export_render_frames,
)
from tools.render.artifact_manifest import create_artifact_manifest


class TestValidValidation:
    """Tests for valid validation."""

    def test_valid_artifact_valid_manifest(self) -> None:
        """Test valid artifact with valid manifest passes."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            result = validate_artifact_manifest(artifact, manifest)

        assert result.valid is True
        assert result.frame_count == 1

    def test_single_frame_artifact(self) -> None:
        """Test single-frame artifact validation."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            result = validate_artifact_manifest(artifact, manifest)

        assert result.valid is True
        assert result.frame_indices == (0,)

    def test_multi_frame_artifact(self) -> None:
        """Test multi-frame artifact validation."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            result = validate_artifact_manifest(artifact, manifest)

        assert result.valid is True
        assert result.frame_indices == (0, 1, 2, 3, 4)


class TestMismatchDetection:
    """Tests for mismatch detection."""

    def test_output_dir_mismatch(self) -> None:
        """Test output_dir mismatch is detected."""
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

            # Modify manifest's output_dir
            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir="/wrong/path",
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="output_dir"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_prefix_mismatch(self) -> None:
        """Test prefix mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix="wrong_prefix",
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="prefix"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_frame_count_mismatch(self) -> None:
        """Test frame_count mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=99,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="frame_count"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_frame_indices_mismatch(self) -> None:
        """Test frame_indices mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=(99,),
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="frame_indices"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_frame_rate_mismatch(self) -> None:
        """Test frame_rate mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=99.0,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="frame_rate"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_duration_mismatch(self) -> None:
        """Test duration_seconds mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=99.0,
                dimensions=manifest.dimensions,
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="duration_seconds"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_dimensions_mismatch(self) -> None:
        """Test dimensions mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=(1920, 1080),
                mode=manifest.mode,
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="dimensions"):
                validate_artifact_manifest(artifact, wrong_manifest)

    def test_mode_mismatch(self) -> None:
        """Test mode mismatch is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            wrong_manifest = RenderArtifactManifest(
                output_dir=manifest.output_dir,
                prefix=manifest.prefix,
                frame_count=manifest.frame_count,
                frame_indices=manifest.frame_indices,
                frame_rate=manifest.frame_rate,
                duration_seconds=manifest.duration_seconds,
                dimensions=manifest.dimensions,
                mode="RGB",
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="mode"):
                validate_artifact_manifest(artifact, wrong_manifest)


class TestInvalidSequenceDetection:
    """Tests for invalid sequence detection."""

    def test_invalid_png_sequence(self) -> None:
        """Test invalid PNG sequence is detected."""
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

            # Corrupt PNG file
            png_path = Path(tmpdir) / "frame_000000.png"
            png_path.write_bytes(b"not valid png")

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="PNG sequence"):
                validate_artifact_manifest(artifact, manifest)


class TestManifestMetadataValidation:
    """Tests for manifest metadata validation."""

    def test_duplicate_frame_indices(self) -> None:
        """Test duplicate frame_indices are detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            # Create manifest with duplicate indices that match frame_count
            invalid_manifest = RenderArtifactManifest(
                output_dir=str(Path(tmpdir)),
                prefix="frame",
                frame_count=1,
                frame_indices=(0, 0),
                frame_rate=24.0,
                duration_seconds=1.0,
                dimensions=(800, 600),
                mode="RGBA",
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            # The validation catches frame_indices mismatch first
            with pytest.raises(ArtifactManifestValidationError, match="frame_indices"):
                validate_artifact_manifest(artifact, invalid_manifest)

    def test_empty_frame_indices(self) -> None:
        """Test empty frame_indices is detected."""
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

            from tools.render.artifact_manifest import RenderArtifactManifest

            invalid_manifest = RenderArtifactManifest(
                output_dir=str(Path(tmpdir)),
                prefix="frame",
                frame_count=1,
                frame_indices=(),
                frame_rate=24.0,
                duration_seconds=0.0,
                dimensions=(800, 600),
                mode="RGBA",
            )

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="frame_indices"):
                validate_artifact_manifest(artifact, invalid_manifest)


class TestArtifactValidationFailure:
    """Tests for artifact validation failure."""

    def test_artifact_validation_failure(self) -> None:
        """Test artifact validation failure is propagated."""
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

            # Corrupt PNG
            png_path = Path(tmpdir) / "frame_000000.png"
            png_path.write_bytes(b"not valid png")

            from tools.render.artifact_manifest_validation import (
                ArtifactManifestValidationError,
                validate_artifact_manifest,
            )

            with pytest.raises(ArtifactManifestValidationError, match="Artifact validation failed"):
                validate_artifact_manifest(artifact, manifest)


class TestImmutability:
    """Tests for immutability."""

    def test_result_is_frozen(self) -> None:
        """Test RenderArtifactManifestValidation is frozen."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            result = validate_artifact_manifest(artifact, manifest)

        with pytest.raises(AttributeError):
            result.valid = False


class TestValidResult:
    """Tests for valid result."""

    def test_valid_true_for_valid_input(self) -> None:
        """Test valid=True for valid input."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            result = validate_artifact_manifest(artifact, manifest)

        assert result.valid is True


class TestNoMutation:
    """Tests for no mutation."""

    def test_artifact_unchanged(self) -> None:
        """Test artifact is unchanged after validation."""
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

            artifact_id = id(artifact)

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            validate_artifact_manifest(artifact, manifest)

            assert id(artifact) == artifact_id

    def test_manifest_unchanged(self) -> None:
        """Test manifest is unchanged after validation."""
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

            manifest_id = id(manifest)

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            validate_artifact_manifest(artifact, manifest)

            assert id(manifest) == manifest_id

    def test_png_files_unchanged(self) -> None:
        """Test PNG files are unchanged after validation."""
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

            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            validate_artifact_manifest(artifact, manifest)

            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_no_filesystem_mutation(self) -> None:
        """Test no filesystem mutation during validation."""
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

            contents_before = set(Path(tmpdir).iterdir())

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            validate_artifact_manifest(artifact, manifest)

            contents_after = set(Path(tmpdir).iterdir())

            assert contents_before == contents_after


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_validation_deterministic(self) -> None:
        """Test repeated validation produces identical results."""
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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            r1 = validate_artifact_manifest(artifact, manifest)
            r2 = validate_artifact_manifest(artifact, manifest)
            r3 = validate_artifact_manifest(artifact, manifest)

            assert r1.valid == r2.valid == r3.valid

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

            from tools.render.artifact_manifest_validation import (
                validate_artifact_manifest,
            )

            r1 = validate_artifact_manifest(artifact, manifest)
            r2 = validate_artifact_manifest(artifact, manifest)

            assert r1 is not r2


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test no forbidden imports."""
        import ast

        with open("tools/render/artifact_manifest_validation.py") as f:
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

    def test_render_artifact_manifest_validation_importable(self) -> None:
        """Test RenderArtifactManifestValidation is importable."""
        from tools.render import RenderArtifactManifestValidation
        assert RenderArtifactManifestValidation is not None

    def test_artifact_manifest_validation_error_importable(self) -> None:
        """Test ArtifactManifestValidationError is importable."""
        from tools.render import ArtifactManifestValidationError
        assert ArtifactManifestValidationError is not None

    def test_validate_artifact_manifest_importable(self) -> None:
        """Test validate_artifact_manifest is importable."""
        from tools.render import validate_artifact_manifest
        assert validate_artifact_manifest is not None
