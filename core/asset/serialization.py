"""Asset serialization and deserialization."""

import json
from datetime import UTC, datetime
from typing import Any

from core.asset.asset import Asset
from core.asset.exceptions import AssetSerializationError


class AssetSerializer:
    """Handles asset serialization to and from JSON."""

    @staticmethod
    def serialize(asset: Asset) -> dict[str, Any]:
        """Serialize an asset to a dictionary.

        Args:
            asset: The asset to serialize.

        Returns:
            Dictionary representation of the asset.
        """
        return {
            "id": asset.id,
            "name": asset.name,
            "asset_type": asset.asset_type.value,
            "metadata": {
                "name": asset.metadata.name,
                "display_name": asset.metadata.display_name,
                "description": asset.metadata.description,
                "tags": list(asset.metadata.tags),
                "author": asset.metadata.author,
                "source": asset.metadata.source,
                "license": asset.metadata.license,
                "notes": asset.metadata.notes,
                "created_at": _serialize_datetime(asset.metadata.created_at),
                "updated_at": _serialize_datetime(asset.metadata.updated_at),
                "custom_metadata": asset.metadata.custom_metadata,
            },
            "reference": {
                "path": asset.reference.path,
                "uri": asset.reference.uri,
                "mime_type": asset.reference.mime_type,
                "extension": asset.reference.extension,
                "checksum": asset.reference.checksum,
                "size_bytes": asset.reference.size_bytes,
            },
            "properties": {
                "width": asset.properties.width,
                "height": asset.properties.height,
                "duration": asset.properties.duration,
                "frame_count": asset.properties.frame_count,
                "sample_rate": asset.properties.sample_rate,
                "channels": asset.properties.channels,
                "bit_rate": asset.properties.bit_rate,
                "format": asset.properties.format,
                "codec": asset.properties.codec,
                "color_space": asset.properties.color_space,
                "custom_attributes": asset.properties.custom_attributes,
            },
            "state": {
                "enabled": asset.state.enabled,
                "available": asset.state.available,
                "verified": asset.state.verified,
                "custom_state": asset.state.custom_state,
            },
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Asset:
        """Deserialize an asset from a dictionary.

        Args:
            data: Dictionary containing asset data.

        Returns:
            Deserialized Asset instance.

        Raises:
            AssetSerializationError: If data is malformed.
        """
        if not isinstance(data, dict):
            raise AssetSerializationError("Asset data must be a dictionary")

        if "id" not in data:
            raise AssetSerializationError("Missing required field: id")

        try:
            return Asset.model_validate(data)
        except Exception as e:
            raise AssetSerializationError(f"Invalid asset data: {e}") from e

    @staticmethod
    def to_json(asset: Asset, indent: int | None = 2) -> str:
        """Serialize an asset to JSON string.

        Args:
            asset: The asset to serialize.
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(
            AssetSerializer.serialize(asset),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Asset:
        """Deserialize an asset from JSON string.

        Args:
            json_str: JSON string containing asset data.

        Returns:
            Deserialized Asset instance.

        Raises:
            AssetSerializationError: If JSON is invalid or asset data is malformed.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise AssetSerializationError(f"Invalid JSON: {e}") from e

        return AssetSerializer.deserialize(data)


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
