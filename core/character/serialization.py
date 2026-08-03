"""Character serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.character.character import Character
from core.character.exceptions import CharacterSerializationError


class CharacterSerializer:
    """Handles character serialization to and from JSON."""

    @staticmethod
    def serialize(character: Character) -> dict[str, Any]:
        """Serialize a character to a dictionary.

        Args:
            character: The character to serialize.

        Returns:
            Dictionary representation of the character.
        """
        return {
            "id": character.id,
            "name": character.name,
            "display_name": character.display_name,
            "metadata": {
                "description": character.metadata.description,
                "tags": list(character.metadata.tags),
                "notes": character.metadata.notes,
                "created_at": _serialize_datetime(character.metadata.created_at),
                "updated_at": _serialize_datetime(character.metadata.updated_at),
                "custom_metadata": character.metadata.custom_metadata,
            },
            "appearance": {
                "description": character.appearance.description,
                "style": character.appearance.style,
                "hair_color": character.appearance.hair_color,
                "eye_color": character.appearance.eye_color,
                "skin_tone": character.appearance.skin_tone,
                "height_description": character.appearance.height_description,
                "build_description": character.appearance.build_description,
                "age_description": character.appearance.age_description,
                "asset_references": character.appearance.asset_references,
                "custom_attributes": character.appearance.custom_attributes,
            },
            "properties": {
                "height": character.properties.height,
                "age": character.properties.age,
                "role": character.properties.role,
                "faction": character.properties.faction,
                "custom_attributes": character.properties.custom_attributes,
            },
            "state": {
                "active": character.state.active,
                "visible": character.state.visible,
                "enabled": character.state.enabled,
                "custom_state": character.state.custom_state,
            },
            "references": {
                "design_asset_id": character.references.design_asset_id,
                "portrait_asset_id": character.references.portrait_asset_id,
                "model_asset_id": character.references.model_asset_id,
                "voice_asset_id": character.references.voice_asset_id,
                "scene_id": character.references.scene_id,
                "object_id": character.references.object_id,
                "track_ids": list(character.references.track_ids),
                "custom_references": character.references.custom_references,
            },
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Character:
        """Deserialize a character from a dictionary.

        Args:
            data: Dictionary containing character data.

        Returns:
            Deserialized Character instance.

        Raises:
            CharacterSerializationError: If data is malformed.
        """
        if not isinstance(data, dict):
            raise CharacterSerializationError("Character data must be a dictionary")

        if "id" not in data:
            raise CharacterSerializationError("Missing required field: id")

        try:
            return Character.model_validate(data)
        except Exception as e:
            raise CharacterSerializationError(f"Invalid character data: {e}") from e

    @staticmethod
    def to_json(character: Character, indent: int | None = 2) -> str:
        """Serialize a character to JSON string.

        Args:
            character: The character to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            CharacterSerializer.serialize(character),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Character:
        """Deserialize a character from JSON string.

        Args:
            json_str: JSON string containing character data.

        Returns:
            Deserialized Character instance.

        Raises:
            CharacterSerializationError: If JSON is invalid or character data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise CharacterSerializationError(f"Invalid JSON: {e}") from e

        return CharacterSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
