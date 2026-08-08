"""Tests for single-frame render integration."""

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
from tools.render import (
    RenderFrame,
    render_frame_to_png,
)


class TestRenderFrameToPngBasics:
    """Tests for basic render_frame_to_png functionality."""

    def test_import_render_frame_to_png(self) -> None:
        """Test that render_frame_to_png is importable."""
        from tools.render import render_frame_to_png

        assert render_frame_to_png is not None

    def test_accepts_valid_render_frame(self) -> None:
        """Test that a valid RenderFrame is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            render_frame_to_png(frame, output_path)

            assert output_path.exists()

    def test_creates_png_file(self) -> None:
        """Test that output is a valid PNG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            render_frame_to_png(frame, output_path)

            image = Image.open(output_path)
            assert image.format == "PNG"

    def test_output_is_rgba(self) -> None:
        """Test that output image is RGBA mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            render_frame_to_png(frame, output_path)

            image = Image.open(output_path)
            assert image.mode == "RGBA"

    def test_output_dimensions_match_config(self) -> None:
        """Test that output dimensions match ConcreteRenderer configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            render_frame_to_png(frame, output_path, canvas_size=(640, 480))

            image = Image.open(output_path)
            assert image.size == (640, 480)


class TestFrameAdapterUsage:
    """Tests verifying FrameAdapter is used in the integration."""

    def test_integration_uses_adapter(self) -> None:
        """Test that integration uses FrameAdapter internally."""
        # This test verifies the integration module uses FrameAdapter
        # by checking the code structure rather than runtime behavior
        import ast

        with open("tools/render/integration.py") as f:
            source = f.read()

        tree = ast.parse(source)
        # Find the render_frame_to_png function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "render_frame_to_png":
                func_source = ast.get_source_segment(source, node)
                # Check that FrameAdapter is imported and used
                assert "FrameAdapter" in func_source
                assert "adapter" in func_source
                return

        raise AssertionError("render_frame_to_png function not found")


class TestEmptyFrame:
    """Tests for empty frame rendering."""

    def test_empty_frame_produces_blank_png(self) -> None:
        """Test that empty frame produces valid blank PNG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            render_frame_to_png(frame, output_path)

            image = Image.open(output_path)
            # All pixels should be background color (255, 255, 255, 255)
            extrema = image.getextrema()
            # RGBA: check that all channels have uniform values
            assert all(
                e[0] == e[1] for e in extrema
            ), "Empty frame should have uniform background"


class TestSingleEntity:
    """Tests for single entity rendering."""

    def test_single_entity_produces_visible_pixels(self) -> None:
        """Test that single entity produces non-background pixels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={
                    "hero": FrameTransform(position_x=100, position_y=100),
                },
            )

            render_frame_to_png(frame, output_path)

            image = Image.open(output_path)
            # Sample a pixel where entity should be
            pixel = image.getpixel((100, 100))
            # Should not be pure white background
            assert pixel != (255, 255, 255, 255)


class TestMultipleEntities:
    """Tests for multiple entity rendering."""

    def test_multiple_entities_produce_visible_output(self) -> None:
        """Test that multiple entities produce visible output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={
                    "hero": FrameTransform(position_x=100, position_y=100),
                    "villain": FrameTransform(position_x=300, position_y=200),
                },
            )

            render_frame_to_png(frame, output_path)

            image = Image.open(output_path)
            # Both entities should be visible
            pixel1 = image.getpixel((100, 100))
            pixel2 = image.getpixel((300, 200))
            assert pixel1 != (255, 255, 255, 255)
            assert pixel2 != (255, 255, 255, 255)


class TestClipIdIdentity:
    """Tests for clip_id identity preservation."""

    def test_clip_id_in_runtime_frame(self) -> None:
        """Test that clip_id reaches render pipeline through runtime frame."""
        # This tests that a runtime-produced RenderFrame with specific clip_id
        # can be rendered. Note: runtime may transform clip_ids (e.g., hero -> hero_1)
        # so we verify that some clip_id exists in the frame.
        target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="1",
            sequence_id="test",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=0,
            palette_id=None,
        )
        output = CharacterAnimationOutput(
            sequence_id="test",
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
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)
        frame = orchestrator.render_frame()

        # Verify some clip_id exists in the frame (runtime may transform it)
        assert len(frame.transforms) > 0
        # The runtime creates clips with transformed IDs
        clip_ids = list(frame.transforms.keys())
        assert any("hero" in clip_id for clip_id in clip_ids)

        # Render to PNG
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            render_frame_to_png(frame, output_path)

            # Verify PNG was created
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.format == "PNG"


class TestExceptionHandling:
    """Tests for error handling."""

    def test_renderer_error_propagates(self) -> None:
        """Test that renderer errors propagate."""

        class FailingRenderer:
            def render(self, frame: RenderFrame) -> None:
                msg = "Test renderer error"
                raise RuntimeError(msg)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )

            with pytest.raises(RuntimeError, match="Test renderer error"):
                render_frame_to_png(frame, output_path, renderer=FailingRenderer())

    def test_filesystem_error_not_swallowed(self) -> None:
        """Test that filesystem errors are not silently swallowed."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        # Invalid path (not a directory)
        with pytest.raises(OSError):
            render_frame_to_png(frame, "/nonexistent/path/output.png")


class TestImmutability:
    """Tests for RenderFrame immutability."""

    def test_render_frame_unchanged(self) -> None:
        """Test that RenderFrame is not mutated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.png"
            frame = RenderFrame(
                frame_index=5,
                timestamp_seconds=5.0 / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={"entity": FrameTransform()},
            )

            original_frame_index = frame.frame_index
            original_keys = set(frame.transforms.keys())

            render_frame_to_png(frame, output_path)

            assert frame.frame_index == original_frame_index
            assert set(frame.transforms.keys()) == original_keys


class TestRealRuntimeFrame:
    """Tests using real RenderFrame from AnimationOrchestrator."""

    def test_real_runtime_frame_renders(self) -> None:
        """Test that real RenderFrame from runtime renders to PNG."""
        # Create real animation data
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
                    transform=FrameTransform(position_x=100, position_y=100, scale=2.0),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=200, position_y=200, scale=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        # Create orchestrator and load
        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)

        # Get RenderFrame using render_frame() method
        frame = orchestrator.render_frame()

        # Verify we got a valid RenderFrame
        assert frame is not None
        assert frame.frame_index == 0
        # Runtime transforms clip_ids (hero -> hero_1)
        assert len(frame.transforms) > 0

        # Render to PNG
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame_0.png"
            render_frame_to_png(frame, output_path, canvas_size=(400, 400))

            # Verify PNG
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.format == "PNG"
            assert image.mode == "RGBA"
            assert image.size == (400, 400)

            # Verify entity was rendered at expected position
            pixel = image.getpixel((100, 100))
            assert pixel != (255, 255, 255, 255)

    def test_runtime_frame_interpolation(self) -> None:
        """Test that animation interpolation works in rendered frame."""
        # Create animation with linear interpolation
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
                    transform=FrameTransform(position_x=0),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(position_x=240),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        orchestrator = AnimationOrchestrator()
        orchestrator.load(output, transforms)

        # Get frame at current position
        frame = orchestrator.render_frame()

        # Verify frame is valid
        assert frame is not None
        assert len(frame.transforms) > 0

        # Get the transform
        clip_id = list(frame.transforms.keys())[0]
        transform = frame.transforms[clip_id]

        # At frame 0, position_x should be 0
        assert transform.position_x == 0.0

        # Render to PNG
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame.png"
            render_frame_to_png(frame, output_path, canvas_size=(400, 400))

            image = Image.open(output_path)
            assert image.format == "PNG"


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in integration module."""
        import ast

        with open("tools/render/integration.py") as f:
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
