"""Tests for render sequence preview."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from tools.render import (
    PreviewError,
    RenderFrame,
    RenderPreview,
    ValidationError,
    create_render_preview,
    export_render_frames,
)


class TestValidPreviews:
    """Tests for valid preview creation."""

    def test_valid_single_frame_preview(self) -> None:
        """Test preview of a single-frame sequence."""
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
            preview = create_render_preview(tmpdir)

        assert isinstance(preview, RenderPreview)
        assert preview.frame_count == 1

    def test_valid_multi_frame_preview(self) -> None:
        """Test preview of a multi-frame sequence."""
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
            preview = create_render_preview(tmpdir)

        assert preview.frame_count == 5


class TestFrameCount:
    """Tests for frame_count property."""

    def test_frame_count_matches_sequence(self) -> None:
        """Test that frame_count matches the actual sequence length."""
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
            preview = create_render_preview(tmpdir)

        assert preview.frame_count == 10


class TestFrameIndices:
    """Tests for frame_indices property."""

    def test_frame_indices_preserved(self) -> None:
        """Test that frame_indices are preserved correctly."""
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
            preview = create_render_preview(tmpdir)

        assert preview.frame_indices == (0, 1, 2, 3, 4, 5, 6)


class TestFramePaths:
    """Tests for frame_paths property."""

    def test_frame_paths_in_correct_order(self) -> None:
        """Test that frame_paths are in frame index order."""
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
            preview = create_render_preview(tmpdir)

        assert len(preview.frame_paths) == 3
        assert preview.frame_paths[0].name == "frame_000000.png"
        assert preview.frame_paths[1].name == "frame_000001.png"
        assert preview.frame_paths[2].name == "frame_000002.png"


class TestCustomPrefix:
    """Tests for custom prefix handling."""

    def test_custom_prefix(self) -> None:
        """Test preview with custom prefix."""
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
            preview = create_render_preview(tmpdir, prefix="img")

        assert preview.frame_paths[0].name == "img_000000.png"


class TestFrameRate:
    """Tests for frame_rate parameter."""

    def test_custom_frame_rate(self) -> None:
        """Test preview with custom frame rate."""
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
            preview = create_render_preview(tmpdir, frame_rate=30.0)

        assert preview.frame_rate == 30.0
        assert preview.duration_seconds == 24 / 30.0


class TestDuration:
    """Tests for duration_seconds property."""

    def test_duration_seconds(self) -> None:
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
            preview = create_render_preview(tmpdir, frame_rate=24.0)

        assert preview.duration_seconds == 48 / 24.0


class TestFrameRateValidation:
    """Tests for frame_rate validation."""

    def test_zero_frame_rate_rejected(self) -> None:
        """Test that zero frame_rate raises PreviewError."""
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
                create_render_preview(tmpdir, frame_rate=0.0)

    def test_negative_frame_rate_rejected(self) -> None:
        """Test that negative frame_rate raises PreviewError."""
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
                create_render_preview(tmpdir, frame_rate=-24.0)


class TestFramePath:
    """Tests for frame_path() method."""

    def test_frame_path_returns_correct_file(self) -> None:
        """Test that frame_path returns the correct PNG path."""
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
            preview = create_render_preview(tmpdir)

            path = preview.frame_path(2)
            assert path.name == "frame_000002.png"
            assert path.exists()

    def test_invalid_frame_index_rejected(self) -> None:
        """Test that invalid frame index raises ValueError."""
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
            preview = create_render_preview(tmpdir)

            with pytest.raises(ValueError, match="Frame index 99 not found"):
                preview.frame_path(99)


class TestFrameImage:
    """Tests for frame_image() method."""

    def test_frame_image_loads_correct_png(self) -> None:
        """Test that frame_image loads the correct PNG file."""
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
            preview = create_render_preview(tmpdir)

            img = preview.frame_image(1)
            assert isinstance(img, Image.Image)
            assert img.format == "PNG"

    def test_image_dimensions_preserved(self) -> None:
        """Test that image dimensions are preserved."""
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
            preview = create_render_preview(tmpdir)

            img = preview.frame_image(0)
            assert img.width == 640
            assert img.height == 480

    def test_image_mode_preserved(self) -> None:
        """Test that image mode is preserved."""
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
            preview = create_render_preview(tmpdir)

            img = preview.frame_image(0)
            assert img.mode == "RGBA"


class TestFilesystemMutation:
    """Tests verifying no filesystem mutation."""

    def test_preview_does_not_mutate_files(self) -> None:
        """Test that preview creation doesn't modify any files."""
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

            # Create preview (verifies it doesn't mutate files)
            create_render_preview(tmpdir)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Timestamps should be unchanged
            assert files_before == files_after


class TestNoCaching:
    """Tests verifying no caching behavior."""

    def test_preview_does_not_cache_images(self) -> None:
        """Test that frame_image loads fresh each call."""
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
            preview = create_render_preview(tmpdir)

            # Load image twice
            img1 = preview.frame_image(0)
            img2 = preview.frame_image(0)

            # Both should be separate Image objects
            assert img1 is not img2


class TestValidationDelegation:
    """Tests verifying validation delegation."""

    def test_preview_uses_validation_layer(self) -> None:
        """Test that preview creation uses existing validation."""
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
            preview = create_render_preview(tmpdir)
            assert preview.frame_count == 1


class TestDeterministicOrdering:
    """Tests for deterministic ordering."""

    def test_deterministic_ordering(self) -> None:
        """Test that frame order is deterministic."""
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

            # Create preview twice
            preview1 = create_render_preview(tmpdir)
            preview2 = create_render_preview(tmpdir)

            # Should produce identical ordering
            assert preview1.frame_indices == preview2.frame_indices
            assert preview1.frame_paths == preview2.frame_paths


class TestEmptySequence:
    """Tests for empty sequence handling."""

    def test_empty_sequence_rejected(self) -> None:
        """Test that empty sequence raises PreviewError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No files exported
            with pytest.raises((PreviewError, ValidationError)):
                create_render_preview(tmpdir)


class TestInvalidSequence:
    """Tests for invalid sequence handling."""

    def test_invalid_png_sequence_rejected(self) -> None:
        """Test that invalid PNG sequence raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bad PNG file
            bad_png = Path(tmpdir) / "frame_000000.png"
            bad_png.write_bytes(b"not a valid png")

            with pytest.raises((PreviewError, ValidationError)):
                create_render_preview(tmpdir)


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in preview module."""
        import ast

        with open("tools/render/preview.py") as f:
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


class TestPublicAPI:
    """Tests for public API."""

    def test_render_preview_importable(self) -> None:
        """Test RenderPreview is importable from tools.render."""
        from tools.render import RenderPreview

        assert RenderPreview is not None

    def test_preview_error_importable(self) -> None:
        """Test PreviewError is importable from tools.render."""
        from tools.render import PreviewError

        assert PreviewError is not None

    def test_create_render_preview_importable(self) -> None:
        """Test create_render_preview is importable from tools.render."""
        from tools.render import create_render_preview

        assert create_render_preview is not None


class TestImmutability:
    """Tests for immutability of preview result."""

    def test_preview_is_frozen(self) -> None:
        """Test that RenderPreview is immutable."""
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
            preview = create_render_preview(tmpdir)

        with pytest.raises(AttributeError):
            preview.frame_paths = ()

    def test_frame_paths_immutable(self) -> None:
        """Test that frame_paths tuple is immutable."""
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
            preview = create_render_preview(tmpdir)

        with pytest.raises(TypeError):
            preview.frame_paths[0] = Path("/fake")

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
            preview = create_render_preview(tmpdir)

        with pytest.raises(TypeError):
            preview.frame_indices[0] = 99
