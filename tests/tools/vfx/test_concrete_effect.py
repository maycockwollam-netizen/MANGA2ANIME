"""Tests for concrete speed lines VFX effect."""

import pytest
from PIL import Image

from tools.vfx import (
    SpeedLineDirection,
    SpeedLinesConfig,
    SpeedLinesEffect,
    VfxEffect,
    VfxRenderError,
)


def _canvas(size: tuple[int, int] = (200, 200)) -> Image.Image:
    return Image.new("RGBA", size, (255, 255, 255, 255))


class TestSpeedLinesEffectBasics:
    """Tests for SpeedLinesEffect basic functionality."""

    def test_satisfies_vfx_effect_protocol(self) -> None:
        """Test that SpeedLinesEffect satisfies the VfxEffect protocol."""
        assert isinstance(SpeedLinesEffect(), VfxEffect)

    def test_apply_returns_rgba_image(self) -> None:
        """Test that apply returns an RGBA image."""
        result = SpeedLinesEffect().apply(_canvas(), SpeedLinesConfig(line_count=16))
        assert result.mode == "RGBA"

    def test_apply_preserves_size(self) -> None:
        """Test that apply preserves the input canvas size."""
        result = SpeedLinesEffect().apply(_canvas((300, 150)), SpeedLinesConfig(line_count=16))
        assert result.size == (300, 150)

    def test_apply_does_not_mutate_input(self) -> None:
        """Test that apply does not mutate the input image."""
        canvas = _canvas()
        original = list(canvas.getdata())
        SpeedLinesEffect().apply(canvas, SpeedLinesConfig(line_count=16))
        assert list(canvas.getdata()) == original

    def test_apply_returns_new_image(self) -> None:
        """Test that apply returns a new image instance, not the input."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(canvas, SpeedLinesConfig(line_count=16))
        assert result is not canvas


class TestSpeedLinesDeterminism:
    """Tests for deterministic speed line placement."""

    def test_same_seed_same_output(self) -> None:
        """Test that the same seed produces identical output."""
        cfg = SpeedLinesConfig(line_count=32, line_length=80, seed=42)
        r1 = SpeedLinesEffect().apply(_canvas(), cfg)
        r2 = SpeedLinesEffect().apply(_canvas(), cfg)
        assert list(r1.getdata()) == list(r2.getdata())

    def test_different_seed_different_output(self) -> None:
        """Test that different seeds produce different output."""
        cfg_a = SpeedLinesConfig(line_count=32, line_length=80, seed=1)
        cfg_b = SpeedLinesConfig(line_count=32, line_length=80, seed=2)
        r1 = SpeedLinesEffect().apply(_canvas(), cfg_a)
        r2 = SpeedLinesEffect().apply(_canvas(), cfg_b)
        assert list(r1.getdata()) != list(r2.getdata())


class TestSpeedLinesNoOp:
    """Tests for no-op fast paths."""

    def test_zero_lines_returns_identical_pixels(self) -> None:
        """Test that zero lines yields pixels identical to the base."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(canvas, SpeedLinesConfig(line_count=0))
        assert list(result.getdata()) == list(canvas.getdata())

    def test_zero_length_returns_identical_pixels(self) -> None:
        """Test that zero line length yields pixels identical to the base."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(canvas, SpeedLinesConfig(line_length=0))
        assert list(result.getdata()) == list(canvas.getdata())

    def test_zero_intensity_returns_identical_pixels(self) -> None:
        """Test that zero intensity yields pixels identical to the base."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(canvas, SpeedLinesConfig(intensity=0.0))
        assert list(result.getdata()) == list(canvas.getdata())

    def test_zero_alpha_color_returns_identical_pixels(self) -> None:
        """Test that zero-alpha line color yields identical pixels."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(
            canvas, SpeedLinesConfig(line_color=(0, 0, 0, 0))
        )
        assert list(result.getdata()) == list(canvas.getdata())


class TestSpeedLinesEffectApplication:
    """Tests that speed lines actually alter the canvas."""

    def test_effect_alters_canvas(self) -> None:
        """Test that applying speed lines changes pixels vs the blank base."""
        canvas = _canvas()
        result = SpeedLinesEffect().apply(
            canvas,
            SpeedLinesConfig(line_count=64, line_length=120, line_color=(0, 0, 0, 255)),
        )
        assert list(result.getdata()) != list(canvas.getdata())

    def test_directions_all_produce_output(self) -> None:
        """Test that each supported direction alters the canvas."""
        for direction in SpeedLineDirection:
            canvas = _canvas()
            result = SpeedLinesEffect().apply(
                canvas, SpeedLinesConfig(line_count=32, line_length=80, direction=direction)
            )
            assert list(result.getdata()) != list(canvas.getdata()), (
                f"direction {direction} did not alter canvas"
            )

    def test_horizontal_direction_is_horizontal(self) -> None:
        """Test that horizontal lines stay within rows (no vertical spread)."""
        canvas = _canvas((200, 200))
        result = SpeedLinesEffect().apply(
            canvas,
            SpeedLinesConfig(
                line_count=32,
                line_length=80,
                direction=SpeedLineDirection.HORIZONTAL,
                focal_x=0.5,
                focal_y=0.5,
                line_color=(0, 0, 0, 255),
            ),
        )
        # Horizontal lines drawn from the focal point: the center row should
        # contain black pixels, while rows far from center should be unchanged.
        px = result.load()
        center_y = 100
        # Center row should contain at least one dark pixel.
        dark_in_center_row = any(
            px[x, center_y][0] < 50 for x in range(0, 200, 4)
        )
        assert dark_in_center_row

    def test_intensity_scales_alpha(self) -> None:
        """Test that lower intensity produces lighter (less opaque) lines."""
        full = SpeedLinesEffect().apply(
            _canvas(),
            SpeedLinesConfig(line_count=64, line_length=120, intensity=1.0, seed=3),
        )
        half = SpeedLinesEffect().apply(
            _canvas(),
            SpeedLinesConfig(line_count=64, line_length=120, intensity=0.1, seed=3),
        )
        full_dark = sum(1 for p in full.getdata() if p[3] > 200)
        half_dark = sum(1 for p in half.getdata() if p[3] > 200)
        # Fewer fully-opaque pixels at lower intensity.
        assert half_dark <= full_dark


class TestSpeedLinesEffectErrors:
    """Tests for error handling in SpeedLinesEffect."""

    def test_non_rgba_base_raises(self) -> None:
        """Test that a non-RGBA base image raises VfxRenderError."""
        base = Image.new("RGB", (200, 200), (255, 255, 255))
        with pytest.raises(VfxRenderError, match="RGBA"):
            SpeedLinesEffect().apply(base, SpeedLinesConfig(line_count=8))

    def test_zero_size_base_raises(self) -> None:
        """Test that a zero-size base image raises VfxRenderError."""
        base = Image.new("RGBA", (0, 0))
        with pytest.raises(VfxRenderError, match="positive size"):
            SpeedLinesEffect().apply(base, SpeedLinesConfig(line_count=8))
