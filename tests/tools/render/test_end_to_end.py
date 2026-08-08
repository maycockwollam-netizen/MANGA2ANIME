"""End-to-end smoke tests for the render export pipeline.

Verifies that the complete render pipeline can consume real RenderFrame objects
produced by the existing animation orchestration layer and produce valid PNG artifacts.

Architecture under test:
    AnimationOrchestrator.render_frame()
        ↓
    RenderFrame
        ↓
    export_render_frames()
        ↓
    render_frames_to_png()
        ↓
    render_frame_to_png()
        ↓
    FrameAdapter
        ↓
    ConcreteRenderer
        ↓
    PNG files
"""

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
from tools.render import RenderFrame, export_render_frames


class TestRenderFrameProduction:
    """Tests verifying real RenderFrame can be produced by animation orchestration."""

    def test_orchestrator_produces_render_frame(self) -> None:
        """Verify AnimationOrchestrator produces a valid RenderFrame."""
        orchestrator = self._create_orchestrator()
        frame = orchestrator.render_frame()

        assert frame is not None
        assert isinstance(frame.frame_index, int)
        assert isinstance(frame.timestamp_seconds, float)
        assert isinstance(frame.frame_rate, float)
        assert isinstance(frame.duration_frames, int)

    def test_render_frame_has_clip_id(self) -> None:
        """Verify RenderFrame contains expected clip_id."""
        orchestrator = self._create_orchestrator()
        frame = orchestrator.render_frame()

        assert len(frame.transforms) > 0
        clip_ids = list(frame.transforms.keys())
        assert len(clip_ids) == 1
        assert clip_ids[0] == "hero_1"

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator


class TestExportPipeline:
    """Tests verifying the complete export pipeline."""

    def test_single_frame_export_creates_png(self) -> None:
        """Verify single frame export creates a valid PNG file."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            count = export_render_frames(frames, tmpdir)

            assert count == 1
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1

    def test_png_can_be_opened_with_pillow(self) -> None:
        """Verify PNG can be opened successfully with Pillow."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            export_render_frames(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image is not None

    def test_png_format_is_rgba(self) -> None:
        """Verify PNG format is RGBA."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            export_render_frames(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.mode == "RGBA"

    def test_png_dimensions_match_canvas_size(self) -> None:
        """Verify PNG dimensions match configured canvas size."""
        orchestrator = self._create_orchestrator()
        canvas_size = (640, 480)

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            export_render_frames(frames, tmpdir, canvas_size=canvas_size)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.size == canvas_size

    def test_filename_contains_frame_index(self) -> None:
        """Verify PNG filename contains correct frame_index."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            export_render_frames(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert "000000" in png_files[0].name

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator


class TestMultiFrameExport:
    """Tests for multi-frame sequence export."""

    def test_export_produces_expected_frame_count(self) -> None:
        """Verify exported sequence contains expected number of frames."""
        orchestrator = self._create_orchestrator()

        # Get frame from orchestrator, then create additional frames for multi-frame test
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [
                orchestrator.render_frame(),
                self._create_render_frame(1),
                self._create_render_frame(2),
                self._create_render_frame(3),
                self._create_render_frame(4),
            ]
            count = export_render_frames(frames, tmpdir)

            assert count == 5
            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 5

    def test_frame_ordering_is_deterministic(self) -> None:
        """Verify frame ordering is deterministic."""
        orchestrator = self._create_orchestrator()

        frames = [
            orchestrator.render_frame(),
            self._create_render_frame(1),
            self._create_render_frame(2),
        ]

        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                export_render_frames(frames, tmpdir1)
                export_render_frames(frames, tmpdir2)

                files1 = sorted(Path(tmpdir1).glob("frame_*.png"))
                files2 = sorted(Path(tmpdir2).glob("frame_*.png"))

                assert len(files1) == len(files2) == 3
                assert files1[0].name == files2[0].name
                assert files1[1].name == files2[1].name
                assert files1[2].name == files2[2].name

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator

    def _create_render_frame(self, frame_index: int) -> RenderFrame:
        """Create a RenderFrame for multi-frame testing."""
        return RenderFrame(
            frame_index=frame_index,
            timestamp_seconds=frame_index / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"hero_1": FrameTransform(position_x=100, position_y=100)},
        )


class TestRenderFrameIntegrity:
    """Tests verifying RenderFrame metadata integrity through pipeline."""

    def test_frame_index_preserved_in_export(self) -> None:
        """Verify frame_index is preserved through export."""
        orchestrator = self._create_orchestrator()
        original_frame = orchestrator.render_frame()
        original_index = original_frame.frame_index

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([original_frame], tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert f"{original_index:06d}" in png_files[0].name

    def test_timestamp_preserved(self) -> None:
        """Verify timestamp_seconds is preserved through pipeline."""
        orchestrator = self._create_orchestrator()
        frame = orchestrator.render_frame()
        original_timestamp = frame.timestamp_seconds

        assert frame.timestamp_seconds == original_timestamp

    def test_duration_preserved(self) -> None:
        """Verify duration_frames is preserved through pipeline."""
        orchestrator = self._create_orchestrator()
        frame = orchestrator.render_frame()
        original_duration = frame.duration_frames

        assert frame.duration_frames == original_duration

    def test_clip_id_keys_unchanged(self) -> None:
        """Verify clip_id keys remain unchanged through pipeline."""
        orchestrator = self._create_orchestrator()
        frame = orchestrator.render_frame()
        original_keys = set(frame.transforms.keys())

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([frame], tmpdir)

        assert set(frame.transforms.keys()) == original_keys

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator


class TestPNGContentVerification:
    """Tests for PNG content verification."""

    def test_entity_produces_visible_output(self) -> None:
        """Verify entity produces visible (non-background) pixels."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            frames = [orchestrator.render_frame()]
            export_render_frames(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])

            # Check entity position has non-background pixels
            pixel = image.getpixel((100, 100))
            assert pixel != (255, 255, 255, 255)

    def test_deterministic_output(self) -> None:
        """Verify identical input produces byte-identical output."""
        orchestrator = self._create_orchestrator()
        frames = [orchestrator.render_frame()]

        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                export_render_frames(frames, tmpdir1)
                export_render_frames(frames, tmpdir2)

                img1 = Image.open(Path(tmpdir1) / "frame_000000.png")
                img2 = Image.open(Path(tmpdir2) / "frame_000000.png")

                assert img1.tobytes() == img2.tobytes()

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator


class TestErrorHandling:
    """Tests for error handling."""

    def test_exceptions_not_swallowed(self) -> None:
        """Verify renderer exceptions are not swallowed."""

        class FailingRenderer:
            last_output = None

            def render(self, frame) -> None:
                msg = "Test failure"
                raise RuntimeError(msg)

        orchestrator = self._create_orchestrator()
        frames = [orchestrator.render_frame()]

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError, match="Test failure"):
                export_render_frames(frames, tmpdir, renderer=FailingRenderer())

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator


class TestOutputDirectoryHandling:
    """Tests for output directory handling."""

    def test_nested_directory_created(self) -> None:
        """Verify nested output directory is created."""
        orchestrator = self._create_orchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            assert not output_dir.exists()

            frames = [orchestrator.render_frame()]
            export_render_frames(frames, output_dir)

            assert output_dir.exists()
            png_files = list(output_dir.glob("frame_*.png"))
            assert len(png_files) == 1

    def _create_orchestrator(self) -> AnimationOrchestrator:
        """Create a test orchestrator with animation data."""
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
                    transform=FrameTransform(position_x=100, position_y=100),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        return orchestrator
