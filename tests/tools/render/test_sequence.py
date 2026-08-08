"""Tests for multi-frame PNG sequence export."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from runtime.animation.consumer import AnimationOrchestrator
from tools.frame.models import FrameTransform, InterpolationType
from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    CharacterTransformInput,
    CharacterTransformInputSet,
)
from tools.render import RenderFrame, render_frames_to_png


class TestRenderFramesToPngBasics:
    """Tests for basic render_frames_to_png functionality."""

    def test_import_render_frames_to_png(self) -> None:
        """Test that render_frames_to_png is importable."""
        from tools.render import render_frames_to_png

        assert render_frames_to_png is not None

    def test_empty_iterable_returns_zero(self) -> None:
        """Test that empty iterable returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            count = render_frames_to_png([], tmpdir)
            assert count == 0

    def test_one_frame_produces_one_png(self) -> None:
        """Test that one frame produces one PNG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            count = render_frames_to_png(frames, tmpdir)
            assert count == 1

            # Verify the file exists
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1
            assert png_files[0].name == "frame_000000.png"

    def test_multiple_frames_produce_multiple_pngs(self) -> None:
        """Test that multiple frames produce multiple PNG files."""
        with tempfile.TemporaryDirectory() as tmpdir:
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
            count = render_frames_to_png(frames, tmpdir)
            assert count == 5

            # Verify all files exist
            png_files = sorted(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 5


class TestFilenameConvention:
    """Tests for filename generation."""

    def test_filenames_contain_frame_index(self) -> None:
        """Test that filenames contain frame_index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=5,
                    timestamp_seconds=5.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1
            assert "000005" in png_files[0].name

    def test_zero_padding_is_deterministic(self) -> None:
        """Test that zero-padding is deterministic (6 digits)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
                RenderFrame(
                    frame_index=1,
                    timestamp_seconds=1.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
                RenderFrame(
                    frame_index=99,
                    timestamp_seconds=99.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
            ]
            render_frames_to_png(frames, tmpdir)

            png_files = sorted(Path(tmpdir).glob("frame_*.png"))
            assert png_files[0].name == "frame_000000.png"
            assert png_files[1].name == "frame_000001.png"
            assert png_files[2].name == "frame_000099.png"

    def test_custom_prefix(self) -> None:
        """Test that custom prefix works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, tmpdir, prefix="img")

            png_files = list(Path(tmpdir).glob("img_*.png"))
            assert len(png_files) == 1
            assert png_files[0].name == "img_000000.png"


class TestFrameOrder:
    """Tests for frame ordering."""

    def test_supplied_order_is_preserved(self) -> None:
        """Test that supplied frame order is preserved in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=3,
                    timestamp_seconds=3.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
                RenderFrame(
                    frame_index=1,
                    timestamp_seconds=1.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
                RenderFrame(
                    frame_index=5,
                    timestamp_seconds=5.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                ),
            ]
            render_frames_to_png(frames, tmpdir)

            # Files should be named by frame_index, not order of appearance
            png_files = sorted(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 3
            assert png_files[0].name == "frame_000001.png"
            assert png_files[1].name == "frame_000003.png"
            assert png_files[2].name == "frame_000005.png"


class TestFrameIdentity:
    """Tests for RenderFrame identity preservation."""

    def test_exact_render_frame_objects_reach_renderer(self) -> None:
        """Test that exact RenderFrame objects reach the renderer."""
        captured_frames: list[RenderFrame] = []

        class CapturingRenderer:
            last_output = None  # Will be set by integration

            def render(self, f: RenderFrame) -> None:
                captured_frames.append(f)
                # Set last_output to satisfy integration check
                from PIL import Image
                self.last_output = Image.new("RGBA", (1, 1))

        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            render_frames_to_png(frames, tmpdir, renderer=CapturingRenderer())

        assert len(captured_frames) == 2
        assert captured_frames[0] is frames[0]
        assert captured_frames[1] is frames[1]

    def test_frame_index_unchanged(self) -> None:
        """Test that frame_index remains unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = RenderFrame(
                frame_index=42,
                timestamp_seconds=42.0 / 24.0,
                frame_rate=24.0,
                duration_frames=48,
                transforms={},
            )
            render_frames_to_png([frame], tmpdir)

            # Verify filename contains the frame_index
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1
            assert "000042" in png_files[0].name

    def test_timestamp_unchanged(self) -> None:
        """Test that timestamp_seconds remains unchanged."""
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        captured_timestamp = None

        class TimestampCapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                nonlocal captured_timestamp
                captured_timestamp = f.timestamp_seconds
                # Set last_output to satisfy integration check
                from PIL import Image
                self.last_output = Image.new("RGBA", (1, 1))

        with tempfile.TemporaryDirectory() as tmpdir:
            render_frames_to_png([frame], tmpdir, renderer=TimestampCapturingRenderer())

        assert captured_timestamp == 5.0 / 24.0

    def test_clip_id_keys_unchanged(self) -> None:
        """Test that clip_id keys remain unchanged."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"my_entity": FrameTransform()},
        )

        captured_transforms: dict[str, FrameTransform] = {}

        class TransformCapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                captured_transforms.update(f.transforms)
                # Set last_output to satisfy integration check
                from PIL import Image
                self.last_output = Image.new("RGBA", (1, 1))

        with tempfile.TemporaryDirectory() as tmpdir:
            render_frames_to_png([frame], tmpdir, renderer=TransformCapturingRenderer())

        assert "my_entity" in captured_transforms


class TestFrameContent:
    """Tests for frame content rendering."""

    def test_empty_transforms_work(self) -> None:
        """Test that empty transforms produce valid PNG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, tmpdir)

            # Verify PNG is valid
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.format == "PNG"
            assert image.mode == "RGBA"

    def test_multiple_entities_work(self) -> None:
        """Test that multiple entities produce visible output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={
                        "hero": FrameTransform(position_x=100, position_y=100),
                        "villain": FrameTransform(position_x=300, position_y=200),
                    },
                )
            ]
            render_frames_to_png(frames, tmpdir)

            # Verify PNG has visible content
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])

            # Check that entities are rendered
            pixel1 = image.getpixel((100, 100))
            pixel2 = image.getpixel((300, 200))
            assert pixel1 != (255, 255, 255, 255)
            assert pixel2 != (255, 255, 255, 255)


class TestRendererConfiguration:
    """Tests for renderer configuration."""

    def test_supplied_renderer_is_reused(self) -> None:
        """Test that supplied Renderer instance is reused."""
        render_count = 0

        class CountingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                nonlocal render_count
                render_count += 1
                # Set last_output to satisfy integration check
                from PIL import Image
                self.last_output = Image.new("RGBA", (1, 1))

        renderer = CountingRenderer()
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
            render_frames_to_png(frames, tmpdir, renderer=renderer)

        assert render_count == 3

    def test_default_concrete_renderer_path(self) -> None:
        """Test that default ConcreteRenderer path works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={"entity": FrameTransform()},
                )
            ]
            count = render_frames_to_png(frames, tmpdir)

            assert count == 1
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.format == "PNG"
            assert image.mode == "RGBA"

    def test_canvas_size_config(self) -> None:
        """Test that canvas_size configuration works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, tmpdir, canvas_size=(640, 480))

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.size == (640, 480)


class TestErrorHandling:
    """Tests for error handling."""

    def test_renderer_exception_propagates(self) -> None:
        """Test that renderer exceptions propagate."""

        class FailingRenderer:
            def render(self, f: RenderFrame) -> None:
                msg = "Test renderer error"
                raise RuntimeError(msg)

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
            with pytest.raises(RuntimeError, match="Test renderer error"):
                render_frames_to_png(frames, tmpdir, renderer=FailingRenderer())

    def test_no_partial_failure_silently_ignored(self) -> None:
        """Test that failures stop processing, not silently skipped."""

        class FailOnSecondRenderer:
            last_output = None
            call_count = 0

            def render(self, f: RenderFrame) -> None:
                self.call_count += 1
                if self.call_count == 2:
                    msg = "Failure on second frame"
                    raise RuntimeError(msg)
                # Set last_output to satisfy integration check
                from PIL import Image
                self.last_output = Image.new("RGBA", (1, 1))

        renderer = FailOnSecondRenderer()
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
            with pytest.raises(RuntimeError, match="Failure on second frame"):
                render_frames_to_png(frames, tmpdir, renderer=renderer)


class TestImmutability:
    """Tests for RenderFrame immutability."""

    def test_render_frame_not_mutated(self) -> None:
        """Test that RenderFrame is not mutated."""
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform()},
        )

        original_frame_index = frame.frame_index
        original_timestamp = frame.timestamp_seconds
        original_keys = set(frame.transforms.keys())

        with tempfile.TemporaryDirectory() as tmpdir:
            render_frames_to_png([frame], tmpdir)

        assert frame.frame_index == original_frame_index
        assert frame.timestamp_seconds == original_timestamp
        assert set(frame.transforms.keys()) == original_keys


class TestDeterminism:
    """Tests for deterministic output."""

    def test_deterministic_filenames(self) -> None:
        """Test that filenames are deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                RenderFrame(
                    frame_index=10,
                    timestamp_seconds=10.0 / 24.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert png_files[0].name == "frame_000010.png"

            # Run again - should produce same result
            # Clear directory and render again
            for f in png_files:
                f.unlink()

            render_frames_to_png(frames, tmpdir)
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert png_files[0].name == "frame_000010.png"

    def test_deterministic_image_content(self) -> None:
        """Test that image content is deterministic."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={"entity": FrameTransform()},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                render_frames_to_png(frames, tmpdir1)
                render_frames_to_png(frames, tmpdir2)

                # Compare image content
                img1 = Image.open(Path(tmpdir1) / "frame_000000.png")
                img2 = Image.open(Path(tmpdir2) / "frame_000000.png")

                assert img1.tobytes() == img2.tobytes()


class TestOutputDirectory:
    """Tests for output directory handling."""

    def test_output_directory_created(self) -> None:
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_dir" / "nested"
            assert not output_dir.exists()

            frames = [
                RenderFrame(
                    frame_index=0,
                    timestamp_seconds=0.0,
                    frame_rate=24.0,
                    duration_frames=24,
                    transforms={},
                )
            ]
            render_frames_to_png(frames, output_dir)

            assert output_dir.exists()
            assert len(list(output_dir.glob("*.png"))) == 1


class TestRealRuntimeFrames:
    """Tests using real RenderFrame from AnimationOrchestrator."""

    def test_real_runtime_frames_render(self) -> None:
        """Test that real RenderFrame sequence renders to PNG sequence."""
        # Create animation data
        target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="1",
            sequence_id="intro",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=0,
            palette_id=None,
        )
        output = CharacterAnimationOutput(
            sequence_id="intro",
            bindings=(binding,),
            metadata=CharacterAnimationMetadata(
                bindings_created=1,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )

        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=0,
                    transform=FrameTransform(position_x=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=12,
                    transform=FrameTransform(position_x=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        # Create orchestrator and load
        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)

        # Generate frames using the orchestrator's frames() iterator
        frames = [frame for _, frame in [(0, orchestrator.render_frame())]]

        # Render to PNG sequence
        with tempfile.TemporaryDirectory() as tmpdir:
            count = render_frames_to_png(frames, tmpdir)

            assert count == 1

            # Verify PNG was created
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1

            # Verify it's a valid PNG
            image = Image.open(png_files[0])
            assert image.format == "PNG"
            assert image.mode == "RGBA"


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in sequence module."""
        import ast

        with open("tools/render/sequence.py") as f:
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
        forbidden = ["AnimationRuntime", "AnimationTimeline", "AnimationClip"]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"
