"""Scene serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.scene.exceptions import SceneSerializationError
from core.scene.scene import Scene


class SceneSerializer:
    """Handles scene serialization to and from JSON."""

    @staticmethod
    def serialize(scene: Scene) -> dict[str, Any]:
        """Serialize a scene to a dictionary.

        Args:
            scene: The scene to serialize.

        Returns:
            Dictionary representation of the scene.
        """
        return {
            "id": scene.id,
            "metadata": {
                "name": scene.metadata.name,
                "description": scene.metadata.description,
                "created_at": _serialize_datetime(scene.metadata.created_at),
                "updated_at": _serialize_datetime(scene.metadata.updated_at),
            },
            "settings": {
                "background_color": scene.settings.background_color,
                "ambient_light": scene.settings.ambient_light,
            },
            "objects": {
                obj_id: SceneSerializer._serialize_object(obj)
                for obj_id, obj in scene.objects.items()
            },
        }

    @staticmethod
    def _serialize_object(obj: Any) -> dict[str, Any]:
        """Serialize a scene object."""
        return {
            "id": obj.id,
            "name": obj.name,
            "object_type": obj.object_type,
            "transform": {
                "position": {
                    "x": obj.transform.position.x,
                    "y": obj.transform.position.y,
                    "z": obj.transform.position.z,
                },
                "rotation": {
                    "x": obj.transform.rotation.x,
                    "y": obj.transform.rotation.y,
                    "z": obj.transform.rotation.z,
                },
                "scale": {
                    "x": obj.transform.scale.x,
                    "y": obj.transform.scale.y,
                    "z": obj.transform.scale.z,
                },
            },
            "parent_id": obj.parent_id,
            "visible": obj.visible,
            "enabled": obj.enabled,
            "metadata": {
                "created_at": _serialize_datetime(obj.metadata.created_at),
                "updated_at": _serialize_datetime(obj.metadata.updated_at),
            },
            "custom_data": obj.custom_data,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Scene:
        """Deserialize a scene from a dictionary.

        Args:
            data: Dictionary containing scene data.

        Returns:
            Deserialized Scene instance.

        Raises:
            SceneSerializationError: If data is malformed.
        """
        if not isinstance(data, dict):
            raise SceneSerializationError("Scene data must be a dictionary")

        if "id" not in data:
            raise SceneSerializationError("Missing required field: id")

        try:
            return Scene.model_validate(data)
        except Exception as e:
            raise SceneSerializationError(f"Invalid scene data: {e}") from e

    @staticmethod
    def to_json(scene: Scene, indent: int | None = 2) -> str:
        """Serialize a scene to JSON string.

        Args:
            scene: The scene to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            SceneSerializer.serialize(scene),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Scene:
        """Deserialize a scene from JSON string.

        Args:
            json_str: JSON string containing scene data.

        Returns:
            Deserialized Scene instance.

        Raises:
            SceneSerializationError: If JSON is invalid or scene data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise SceneSerializationError(f"Invalid JSON: {e}") from e

        return SceneSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
