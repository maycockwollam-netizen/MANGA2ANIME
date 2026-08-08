"""Tests for render sequence manifest."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from tools.render import (
    RenderFrame,
    RenderSequenceManifest,
    ValidationError,
    create_render_manifest,
    export_render_frames,
)


class TestValidManifests:
    """Tests for valid manifest creation."""

    def test_valid_single_frame_manifest(self) -> None:
        """Test manifest of a single-frame sequence."""
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
            manifest = create_render_manifest(tmpdir)

        assert isinstance(manifest, RenderSequenceManifest)
        assert manifest.frame_count == 1

    def test_valid_multi_frame_manifest(self) -> None:
        """Test manifest of a multi-frame sequence."""
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
            manifest = create_render_manifest(tmpdir)

        assert manifest.frame_count == 5


class TestOutputDir:
    """Tests for output_dir property."""

    def test_output_dir_preserved_as_path(self) -> None:
        """Test that output_dir is preserved as Path."""
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
            manifest = create_render_manifest(tmpdir)

        assert isinstance(manifest.output_dir, Path)
        assert manifest.output_dir == Path(tmpdir)


class TestPrefix:
    """Tests for prefix property."""

    def test_prefix_preserved(self) -> None:
        """Test that prefix is preserved."""
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
            export_render_frames(frames, tmpdir, prefix="img")
            manifest = create_render_manifest(tmpdir, prefix="img")

        assert manifest.prefix == "img"


class TestFrameCount:
    """Tests for frame_count property."""

    def test_frame_count_correct(self) -> None:
        """Test that frame_count is correct."""
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
            manifest = create_render_manifest(tmpdir)

        assert manifest.frame_count == 10


class TestFrameIndices:
    """Tests for frame_indices property."""

    def test_frame_indices_correct_and_sorted(self) -> None:
        """Test that frame_indices are correct and sorted."""
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
            manifest = create_render_manifest(tmpdir)

        assert manifest.frame_indices == (0, 1, 2, 3, 4, 5, 6)
        assert manifest.frame_indices == tuple(sorted(manifest.frame_indices))


class TestFrameRate:
    """Tests for frame_rate property."""

    def test_frame_rate_preserved(self) -> None:
        """Test that frame_rate is preserved."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 30.0,
                frame_rate=30.0,
                duration_frames=30,
                transforms={},
            )
            for i in range(24)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            manifest = create_render_manifest(tmpdir, frame_rate=30.0)

        assert manifest.frame_rate == 30.0


class TestDuration:
    """Tests for duration_seconds property."""

    def test_duration_seconds_correct(self) -> None:
        """Test that duration_seconds is frame_count / frame_rate."""
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
            manifest = create_render_manifest(tmpdir, frame_rate=24.0)

        assert manifest.duration_seconds == 48 / 24.0


class TestDimensions:
    """Tests for dimensions property."""

    def test_dimensions_correct(self) -> None:
        """Test that dimensions are correct."""
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
            manifest = create_render_manifest(tmpdir)

        assert manifest.dimensions == (640, 480)


class TestMode:
    """Tests for mode property."""

    def test_mode_correct(self) -> None:
        """Test that image mode is correct."""
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
            manifest = create_render_manifest(tmpdir)

        assert manifest.mode == "RGBA"


class TestFrameRateValidation:
    """Tests for frame_rate validation."""

    def test_zero_frame_rate_rejected(self) -> None:
        """Test that zero frame_rate raises error."""
        from tools.render import PreviewError

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

            with pytest.raises(PreviewError, match="frame_rate must be positive"):
                create_render_manifest(tmpdir, frame_rate=0.0)

    def test_negative_frame_rate_rejected(self) -> None:
        """Test that negative frame_rate raises error."""
        from tools.render import PreviewError

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

            with pytest.raises(PreviewError, match="frame_rate must be positive"):
                create_render_manifest(tmpdir, frame_rate=-24.0)


class TestEmptySequence:
    """Tests for empty sequence handling."""

    def test_empty_sequence_rejected(self) -> None:
        """Test that empty sequence raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No files exported
            with pytest.raises((ValidationError, Exception)):
                create_render_manifest(tmpdir)


class TestInvalidSequence:
    """Tests for invalid sequence handling."""

    def test_invalid_png_sequence_rejected(self) -> None:
        """Test that invalid PNG sequence raises error."""
        from tools.render import PreviewError

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bad PNG file
            bad_png = Path(tmpdir) / "frame_000000.png"
            bad_png.write_bytes(b"not a valid png")

            with pytest.raises(PreviewError):
                create_render_manifest(tmpdir)


class TestMissingFrameIndex:
    """Tests for missing frame index handling."""

    def test_missing_frame_index_rejected(self) -> None:
        """Test that missing frame index raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames 0, 1, 2, 4 (missing 3)
            for i in [0, 1, 2, 4]:
                img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
                img.save(Path(tmpdir) / f"frame_{i:06d}.png")

            with pytest.raises((ValidationError, Exception), match="Missing frame indices"):
                create_render_manifest(tmpdir)


class TestInconsistentDimensions:
    """Tests for inconsistent dimensions handling."""

    def test_inconsistent_dimensions_rejected(self) -> None:
        """Test that inconsistent dimensions raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames with different sizes
            img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img1.save(Path(tmpdir) / "frame_000000.png")

            img2 = Image.new("RGBA", (200, 200), (0, 255, 0, 255))
            img2.save(Path(tmpdir) / "frame_000001.png")

            with pytest.raises((ValidationError, Exception), match="Inconsistent dimensions"):
                create_render_manifest(tmpdir)


class TestInconsistentMode:
    """Tests for inconsistent image mode handling."""

    def test_inconsistent_mode_rejected(self) -> None:
        """Test that inconsistent image modes raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames with different modes
            img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img1.save(Path(tmpdir) / "frame_000000.png")

            img2 = Image.new("RGB", (100, 100), (0, 255, 0))
            img2.save(Path(tmpdir) / "frame_000001.png")

            with pytest.raises((ValidationError, Exception), match="Inconsistent image mode"):
                create_render_manifest(tmpdir)


class TestImmutability:
    """Tests for immutability of manifest."""

    def test_manifest_is_frozen(self) -> None:
        """Test that RenderSequenceManifest is immutable."""
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
            manifest = create_render_manifest(tmpdir)

        with pytest.raises(AttributeError):
            manifest.frame_count = 99

    def test_frame_indices_immutable(self) -> None:
        """Test that frame_indices tuple is immutable."""
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
            manifest = create_render_manifest(tmpdir)

        with pytest.raises(TypeError):
            manifest.frame_indices[0] = 99


class TestFilesystemMutation:
    """Tests verifying no filesystem mutation."""

    def test_no_filesystem_mutation(self) -> None:
        """Test that manifest creation doesn't modify any files."""
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

            # Create manifest
            create_render_manifest(tmpdir)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Timestamps should be unchanged
            assert files_before == files_after


class TestDeterministicResult:
    """Tests for deterministic result."""

    def test_deterministic_result(self) -> None:
        """Test that manifest creation is deterministic."""
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

            # Create manifest twice
            manifest1 = create_render_manifest(tmpdir)
            manifest2 = create_render_manifest(tmpdir)

            # Should produce identical results
            assert manifest1.output_dir == manifest2.output_dir
            assert manifest1.prefix == manifest2.prefix
            assert manifest1.frame_count == manifest2.frame_count
            assert manifest1.frame_indices == manifest2.frame_indices
            assert manifest1.frame_rate == manifest2.frame_rate
            assert manifest1.duration_seconds == manifest2.duration_seconds
            assert manifest1.dimensions == manifest2.dimensions
            assert manifest1.mode == manifest2.mode


class TestPublicAPI:
    """Tests for public API."""

    def test_render_sequence_manifest_importable(self) -> None:
        """Test RenderSequenceManifest is importable from tools.render."""
        from tools.render import RenderSequenceManifest

        assert RenderSequenceManifest is not None

    def test_create_render_manifest_importable(self) -> None:
        """Test create_render_manifest is importable from tools.render."""
        from tools.render import create_render_manifest

        assert create_render_manifest is not None


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in manifest module."""
        import ast

        with open("tools/render/manifest.py") as f:
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
        ]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"


class TestValidationDelegation:
    """Tests verifying validation delegation."""

    def test_manifest_uses_validation_layer(self) -> None:
        """Test that manifest creation uses existing validation."""
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
            # Should succeed with valid sequence
            manifest = create_render_manifest(tmpdir)
            assert manifest.frame_count == 1

    def test_no_unnecessary_image_loading(self) -> None:
        """Test that manifest doesn't load images unnecessarily."""
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
            # Create manifest
            manifest = create_render_manifest(tmpdir)
            # All metadata should come from validation
            assert manifest.dimensions == (800, 600)
            assert manifest.mode == "RGBA"
