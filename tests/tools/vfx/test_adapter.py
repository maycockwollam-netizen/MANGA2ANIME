"""Tests for VFX effect adapter."""

import pytest
from PIL import Image

from tools.vfx import (
    EffectAdapter,
    SpeedLinesConfig,
    SpeedLinesEffect,
    VfxError,
)


def _make_canvas() -> Image.Image:
    return Image.new("RGBA", (100, 100), (255, 255, 255, 255))


class TestEffectAdapterBasics:
    """Tests for EffectAdapter basic functionality."""

    def test_adapter_binds_effect_and_config(self) -> None:
        """Test that adapter exposes the bound effect and config."""
        effect = SpeedLinesEffect()
        config = SpeedLinesConfig(line_count=8)
        adapter = EffectAdapter(effect, config)

        assert adapter.effect is effect
        assert adapter.config is config

    def test_adapter_apply_returns_image(self) -> None:
        """Test that apply returns an RGBA image of matching size."""
        adapter = EffectAdapter(SpeedLinesEffect(), SpeedLinesConfig(line_count=8))
        result = adapter.apply(_make_canvas())

        assert isinstance(result, Image.Image)
        assert result.mode == "RGBA"
        assert result.size == (100, 100)


class TestEffectAdapterForwarding:
    """Tests for EffectAdapter forwarding behavior."""

    def test_adapter_applies_effect(self) -> None:
        """Test that the adapter actually applies the effect (canvas changes)."""
        canvas = _make_canvas()
        adapter = EffectAdapter(
            SpeedLinesEffect(),
            SpeedLinesConfig(line_count=32, line_length=50, line_color=(0, 0, 0, 255)),
        )
        result = adapter.apply(canvas)

        # The composited result must differ from the blank base.
        assert list(result.getdata()) != list(canvas.getdata())

    def test_adapter_does_not_mutate_input(self) -> None:
        """Test that the adapter does not mutate the input image."""
        canvas = _make_canvas()
        original = list(canvas.getdata())
        adapter = EffectAdapter(SpeedLinesEffect(), SpeedLinesConfig(line_count=16))

        adapter.apply(canvas)

        assert list(canvas.getdata()) == original


class TestEffectAdapterEdgeCases:
    """Tests for EffectAdapter edge cases."""

    def test_adapter_noop_config_returns_identical_pixels(self) -> None:
        """Test that a zero-line config yields pixels identical to the base."""
        canvas = _make_canvas()
        adapter = EffectAdapter(SpeedLinesEffect(), SpeedLinesConfig(line_count=0))
        result = adapter.apply(canvas)

        assert list(result.getdata()) == list(canvas.getdata())

    def test_adapter_repeated_apply_is_deterministic(self) -> None:
        """Test that repeated apply produces identical results."""
        adapter = EffectAdapter(SpeedLinesEffect(), SpeedLinesConfig(line_count=16, seed=7))
        r1 = adapter.apply(_make_canvas())
        r2 = adapter.apply(_make_canvas())

        assert list(r1.getdata()) == list(r2.getdata())


class TestEffectAdapterExceptions:
    """Tests for EffectAdapter exception propagation."""

    def test_vfx_error_propagates(self) -> None:
        """Test that VfxError propagates from the underlying effect."""

        class FailingEffect:
            def apply(self, base: Image.Image, config: SpeedLinesConfig) -> Image.Image:
                raise VfxError("effect failed")

        adapter = EffectAdapter(FailingEffect(), SpeedLinesConfig())
        with pytest.raises(VfxError, match="effect failed"):
            adapter.apply(_make_canvas())
