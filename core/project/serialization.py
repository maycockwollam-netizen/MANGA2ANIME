"""Project serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.project.exceptions import ProjectFormatError
from core.project.model import Project


class ProjectSerializer:
    """Handles project serialization to and from JSON."""

    @staticmethod
    def serialize(project: Project) -> dict[str, Any]:
        """Serialize a project to a dictionary.

        Args:
            project: The project to serialize.

        Returns:
            Dictionary representation of the project.
        """
        return {
            "id": project.id,
            "version": project.version,
            "metadata": {
                "name": project.metadata.name,
                "description": project.metadata.description,
                "author": project.metadata.author,
                "tags": project.metadata.tags,
                "created_at": _serialize_datetime(project.metadata.created_at),
                "updated_at": _serialize_datetime(project.metadata.updated_at),
            },
            "settings": {
                "resolution_width": project.settings.resolution_width,
                "resolution_height": project.settings.resolution_height,
                "frame_rate": project.settings.frame_rate,
                "audio_sample_rate": project.settings.audio_sample_rate,
                "default_duration_seconds": project.settings.default_duration_seconds,
            },
            "state": {
                "status": project.state.status,
                "scenes": project.state.scenes,
                "assets": project.state.assets,
            },
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Project:
        """Deserialize a project from a dictionary.

        Args:
            data: Dictionary containing project data.

        Returns:
            Deserialized Project instance.

        Raises:
            ProjectFormatError: If data is malformed or missing required fields.
        """
        if not isinstance(data, dict):
            raise ProjectFormatError("Project data must be a dictionary")

        if "id" not in data:
            raise ProjectFormatError("Missing required field: id")

        if "version" not in data:
            raise ProjectFormatError("Missing required field: version")

        try:
            return Project.from_dict(data)
        except Exception as e:
            raise ProjectFormatError(f"Invalid project data: {e}") from e

    @staticmethod
    def to_json(project: Project, indent: int | None = 2) -> str:
        """Serialize a project to JSON string.

        Args:
            project: The project to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            ProjectSerializer.serialize(project),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Project:
        """Deserialize a project from JSON string.

        Args:
            json_str: JSON string containing project data.

        Returns:
            Deserialized Project instance.

        Raises:
            ProjectFormatError: If JSON is invalid or project data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ProjectFormatError(f"Invalid JSON: {e}") from e

        return ProjectSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize datetime from ISO format string."""
    return datetime.fromisoformat(dt_str)
