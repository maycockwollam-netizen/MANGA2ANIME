"""Tests for concrete renderer."""

import hashlib

import pytest
from PIL import Image

from tools.frame.models import FrameTransform
from tools.render import (
    ConcreteRenderer,
    Renderer,
    RendererError,
    RenderFrame,
)


class TestConcreteRendererBasics:
    """Tests for ConcreteRenderer basic functionality."""

    def test_satisfies_renderer_protocol(self) -> None:
        """Test that ConcreteRenderer satisfies the Renderer Protocol."""
        renderer = ConcreteRenderer()
        assert isinstance(renderer, Renderer)

    def test_default_canvas_size(self) -> None:
        """Test that default canvas size is 800x600."""
        renderer = ConcreteRenderer()
        assert renderer.canvas_size == (800, 600)

    def test_custom_canvas_size(self) -> None:
        """Test that custom canvas size is accepted."""
        renderer = ConcreteRenderer(canvas_size=(640, 480))
        assert renderer.canvas_size == (640, 480)

    def test_default_background(self) -> None:
        """Test that default background is white."""
        renderer = ConcreteRenderer()
        assert renderer.background == (255, 255, 255, 255)

    def test_custom_background(self) -> None:
        """Test that custom background is accepted."""
        renderer = ConcreteRenderer(background=(0, 0, 0, 255))
        assert renderer.background == (0, 0, 0, 255)

    def test_last_output_initially_none(self) -> None:
        """Test that last_output is None before first render."""
        renderer = ConcreteRenderer()
        assert renderer.last_output is None

    def test_render_returns_none(self) -> None:
        """Test that render() returns None."""
        renderer = ConcreteRenderer()
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )
        result = renderer.render(frame)
        assert result is None


class TestEmptyFrame:
    """Tests for empty frame rendering."""

    def test_empty_frame_produces_blank_canvas(self) -> None:
        """Test that empty frame produces blank canvas."""
        renderer = ConcreteRenderer(canvas_size=(100, 100))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        assert image.size == (100, 100)
        assert image.mode == "RGBA"

    def test_empty_frame_has_correct_background(self) -> None:
        """Test that empty frame has the correct background color."""
        renderer = ConcreteRenderer(
            canvas_size=(10, 10), background=(255, 0, 0, 255)
        )
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # Sample the center pixel
        pixel = image.getpixel((5, 5))
        assert pixel == (255, 0, 0, 255)


class TestSingleEntity:
    """Tests for single entity rendering."""

    def test_single_entity_renders(self) -> None:
        """Test that single entity is rendered."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"hero": FrameTransform(position_x=50, position_y=50)},
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # The entity should be rendered somewhere on the canvas
        # Check that image has been modified from blank
        assert image.getpixel((50, 50)) != (255, 255, 255, 255)


class TestMultipleEntities:
    """Tests for multiple entity rendering."""

    def test_multiple_entities_renders(self) -> None:
        """Test that multiple entities are rendered."""
        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "hero": FrameTransform(position_x=50, position_y=50),
                "villain": FrameTransform(position_x=150, position_y=150),
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # Both entities should be rendered
        pixel1 = image.getpixel((50, 50))
        pixel2 = image.getpixel((150, 150))
        # At least one of them should not be background color
        assert pixel1 != (255, 255, 255, 255) or pixel2 != (255, 255, 255, 255)

    def test_entity_order_deterministic(self) -> None:
        """Test that entities are rendered in sorted order for determinism."""
        renderer1 = ConcreteRenderer()
        renderer2 = ConcreteRenderer()

        frame1 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "zebra": FrameTransform(),
                "alpha": FrameTransform(),
                "middle": FrameTransform(),
            },
        )

        renderer1.render(frame1)
        renderer2.render(frame1)

        # Same frame should produce identical output
        assert renderer1.last_output.tobytes() == renderer2.last_output.tobytes()


class TestClipIdColor:
    """Tests for clip_id to color derivation."""

    def test_same_clip_id_same_color(self) -> None:
        """Test that same clip_id produces same color across instances."""
        renderer1 = ConcreteRenderer()
        renderer2 = ConcreteRenderer()

        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform()},
        )

        renderer1.render(frame)
        renderer2.render(frame)

        # Get pixel at entity position (with anchor at 0.5, entity is centered)
        pixel1 = renderer1.last_output.getpixel((50, 50))
        pixel2 = renderer2.last_output.getpixel((50, 50))
        assert pixel1 == pixel2

    def test_different_clip_ids_different_colors(self) -> None:
        """Test that different clip_ids produce different colors."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))

        frame1 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_a": FrameTransform(position_x=50, position_y=50)},
        )
        frame2 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_b": FrameTransform(position_x=150, position_y=150)},
        )

        renderer.render(frame1)
        pixel1 = renderer.last_output.getpixel((50, 50))

        renderer.render(frame2)
        pixel2 = renderer.last_output.getpixel((150, 150))

        assert pixel1 != pixel2
        # Verify both positions have entities (not background)
        assert pixel1 != (255, 255, 255, 255)
        assert pixel2 != (255, 255, 255, 255)


class TestPosition:
    """Tests for position transform."""

    def test_position_x(self) -> None:
        """Test that position_x is applied."""
        renderer = ConcreteRenderer(canvas_size=(300, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=150, position_y=100, anchor_x=0.0, anchor_y=0.0)},
        )
        renderer.render(frame)

        # With anchor_x=0.0, entity's left edge is at position_x
        # Background pixel at x=0 (should be white)
        bg_pixel = renderer.last_output.getpixel((0, 100))
        # Entity pixel at position_x (should not be white)
        entity_pixel = renderer.last_output.getpixel((150, 100))

        assert bg_pixel == (255, 255, 255, 255)
        assert entity_pixel != (255, 255, 255, 255)

    def test_position_y(self) -> None:
        """Test that position_y is applied."""
        renderer = ConcreteRenderer(canvas_size=(200, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=100, position_y=150, anchor_x=0.0, anchor_y=0.0)},
        )
        renderer.render(frame)

        bg_pixel = renderer.last_output.getpixel((100, 0))
        entity_pixel = renderer.last_output.getpixel((100, 150))

        assert bg_pixel == (255, 255, 255, 255)
        assert entity_pixel != (255, 255, 255, 255)


class TestScale:
    """Tests for scale transform."""

    def test_scale_2x(self) -> None:
        """Test that scale 2.0 doubles the entity size."""
        renderer = ConcreteRenderer(canvas_size=(500, 500))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100, position_y=100, scale=2.0, anchor_x=0.0, anchor_y=0.0
                )
            },
        )
        renderer.render(frame)

        # With scale 2.0 and anchor 0.0, entity should be 200x200
        # Left edge at 100, right edge at 300, top at 100, bottom at 300
        pixel_inside = renderer.last_output.getpixel((200, 200))
        pixel_outside = renderer.last_output.getpixel((400, 400))

        assert pixel_inside != (255, 255, 255, 255)
        assert pixel_outside == (255, 255, 255, 255)

    def test_scale_half(self) -> None:
        """Test that scale 0.5 halves the entity size."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=0, position_y=0, scale=0.5, anchor_x=0.0, anchor_y=0.0
                )
            },
        )
        renderer.render(frame)

        # With scale 0.5 and anchor 0.0, entity should be 50x50
        # From (0,0) to (50,50)
        pixel_entity = renderer.last_output.getpixel((25, 25))
        pixel_outside = renderer.last_output.getpixel((75, 75))

        assert pixel_entity != (255, 255, 255, 255)
        assert pixel_outside == (255, 255, 255, 255)

    def test_scale_zero(self) -> None:
        """Test that scale 0 handles gracefully."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=100, position_y=100, scale=0.0, anchor_x=0.5, anchor_y=0.5)},
        )
        # Should not raise
        renderer.render(frame)
        assert renderer.last_output is not None


class TestRotation:
    """Tests for rotation transform."""

    def test_rotation_45_degrees(self) -> None:
        """Test that 45 degree rotation is applied."""
        renderer = ConcreteRenderer(canvas_size=(400, 400))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=200, position_y=200, rotation_deg=45.0, anchor_x=0.5, anchor_y=0.5
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # The entity should be rendered at center
        pixel = image.getpixel((200, 200))
        assert pixel != (255, 255, 255, 255)


class TestOpacity:
    """Tests for opacity transform."""

    def test_full_opacity(self) -> None:
        """Test that opacity 1.0 produces fully opaque entity."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50, position_y=50, opacity=1.0, anchor_x=0.5, anchor_y=0.5)},
        )
        renderer.render(frame)

        pixel = renderer.last_output.getpixel((50, 50))
        # With full opacity, alpha should be 255
        assert pixel[3] == 255

    def test_half_opacity(self) -> None:
        """Test that opacity 0.5 produces semi-transparent entity."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50, position_y=50, opacity=0.5, anchor_x=0.5, anchor_y=0.5)},
        )
        renderer.render(frame)

        pixel = renderer.last_output.getpixel((50, 50))
        # With 0.5 opacity, alpha will be composited with background
        # The exact value depends on Pillow's paste compositing
        # But it should be between entity alpha (127) and full opacity (255)
        # and less than full opacity
        assert 127 <= pixel[3] < 255

    def test_zero_opacity(self) -> None:
        """Test that opacity 0.0 produces invisible entity."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50, position_y=50, opacity=0.0, anchor_x=0.5, anchor_y=0.5)},
        )
        renderer.render(frame)

        # Entity should be invisible (transparent)
        # Background should show through
        pixel = renderer.last_output.getpixel((50, 50))
        assert pixel == (255, 255, 255, 255)


class TestAnchor:
    """Tests for anchor transform."""

    def test_anchor_center(self) -> None:
        """Test that anchor 0.5, 0.5 centers on position."""
        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=150, position_y=150, anchor_x=0.5, anchor_y=0.5
                )
            },
        )
        renderer.render(frame)

        # With center anchor, the entity center should be at (150, 150)
        # Default size is 100x100, so center is at position
        pixel = renderer.last_output.getpixel((150, 150))
        assert pixel != (255, 255, 255, 255)

    def test_anchor_top_left(self) -> None:
        """Test that anchor 0.0, 0.0 places top-left at position."""
        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100, position_y=100, anchor_x=0.0, anchor_y=0.0
                )
            },
        )
        renderer.render(frame)

        # With top-left anchor, the top-left corner should be at (100, 100)
        pixel = renderer.last_output.getpixel((100, 100))
        assert pixel != (255, 255, 255, 255)

        # The entity extends from (100,100) to (200,200)
        # Check that a point outside (50, 50) is background
        bg_pixel = renderer.last_output.getpixel((50, 50))
        assert bg_pixel == (255, 255, 255, 255)


class TestNoneDefaults:
    """Tests for None transform value defaults."""

    def test_none_position_defaults_to_zero(self) -> None:
        """Test that None position_x/position_y default to 0."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=None, position_y=None, scale=None, rotation_deg=None,
                    anchor_x=0.0, anchor_y=0.0
                )
            },
        )
        renderer.render(frame)

        # Entity should be rendered at origin (0, 0) with default size 100x100
        # So pixels from 0-100 should be entity
        pixel = renderer.last_output.getpixel((50, 50))
        assert pixel != (255, 255, 255, 255)

    def test_none_opacity_defaults_to_one(self) -> None:
        """Test that None opacity defaults to 1.0."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50, position_y=50, opacity=None, anchor_x=0.5, anchor_y=0.5)},
        )
        renderer.render(frame)

        pixel = renderer.last_output.getpixel((50, 50))
        assert pixel[3] == 255  # Full opacity


class TestDeterminism:
    """Tests for deterministic rendering."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50, position_y=50, anchor_x=0.0, anchor_y=0.0)},
        )

        renderer.render(frame)
        output1 = renderer.last_output.tobytes()

        renderer.render(frame)
        output2 = renderer.last_output.tobytes()

        assert output1 == output2

    def test_determinism_across_instances(self) -> None:
        """Test that separate instances produce identical output."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity_a": FrameTransform(position_x=50, position_y=50, anchor_x=0.0, anchor_y=0.0),
                "entity_b": FrameTransform(position_x=150, position_y=150, anchor_x=0.0, anchor_y=0.0),
            },
        )

        renderer1 = ConcreteRenderer()
        renderer2 = ConcreteRenderer()

        renderer1.render(frame)
        renderer2.render(frame)

        assert renderer1.last_output.tobytes() == renderer2.last_output.tobytes()

    def test_stable_color_derivation(self) -> None:
        """Test that color derivation uses stable hash, not Python hash()."""
        # This test verifies we don't use Python's built-in hash()
        # which has randomization between processes
        clip_id = "test_entity"

        # Manually compute expected color using SHA-256
        digest = hashlib.sha256(clip_id.encode("utf-8")).digest()
        expected_r = int(digest[0])
        expected_g = int(digest[1])
        expected_b = int(digest[2])

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"test_entity": FrameTransform(position_x=50, position_y=50, anchor_x=0.0, anchor_y=0.0)},
        )
        renderer.render(frame)

        pixel = renderer.last_output.getpixel((50, 50))
        # Alpha should be 255 (default opacity)
        assert pixel[3] == 255
        # Color should match SHA-256 derivation
        assert pixel[0] == expected_r
        assert pixel[1] == expected_g
        assert pixel[2] == expected_b


class TestImmutability:
    """Tests for RenderFrame immutability."""

    def test_render_frame_unchanged(self) -> None:
        """Test that RenderFrame is not mutated."""
        renderer = ConcreteRenderer()
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform(position_x=50)},
        )

        # Capture original state
        original_frame_index = frame.frame_index
        original_transforms_keys = set(frame.transforms.keys())

        renderer.render(frame)

        # Verify frame is unchanged
        assert frame.frame_index == original_frame_index
        assert set(frame.transforms.keys()) == original_transforms_keys

    def test_transforms_unchanged(self) -> None:
        """Test that transforms mapping is not mutated."""
        renderer = ConcreteRenderer()
        transform = FrameTransform(position_x=50)
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": transform},
        )

        original_x = transform.position_x

        renderer.render(frame)

        assert transform.position_x == original_x


class TestErrorHandling:
    """Tests for error handling."""

    def test_zero_width_rejected(self) -> None:
        """Test that zero width canvas is rejected."""
        with pytest.raises(RendererError, match="width must be positive"):
            ConcreteRenderer(canvas_size=(0, 100))

    def test_zero_height_rejected(self) -> None:
        """Test that zero height canvas is rejected."""
        with pytest.raises(RendererError, match="height must be positive"):
            ConcreteRenderer(canvas_size=(100, 0))

    def test_negative_width_rejected(self) -> None:
        """Test that negative width canvas is rejected."""
        with pytest.raises(RendererError, match="width must be positive"):
            ConcreteRenderer(canvas_size=(-1, 100))


class TestImports:
    """Tests for module imports."""

    def test_concrete_renderer_importable(self) -> None:
        """Test ConcreteRenderer is importable."""
        from tools.render import ConcreteRenderer

        assert ConcreteRenderer is not None

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in concrete_renderer module."""
        import ast

        with open("tools/render/concrete_renderer.py") as f:
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
        forbidden = ["runtime", "AnimationRuntime", "AnimationTimeline", "AnimationClip"]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"


class TestAssetRendering:
    """Tests for asset-backed rendering."""

    def test_basic_asset_rendering(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that a basic asset is loaded and rendered correctly."""
        from pathlib import Path

        # Create a simple test asset
        asset_path = tmp_path / "test_asset.png"
        asset = Image.new("RGB", (50, 50), color=(255, 0, 0))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path(asset_path),
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # Check that the asset was rendered at the correct position
        # With anchor at 0.5, the center of the 50x50 asset should be at (50, 50)
        # So the top-left corner should be at (25, 25)
        pixel = image.getpixel((25, 25))
        assert pixel == (255, 0, 0, 255)

    def test_transparent_rgba_asset(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that transparent RGBA assets are rendered with alpha preserved."""
        from pathlib import Path

        # Create an RGBA asset with transparency
        asset_path = tmp_path / "transparent_asset.png"
        asset = Image.new("RGBA", (40, 40), color=(0, 255, 0, 128))  # Semi-transparent green
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path(asset_path),
                    opacity=1.0,
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # Check that the asset was rendered (not background color)
        # The semi-transparent green will blend with white background
        pixel = image.getpixel((50, 50))
        # The result should be a blend of green and white, with alpha < 255
        assert pixel[3] < 255  # Alpha is less than full due to transparency

    def test_asset_position_transform(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that position transform is applied to assets."""
        from pathlib import Path

        asset_path = tmp_path / "position_test.png"
        asset = Image.new("RGB", (50, 50), color=(0, 0, 255))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=150,
                    source_path=Path(asset_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        # With anchor at (0, 0), top-left of asset should be at (100, 150)
        pixel_at_position = image.getpixel((100, 150))
        assert pixel_at_position == (0, 0, 255, 255)

    def test_asset_scale_transform(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that scale transform is applied to assets."""
        from pathlib import Path

        # Create a 50x50 asset
        asset_path = tmp_path / "scale_test.png"
        asset = Image.new("RGB", (50, 50), color=(255, 0, 0))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=100,
                    scale=2.0,
                    source_path=Path(asset_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        # With scale 2.0, the 50x50 asset should become 100x100
        # Position (0,0) of asset should be at (100, 100)
        # Position (50, 50) of asset should be at (150, 150)
        # Position (99, 99) of asset should be at (199, 199) - last red pixel
        pixel_inside = image.getpixel((150, 150))
        assert pixel_inside == (255, 0, 0, 255)

        # Check that it's actually scaled by verifying a pixel outside the original size
        # but inside the scaled size
        pixel_at_scaled = image.getpixel((120, 120))
        assert pixel_at_scaled == (255, 0, 0, 255)

    def test_asset_rotation_transform(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that rotation transform is applied to assets."""
        from pathlib import Path

        # Create a simple square asset
        asset_path = tmp_path / "rotation_test.png"
        asset = Image.new("RGB", (50, 50), color=(0, 255, 0))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=100,
                    rotation_deg=90,
                    source_path=Path(asset_path),
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        # Just verify it renders without error

    def test_asset_opacity_transform(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that opacity transform is applied to assets."""
        from pathlib import Path

        asset_path = tmp_path / "opacity_test.png"
        asset = Image.new("RGBA", (50, 50), color=(255, 0, 0, 255))  # Fully opaque red
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(100, 100), background=(255, 255, 255, 255))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    opacity=0.5,
                    source_path=Path(asset_path),
                    anchor_x=0.5,
                    anchor_y=0.5,
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        # With 0.5 opacity on an opaque red asset, the result will be
        # semi-transparent red blended with white background
        pixel = image.getpixel((50, 50))
        # The alpha channel should be < 255 due to opacity applied
        assert pixel[3] < 255
        # The red channel should be > 128 due to blending (more red than white)
        assert pixel[0] > 128

    def test_asset_anchor_behavior(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that anchor behavior is correct for assets."""
        from pathlib import Path

        asset_path = tmp_path / "anchor_test.png"
        asset = Image.new("RGB", (100, 100), color=(128, 128, 128))
        asset.save(asset_path)

        # Test top-left anchor: position (100, 100) is the top-left of the asset
        renderer1 = ConcreteRenderer(canvas_size=(300, 300))
        frame1 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=100,
                    anchor_x=0.0,
                    anchor_y=0.0,
                    source_path=Path(asset_path),
                )
            },
        )
        renderer1.render(frame1)
        # Check pixel at (150, 150) which is center of asset (100,100 + 50 offset for 100x100 asset)
        pixel1 = renderer1.last_output.getpixel((150, 150))

        # Test center anchor: position (100, 100) is the center of the asset
        renderer2 = ConcreteRenderer(canvas_size=(300, 300))
        frame2 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=100,
                    anchor_x=0.5,
                    anchor_y=0.5,
                    source_path=Path(asset_path),
                )
            },
        )
        renderer2.render(frame2)
        # Check pixel at (100, 100) which is center of asset (anchor at center)
        pixel2 = renderer2.last_output.getpixel((100, 100))

        # Both should have rendered the same color at their respective centers
        assert pixel1[:3] == pixel2[:3] == (128, 128, 128)

    def test_multiple_assets_composited(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that multiple assets are composited in deterministic order."""
        from pathlib import Path

        # Create two assets
        asset1_path = tmp_path / "asset1.png"
        asset1 = Image.new("RGBA", (50, 50), color=(255, 0, 0, 255))
        asset1.save(asset1_path)

        asset2_path = tmp_path / "asset2.png"
        asset2 = Image.new("RGBA", (50, 50), color=(0, 0, 255, 255))
        asset2.save(asset2_path)

        renderer = ConcreteRenderer(canvas_size=(300, 300))

        # Render with both assets overlapping
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "alpha_entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path(asset1_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                ),
                "beta_entity": FrameTransform(
                    position_x=75,
                    position_y=75,
                    source_path=Path(asset2_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                ),
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None

        # Deterministic order: alpha renders before beta
        # At (75, 75), beta's top-left corner, should see blue (beta on top)
        pixel_overlap = image.getpixel((75, 75))
        assert pixel_overlap == (0, 0, 255, 255)

        # At (50, 50), only alpha renders (outside beta), should see red
        pixel_alpha_only = image.getpixel((50, 50))
        assert pixel_alpha_only == (255, 0, 0, 255)

    def test_missing_asset(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that missing asset raises TransformError."""
        from pathlib import Path

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path("/nonexistent/path/asset.png"),
                )
            },
        )

        from tools.render import TransformError

        with pytest.raises(TransformError, match="Asset not found"):
            renderer.render(frame)

    def test_invalid_asset(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that invalid asset raises TransformError."""
        from pathlib import Path

        # Create an invalid file (not an image)
        invalid_path = tmp_path / "invalid_asset.txt"
        invalid_path.write_text("This is not an image")

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path(invalid_path),
                )
            },
        )

        from tools.render import TransformError

        with pytest.raises(TransformError, match="Failed to load asset"):
            renderer.render(frame)

    def test_deterministic_asset_rendering(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that repeated rendering of assets is deterministic."""
        from pathlib import Path

        asset_path = tmp_path / "deterministic_asset.png"
        asset = Image.new("RGB", (50, 50), color=(100, 150, 200))
        asset.save(asset_path)

        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=100,
                    position_y=100,
                    source_path=Path(asset_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                )
            },
        )

        renderer1 = ConcreteRenderer(canvas_size=(300, 300))
        renderer2 = ConcreteRenderer(canvas_size=(300, 300))

        renderer1.render(frame)
        renderer2.render(frame)

        assert renderer1.last_output.tobytes() == renderer2.last_output.tobytes()

    def test_asset_rgb_to_rgba_conversion(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that RGB assets are converted to RGBA for compositing."""
        from pathlib import Path

        # Create an RGB asset (no alpha)
        asset_path = tmp_path / "rgb_asset.png"
        asset = Image.new("RGB", (50, 50), color=(255, 128, 0))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(200, 200))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=50,
                    position_y=50,
                    source_path=Path(asset_path),
                    anchor_x=0.0,
                    anchor_y=0.0,
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        # Check that image is RGBA mode
        assert image.mode == "RGBA"

        # Check that the color is preserved with full alpha
        pixel = image.getpixel((50, 50))
        assert pixel[:3] == (255, 128, 0)
        assert pixel[3] == 255

    def test_asset_with_all_transforms(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that all transforms work together with assets."""
        from pathlib import Path

        asset_path = tmp_path / "full_transform_asset.png"
        asset = Image.new("RGBA", (50, 50), color=(0, 255, 0, 200))
        asset.save(asset_path)

        renderer = ConcreteRenderer(canvas_size=(300, 300))
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity": FrameTransform(
                    position_x=150,
                    position_y=150,
                    scale=1.5,
                    rotation_deg=45,
                    opacity=0.8,
                    anchor_x=0.5,
                    anchor_y=0.5,
                    source_path=Path(asset_path),
                )
            },
        )
        renderer.render(frame)

        image = renderer.last_output
        assert image is not None
        assert image.mode == "RGBA"


class TestSourcePathField:
    """Tests for FrameTransform source_path field."""

    def test_source_path_none_by_default(self) -> None:
        """Test that source_path is None by default."""
        transform = FrameTransform()
        assert transform.source_path is None

    def test_source_path_can_be_set(self) -> None:
        """Test that source_path can be set."""
        from pathlib import Path

        path = Path("/path/to/asset.png")
        transform = FrameTransform(source_path=path)
        assert transform.source_path == path

    def test_source_path_with_other_fields(self) -> None:
        """Test that source_path works with other transform fields."""
        from pathlib import Path

        path = Path("sprite.png")
        transform = FrameTransform(
            position_x=100,
            position_y=200,
            scale=2.0,
            rotation_deg=90,
            opacity=0.5,
            anchor_x=0.25,
            anchor_y=0.75,
            source_path=path,
        )

        assert transform.position_x == 100
        assert transform.position_y == 200
        assert transform.scale == 2.0
        assert transform.rotation_deg == 90
        assert transform.opacity == 0.5
        assert transform.anchor_x == 0.25
        assert transform.anchor_y == 0.75
        assert transform.source_path == path
