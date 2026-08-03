"""Timeline serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.timeline.exceptions import TimelineSerializationError
from core.timeline.timeline import Timeline


class TimelineSerializer:
    """Handles timeline serialization to and from JSON."""

    @staticmethod
    def serialize(timeline: Timeline) -> dict[str, Any]:
        """Serialize a timeline to a dictionary.

        Args:
            timeline: The timeline to serialize.

        Returns:
            Dictionary representation of the timeline.
        """
        return {
            "id": timeline.id,
            "metadata": {
                "name": timeline.metadata.name,
                "description": timeline.metadata.description,
                "created_at": _serialize_datetime(timeline.metadata.created_at),
                "updated_at": _serialize_datetime(timeline.metadata.updated_at),
            },
            "settings": {
                "frame_rate": timeline.settings.frame_rate,
                "duration": timeline.settings.duration,
            },
            "tracks": {
                track_id: TimelineSerializer._serialize_track(track)
                for track_id, track in timeline.tracks.items()
            },
        }

    @staticmethod
    def _serialize_track(track: Any) -> dict[str, Any]:
        """Serialize a track."""
        return {
            "id": track.id,
            "name": track.name,
            "target_id": track.target_id,
            "property_name": track.property_name,
            "keyframes": [
                {
                    "time": kf.time,
                    "value": kf.value,
                    "interpolation": kf.interpolation.value,
                    "metadata": kf.metadata,
                }
                for kf in track.keyframes
            ],
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Timeline:
        """Deserialize a timeline from a dictionary.

        Args:
            data: Dictionary containing timeline data.

        Returns:
            Deserialized Timeline instance.

        Raises:
            TimelineSerializationError: If data is malformed.
        """
        if not isinstance(data, dict):
            raise TimelineSerializationError("Timeline data must be a dictionary")

        if "id" not in data:
            raise TimelineSerializationError("Missing required field: id")

        try:
            return Timeline.model_validate(data)
        except Exception as e:
            raise TimelineSerializationError(f"Invalid timeline data: {e}") from e

    @staticmethod
    def to_json(timeline: Timeline, indent: int | None = 2) -> str:
        """Serialize a timeline to JSON string.

        Args:
            timeline: The timeline to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            TimelineSerializer.serialize(timeline),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Timeline:
        """Deserialize a timeline from JSON string.

        Args:
            json_str: JSON string containing timeline data.

        Returns:
            Deserialized Timeline instance.

        Raises:
            TimelineSerializationError: If JSON is invalid or timeline data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise TimelineSerializationError(f"Invalid JSON: {e}") from e

        return TimelineSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
