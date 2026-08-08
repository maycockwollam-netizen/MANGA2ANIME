"""Tests for render sequence validation."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from tools.render import (
    RenderFrame,
    RenderSequenceValidation,
    ValidationError,
    export_render_frames,
    validate_render_sequence,
)


class TestValidSequences:
    """Tests for valid sequence validation."""

    def test_valid_single_frame_sequence(self) -> None:
        """Test validation of a valid single-frame sequence."""
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
            result = validate_render_sequence(tmpdir)

        assert isinstance(result, RenderSequenceValidation)
        assert result.frame_count == 1
        assert result.frame_indices == (0,)
        assert result.dimensions == (800, 600)
        assert result.mode == "RGBA"

    def test_valid_multi_frame_sequence(self) -> None:
        """Test validation of a valid multi-frame sequence."""
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
            result = validate_render_sequence(tmpdir)

        assert result.frame_count == 5
        assert result.frame_indices == (0, 1, 2, 3, 4)

    def test_custom_prefix(self) -> None:
        """Test validation with custom prefix."""
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
            result = validate_render_sequence(tmpdir, prefix="img")

        assert result.frame_count == 1
        assert result.frame_indices == (0,)

    def test_frame_indices_returned_in_sorted_order(self) -> None:
        """Test that frame indices are returned in sorted order."""
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
            result = validate_render_sequence(tmpdir)

        assert result.frame_indices == tuple(range(10))


class TestEmptyDirectory:
    """Tests for empty directory handling."""

    def test_empty_directory_raises_validation_error(self) -> None:
        """Test that empty directory raises ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="Empty sequence"):
                validate_render_sequence(tmpdir)

    def test_no_png_files_raises_validation_error(self) -> None:
        """Test that directory with no PNG files raises ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-PNG file
            (Path(tmpdir) / "readme.txt").write_text("hello")

            with pytest.raises(ValidationError, match="Empty sequence"):
                validate_render_sequence(tmpdir)


class TestMissingFrames:
    """Tests for missing frame detection."""

    def test_missing_frame_index_raises_error(self) -> None:
        """Test that missing frame index raises ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames 0, 1, 2, 4 (missing 3)
            for i in [0, 1, 2, 4]:
                img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
                img.save(Path(tmpdir) / f"frame_{i:06d}.png")

            with pytest.raises(ValidationError, match="Missing frame indices"):
                validate_render_sequence(tmpdir)


class TestDuplicateFrames:
    """Tests for duplicate frame detection."""

    def test_no_duplicates_in_valid_sequence(self) -> None:
        """Test that valid sequences have no duplicates."""
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
            result = validate_render_sequence(tmpdir)

        # Verify no duplicates in the result
        assert len(result.frame_indices) == len(set(result.frame_indices))


class TestUnexpectedFiles:
    """Tests for unexpected file handling."""

    def test_unexpected_png_filename_raises_error(self) -> None:
        """Test that unexpected PNG filenames raise ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid frame
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img.save(Path(tmpdir) / "frame_000000.png")

            # Create unexpected PNG with bad naming
            img.save(Path(tmpdir) / "frame_abc.png")

            with pytest.raises(ValidationError, match="Unexpected PNG files"):
                validate_render_sequence(tmpdir)


class TestImageValidity:
    """Tests for image validity checking."""

    def test_invalid_unreadable_png_raises_error(self) -> None:
        """Test that unreadable PNG raises ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that looks like PNG but isn't valid
            bad_png = Path(tmpdir) / "frame_000000.png"
            bad_png.write_bytes(b"not a valid png")

            with pytest.raises(ValidationError, match="Unreadable PNG file"):
                validate_render_sequence(tmpdir)


class TestConsistentProperties:
    """Tests for consistent image properties."""

    def test_inconsistent_dimensions_raises_error(self) -> None:
        """Test that inconsistent dimensions raise ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames with different sizes
            img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img1.save(Path(tmpdir) / "frame_000000.png")

            img2 = Image.new("RGBA", (200, 200), (0, 255, 0, 255))
            img2.save(Path(tmpdir) / "frame_000001.png")

            with pytest.raises(ValidationError, match="Inconsistent dimensions"):
                validate_render_sequence(tmpdir)

    def test_inconsistent_image_modes_raises_error(self) -> None:
        """Test that inconsistent image modes raise ValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create frames with different modes
            img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img1.save(Path(tmpdir) / "frame_000000.png")

            img2 = Image.new("RGB", (100, 100), (0, 255, 0))
            img2.save(Path(tmpdir) / "frame_000001.png")

            with pytest.raises(ValidationError, match="Inconsistent image mode"):
                validate_render_sequence(tmpdir)


class TestExpectedFrameCount:
    """Tests for expected frame count validation."""

    def test_expected_count_mismatch_raises_error(self) -> None:
        """Test that expected frame count mismatch raises ValidationError."""
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

            with pytest.raises(ValidationError, match="Frame count mismatch"):
                validate_render_sequence(tmpdir, expected_frame_count=10)

    def test_expected_count_matches(self) -> None:
        """Test that matching expected count passes."""
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
            result = validate_render_sequence(tmpdir, expected_frame_count=5)

        assert result.frame_count == 5


class TestImmutability:
    """Tests for immutability of validation result."""

    def test_validation_result_is_frozen(self) -> None:
        """Test that RenderSequenceValidation is immutable."""
        result = RenderSequenceValidation(
            frame_count=1,
            frame_indices=(0,),
            dimensions=(100, 100),
            mode="RGBA",
        )

        with pytest.raises(AttributeError):
            result.frame_count = 2


class TestFilesystemMutation:
    """Tests verifying no filesystem mutation."""

    def test_no_filesystem_mutation(self) -> None:
        """Test that validation doesn't modify any files."""
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

            # Run validation
            validate_render_sequence(tmpdir)

            # Get file timestamps after
            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            # Timestamps should be unchanged
            assert files_before == files_after


class TestPublicAPI:
    """Tests for public API."""

    def test_render_sequence_validation_importable(self) -> None:
        """Test RenderSequenceValidation is importable from tools.render."""
        from tools.render import RenderSequenceValidation

        assert RenderSequenceValidation is not None

    def test_validation_error_importable(self) -> None:
        """Test ValidationError is importable from tools.render."""
        from tools.render import ValidationError

        assert ValidationError is not None

    def test_validate_render_sequence_importable(self) -> None:
        """Test validate_render_sequence is importable from tools.render."""
        from tools.render import validate_render_sequence

        assert validate_render_sequence is not None


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in validation module."""
        import ast

        with open("tools/render/validation.py") as f:
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
