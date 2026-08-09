"""Tests for VFX data models."""

import pytest
from pydantic import ValidationError

from tools.vfx import (
    SpeedLineDirection,
    SpeedLinesConfig,
    VfxResult,
)


class TestSpeedLinesConfigDefaults:
    """Tests for SpeedLinesConfig default values."""

    def test_default_config_is_valid(self) -> None:
        """Test that default config is valid and has expected defaults."""
        config = SpeedLinesConfig()
        assert config.line_count == 64
        assert config.line_length == 120
        assert config.line_thickness == 2
        assert config.line_color == (0, 0, 0, 255)
        assert config.focal_x == 0.5
        assert config.focal_y == 0.5
        assert config.direction == SpeedLineDirection.RADIAL
        assert config.intensity == 1.0
        assert config.seed == 0


class TestSpeedLinesConfigValidation:
    """Tests for SpeedLinesConfig field validation."""

    def test_line_count_must_be_non_negative(self) -> None:
        """Test that negative line_count is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_count=-1)

    def test_line_length_must_be_non_negative(self) -> None:
        """Test that negative line_length is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_length=-1)

    def test_line_thickness_must_be_at_least_one(self) -> None:
        """Test that zero line_thickness is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_thickness=0)

    def test_focal_x_must_be_in_range(self) -> None:
        """Test that focal_x outside [0,1] is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(focal_x=-0.1)
        with pytest.raises(ValidationError):
            SpeedLinesConfig(focal_x=1.1)

    def test_focal_y_must_be_in_range(self) -> None:
        """Test that focal_y outside [0,1] is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(focal_y=-0.1)
        with pytest.raises(ValidationError):
            SpeedLinesConfig(focal_y=1.1)

    def test_intensity_must_be_in_range(self) -> None:
        """Test that intensity outside [0,1] is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(intensity=-0.1)
        with pytest.raises(ValidationError):
            SpeedLinesConfig(intensity=1.1)

    def test_seed_must_be_non_negative(self) -> None:
        """Test that negative seed is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(seed=-1)


class TestSpeedLinesConfigColor:
    """Tests for SpeedLinesConfig line_color validation."""

    def test_valid_color_accepted(self) -> None:
        """Test that a valid RGBA tuple is accepted."""
        config = SpeedLinesConfig(line_color=(10, 20, 30, 40))
        assert config.line_color == (10, 20, 30, 40)

    def test_color_list_normalized_to_tuple(self) -> None:
        """Test that a list is normalized to a tuple."""
        config = SpeedLinesConfig(line_color=[255, 0, 0, 255])
        assert config.line_color == (255, 0, 0, 255)
        assert isinstance(config.line_color, tuple)

    def test_color_wrong_length_rejected(self) -> None:
        """Test that a 3-tuple is rejected (needs RGBA)."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_color=(255, 0, 0))

    def test_color_channel_out_of_range_rejected(self) -> None:
        """Test that a channel > 255 is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_color=(256, 0, 0, 255))

    def test_color_non_int_channel_rejected(self) -> None:
        """Test that a float channel is rejected."""
        with pytest.raises(ValidationError):
            SpeedLinesConfig(line_color=(1.5, 0, 0, 255))


class TestSpeedLineDirection:
    """Tests for SpeedLineDirection enum."""

    def test_radial_value(self) -> None:
        """Test RADIAL enum value."""
        assert SpeedLineDirection.RADIAL.value == "radial"

    def test_horizontal_value(self) -> None:
        """Test HORIZONTAL enum value."""
        assert SpeedLineDirection.HORIZONTAL.value == "horizontal"

    def test_vertical_value(self) -> None:
        """Test VERTICAL enum value."""
        assert SpeedLineDirection.VERTICAL.value == "vertical"

    def test_direction_from_string(self) -> None:
        """Test that direction can be constructed from string."""
        config = SpeedLinesConfig(direction="horizontal")
        assert config.direction == SpeedLineDirection.HORIZONTAL


class TestVfxResult:
    """Tests for VfxResult data contract."""

    def test_valid_result(self) -> None:
        """Test that a valid VfxResult can be constructed."""
        from pathlib import Path

        result = VfxResult(
            effect_name="speed_lines",
            output_path=Path("/tmp/out.png"),
            canvas_size=(800, 600),
        )
        assert result.effect_name == "speed_lines"
        assert result.applied is True

    def test_result_is_frozen(self) -> None:
        """Test that VfxResult is immutable."""
        from pathlib import Path

        result = VfxResult(
            effect_name="speed_lines",
            output_path=Path("/tmp/out.png"),
            canvas_size=(800, 600),
        )
        with pytest.raises(ValidationError):
            result.applied = False  # type: ignore[misc]

    def test_empty_effect_name_rejected(self) -> None:
        """Test that empty effect_name is rejected."""
        from pathlib import Path

        with pytest.raises(ValidationError):
            VfxResult(
                effect_name="",
                output_path=Path("/tmp/out.png"),
                canvas_size=(800, 600),
            )
