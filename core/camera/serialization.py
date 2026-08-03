"""Camera serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.camera.camera import Camera
from core.camera.exceptions import CameraSerializationError


class CameraSerializer:
    """Handles camera serialization to and from JSON."""

    @staticmethod
    def serialize(camera: Camera) -> dict[str, Any]:
        """Serialize a camera to a dictionary.

        Args:
            camera: The camera to serialize.

        Returns:
            Dictionary representation of the camera.
        """
        return {
            "id": camera.id,
            "name": camera.name,
            "metadata": {
                "description": camera.metadata.description,
                "tags": list(camera.metadata.tags),
                "notes": camera.metadata.notes,
                "created_at": _serialize_datetime(camera.metadata.created_at),
                "updated_at": _serialize_datetime(camera.metadata.updated_at),
                "custom_metadata": camera.metadata.custom_metadata,
            },
            "transform": {
                "position_x": camera.transform.position_x,
                "position_y": camera.transform.position_y,
                "position_z": camera.transform.position_z,
                "rotation_x": camera.transform.rotation_x,
                "rotation_y": camera.transform.rotation_y,
                "rotation_z": camera.transform.rotation_z,
            },
            "projection": {
                "type": camera.projection.type.value,
                "orthographic": {
                    "size": camera.projection.orthographic.size,
                },
                "perspective": {
                    "field_of_view": camera.projection.perspective.field_of_view,
                    "near_clip": camera.projection.perspective.near_clip,
                    "far_clip": camera.projection.perspective.far_clip,
                },
            },
            "viewport": {
                "width": camera.viewport.width,
                "height": camera.viewport.height,
            },
            "framing": {
                "center_x": camera.framing.center_x,
                "center_y": camera.framing.center_y,
                "size_width": camera.framing.size_width,
                "size_height": camera.framing.size_height,
                "zoom": camera.framing.zoom,
                "margin_left": camera.framing.margin_left,
                "margin_right": camera.framing.margin_right,
                "margin_top": camera.framing.margin_top,
                "margin_bottom": camera.framing.margin_bottom,
            },
            "state": {
                "enabled": camera.state.enabled,
                "active": camera.state.active,
                "custom_state": camera.state.custom_state,
            },
            "references": {
                "scene_id": camera.references.scene_id,
                "target_id": camera.references.target_id,
                "custom_references": camera.references.custom_references,
            },
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Camera:
        """Deserialize a camera from a dictionary.

        Args:
            data: Dictionary containing camera data.

        Returns:
            Deserialized Camera instance.

        Raises:
            CameraSerializationError: If data is malformed.
        """
        if not isinstance(data, dict):
            raise CameraSerializationError("Camera data must be a dictionary")

        if "id" not in data:
            raise CameraSerializationError("Missing required field: id")

        try:
            return Camera.model_validate(data)
        except Exception as e:
            raise CameraSerializationError(f"Invalid camera data: {e}") from e

    @staticmethod
    def to_json(camera: Camera, indent: int | None = 2) -> str:
        """Serialize a camera to JSON string.

        Args:
            camera: The camera to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            CameraSerializer.serialize(camera),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Camera:
        """Deserialize a camera from JSON string.

        Args:
            json_str: JSON string containing camera data.

        Returns:
            Deserialized Camera instance.

        Raises:
            CameraSerializationError: If JSON is invalid or camera data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise CameraSerializationError(f"Invalid JSON: {e}") from e

        return CameraSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
