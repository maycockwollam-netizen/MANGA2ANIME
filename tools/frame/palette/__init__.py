"""Frame color palette module.

Provides character color palette contracts for colorization agents.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_hex_color(color: str | None) -> str | None:
    """Validate HEX color format.

    Args:
        color: HEX color string or None

    Returns:
        The color if valid

    Raises:
        ValueError: If color is not valid HEX format
    """
    if color is None:
        return None
    if not isinstance(color, str):
        raise ValueError(f"Color must be string, got {type(color).__name__}")
    if not HEX_PATTERN.match(color):
        raise ValueError(f"Invalid HEX color format: {color}")
    return color.upper()


class CharacterColorPalette(BaseModel):
    """Character color palette for consistent coloring.

    This is a data contract that defines the canonical colors for a character.
    Colorization agents should READ this palette as source of truth,
    not override colors with their own choices.

    The palette is immutable/frozen to prevent accidental modification.

    Example:
        palette = CharacterColorPalette(
            character_id="naruto",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
    """

    model_config = {"frozen": True}

    character_id: Annotated[str, Field(min_length=1, description="Unique character identifier")]
    hair: str = Field(description="Hair color in HEX format")
    skin: str = Field(description="Skin color in HEX format")
    eyes: str = Field(description="Eye color in HEX format")
    outfit: str = Field(description="Primary outfit color in HEX format")
    accessories: str | None = Field(default=None, description="Accessories color in HEX format")
    custom_colors: dict[str, str] = Field(
        default_factory=dict,
        description="Additional custom color mappings"
    )

    @field_validator("hair", "skin", "eyes", "outfit", "accessories", mode="before")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        """Validate HEX color format."""
        return _validate_hex_color(v)

    @field_validator("custom_colors", mode="before")
    @classmethod
    def validate_custom_colors(cls, v: dict | None) -> dict[str, str]:
        """Validate custom color values."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(f"custom_colors must be dict, got {type(v).__name__}")
        result = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError(f"Custom color key must be string, got {type(key).__name__}")
            validated = _validate_hex_color(value)
            if validated is not None:
                result[key] = validated
        return result


__all__ = ["CharacterColorPalette"]
