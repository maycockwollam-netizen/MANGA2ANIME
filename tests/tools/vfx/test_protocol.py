"""Tests for VFX effect protocol contract."""

from PIL import Image

from tools.vfx import (
    SpeedLinesConfig,
    SpeedLinesEffect,
    VfxConfigError,
    VfxEffect,
    VfxError,
    VfxRenderError,
)


class TestVfxEffectProtocolCompliance:
    """Tests for VfxEffect protocol structural typing."""

    def test_class_with_apply_method_satisfies_protocol(self) -> None:
        """Test that a class with apply(base, config) satisfies VfxEffect."""

        class ValidEffect:
            def apply(self, base: Image.Image, config: SpeedLinesConfig) -> Image.Image:
                return base.copy()

        assert isinstance(ValidEffect(), VfxEffect)

    def test_class_without_apply_method_does_not_satisfy_protocol(self) -> None:
        """Test that a class without apply method does not satisfy VfxEffect."""

        class InvalidEffect:
            def draw(self, base: Image.Image, config: SpeedLinesConfig) -> Image.Image:
                return base.copy()

        assert not isinstance(InvalidEffect(), VfxEffect)

    def test_vfx_effect_is_runtime_checkable(self) -> None:
        """Test that isinstance() works at runtime for VfxEffect."""
        assert isinstance(SpeedLinesEffect(), VfxEffect)
        assert not isinstance("not an effect", VfxEffect)
        assert not isinstance(123, VfxEffect)
        assert not isinstance(None, VfxEffect)

    def test_vfx_effect_protocol_is_type(self) -> None:
        """Test that VfxEffect itself is a type/class."""
        assert isinstance(VfxEffect, type)


class TestVfxEffectImports:
    """Tests for VFX module imports."""

    def test_vfx_effect_importable(self) -> None:
        """Test VfxEffect is importable from tools.vfx."""
        from tools.vfx import VfxEffect

        assert VfxEffect is not None

    def test_speed_lines_effect_importable(self) -> None:
        """Test SpeedLinesEffect is importable from tools.vfx."""
        from tools.vfx import SpeedLinesEffect

        assert SpeedLinesEffect is not None

    def test_vfx_error_hierarchy(self) -> None:
        """Test VFX exception hierarchy is importable and correct."""
        assert issubclass(VfxConfigError, VfxError)
        assert issubclass(VfxRenderError, VfxError)

    def test_vfx_errors_can_be_raised(self) -> None:
        """Test that VFX exceptions can be raised."""
        import pytest

        with pytest.raises(VfxError):
            raise VfxError("test error")
        with pytest.raises(VfxConfigError):
            raise VfxConfigError("config error")
        with pytest.raises(VfxRenderError):
            raise VfxRenderError("render error")
