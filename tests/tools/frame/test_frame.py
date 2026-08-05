"""Tests for frame tools."""

from pathlib import Path

import pytest

from tools.frame import (
    Frame,
    FrameLayer,
    FrameToolError,
    FrameTransform,
    FrameTransition,
    FrameValidationError,
    LayerType,
)
from tools.frame.palette import CharacterColorPalette


class TestFrameModels:
    """Tests for frame data models."""

    def test_valid_frame(self) -> None:
        """Test creating a valid frame."""
        frame = Frame(frame_index=0, timestamp_ms=0)

        assert frame.frame_index == 0
        assert frame.timestamp_ms == 0
        assert frame.layers == ()

    def test_frame_with_layers(self) -> None:
        """Test frame with layers."""
        layer = FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)
        frame = Frame(frame_index=0, layers=[layer])

        assert len(frame.layers) == 1
        assert frame.layers[0].layer_type == LayerType.BACKGROUND

    def test_frame_with_duration(self) -> None:
        """Test frame with duration."""
        frame = Frame(frame_index=0, duration_ms=100)

        assert frame.duration_ms == 100

    def test_invalid_frame_index(self) -> None:
        """Test frame with invalid index."""
        with pytest.raises(ValueError):
            Frame(frame_index=-1)

    def test_frame_serialization(self) -> None:
        """Test frame serialization."""
        frame = Frame(frame_index=0, timestamp_ms=100)
        data = frame.model_dump()

        assert data["frame_index"] == 0
        assert data["timestamp_ms"] == 100


class TestFrameLayer:
    """Tests for frame layer model."""

    def test_valid_layer(self) -> None:
        """Test creating a valid layer."""
        layer = FrameLayer(layer_type=LayerType.CHARACTER, layer_index=0)

        assert layer.layer_type == LayerType.CHARACTER
        assert layer.layer_index == 0

    def test_layer_with_source(self) -> None:
        """Test layer with source path."""
        layer = FrameLayer(
            layer_type=LayerType.FOREGROUND,
            layer_index=0,
            source_path=Path("/path/to/layer.png"),
        )

        assert layer.source_path == Path("/path/to/layer.png")

    def test_layer_with_transform(self) -> None:
        """Test layer with transform."""
        transform = FrameTransform(position_x=10.0, scale=1.5)
        layer = FrameLayer(layer_type=LayerType.EFFECT, layer_index=0, transform=transform)

        assert layer.transform is not None
        assert layer.transform.position_x == 10.0
        assert layer.transform.scale == 1.5

    def test_invalid_layer_index(self) -> None:
        """Test layer with invalid index."""
        with pytest.raises(ValueError):
            FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=-1)


class TestFrameTransform:
    """Tests for frame transform model."""

    def test_valid_transform(self) -> None:
        """Test creating a valid transform."""
        transform = FrameTransform()

        assert transform.position_x is None
        assert transform.scale == 1.0
        assert transform.rotation_deg == 0.0
        assert transform.opacity == 1.0

    def test_transform_with_values(self) -> None:
        """Test transform with values."""
        transform = FrameTransform(
            position_x=100.0,
            position_y=200.0,
            scale=2.0,
            rotation_deg=45.0,
            opacity=0.8,
        )

        assert transform.position_x == 100.0
        assert transform.position_y == 200.0
        assert transform.scale == 2.0
        assert transform.rotation_deg == 45.0
        assert transform.opacity == 0.8

    def test_invalid_scale(self) -> None:
        """Test invalid scale value."""
        with pytest.raises(ValueError):
            FrameTransform(scale=-1.0)

    def test_invalid_opacity(self) -> None:
        """Test invalid opacity value."""
        with pytest.raises(ValueError):
            FrameTransform(opacity=1.5)


class TestFrameTransition:
    """Tests for frame transition model."""

    def test_valid_transition(self) -> None:
        """Test creating a valid transition."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
        )

        assert transition.source_frame_index == 0
        assert transition.target_frame_index == 1
        assert transition.duration_ms == 500
        assert transition.transition_type == "cut"

    def test_transition_with_type(self) -> None:
        """Test transition with custom type."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=1000,
            transition_type="fade",
        )

        assert transition.transition_type == "fade"

    def test_invalid_duration(self) -> None:
        """Test invalid duration."""
        with pytest.raises(ValueError):
            FrameTransition(
                source_frame_index=0,
                target_frame_index=1,
                duration_ms=-100,
            )


class TestLayerType:
    """Tests for layer type enum."""

    def test_layer_types(self) -> None:
        """Test all layer types exist."""
        assert LayerType.BACKGROUND == "background"
        assert LayerType.CHARACTER == "character"
        assert LayerType.FOREGROUND == "foreground"
        assert LayerType.EFFECT == "effect"


class TestCharacterColorPalette:
    """Tests for character color palette."""

    def test_valid_palette(self) -> None:
        """Test creating a valid palette."""
        palette = CharacterColorPalette(
            character_id="naruto",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        assert palette.character_id == "naruto"
        assert palette.hair == "#FF9900"
        assert palette.skin == "#FFCC99"
        assert palette.eyes == "#4477EE"
        assert palette.outfit == "#FFCC00"

    def test_lowercase_hex_normalized(self) -> None:
        """Test lowercase HEX is normalized to uppercase."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#ff9900",
            skin="#ffcc99",
            eyes="#4477ee",
            outfit="#ffcc00",
        )

        assert palette.hair == "#FF9900"
        assert palette.skin == "#FFCC99"
        assert palette.eyes == "#4477EE"
        assert palette.outfit == "#FFCC00"

    def test_optional_accessories(self) -> None:
        """Test optional accessories field."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            accessories="#333333",
        )

        assert palette.accessories == "#333333"

    def test_custom_colors(self) -> None:
        """Test custom colors as immutable tuple."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"cape": "#FF0000", "mask": "#000000"},
        )

        # custom_colors is now a tuple of tuples, sorted by key
        assert isinstance(palette.custom_colors, tuple)
        assert len(palette.custom_colors) == 2
        # Sorted alphabetically by key
        assert ("cape", "#FF0000") in palette.custom_colors
        assert ("mask", "#000000") in palette.custom_colors

    def test_empty_character_id(self) -> None:
        """Test empty character ID raises error."""
        with pytest.raises(ValueError):
            CharacterColorPalette(
                character_id="",
                hair="#FF9900",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_invalid_hex_format(self) -> None:
        """Test invalid HEX format raises error."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="#FF99",  # Too short
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_invalid_hex_prefix(self) -> None:
        """Test invalid HEX prefix raises error."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="FF9900",  # Missing #
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_immutable(self) -> None:
        """Test palette is immutable."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        with pytest.raises(Exception) as exc_info:
            palette.hair = "#00FF00"
        # Pydantic frozen raises ValidationError wrapped in Exception
        assert "frozen" in str(exc_info.value).lower()

    def test_deterministic_equality(self) -> None:
        """Test same inputs produce equal palettes."""
        palette1 = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        palette2 = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        assert palette1 == palette2

    def test_serialization(self) -> None:
        """Test palette serialization."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        data = palette.model_dump()

        assert data["character_id"] == "test"
        assert data["hair"] == "#FF9900"


class TestImports:
    """Tests for public API imports."""

    def test_import_frame_module(self) -> None:
        """Test frame module can be imported."""
        from tools.frame import Frame
        assert Frame is not None

    def test_import_palette(self) -> None:
        """Test palette module can be imported."""
        from tools.frame.palette import CharacterColorPalette
        assert CharacterColorPalette is not None

    def test_import_exceptions(self) -> None:
        """Test exception classes can be imported."""
        assert FrameToolError is not None
        assert FrameValidationError is not None


class TestDependencyRules:
    """Tests for dependency boundary verification."""

    def test_no_runtime_import(self) -> None:
        """Verify frame does not import runtime."""
        import tools.frame
        source = tools.frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from runtime" not in content
        assert "import runtime" not in content

    def test_no_agents_import(self) -> None:
        """Verify frame does not import agents."""
        import tools.frame
        source = tools.frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from agents" not in content
        assert "import agents" not in content

    def test_no_apps_import(self) -> None:
        """Verify frame does not import apps."""
        import tools.frame
        source = tools.frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from apps" not in content
        assert "import apps" not in content
