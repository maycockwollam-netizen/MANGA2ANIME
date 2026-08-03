"""Core Asset Module.

This module provides the asset data model for Manga2Anime.
It defines asset identity, metadata, types, references, properties,
and state. Does NOT load, decode, render, or process assets.
"""

from core.asset.asset import Asset
from core.asset.collection import AssetCollection
from core.asset.exceptions import (
    AssetDuplicateIDError,
    AssetError,
    AssetNotFoundError,
    AssetReferenceError,
    AssetSerializationError,
    AssetTypeError,
    AssetValidationError,
)
from core.asset.metadata import AssetMetadata
from core.asset.properties import AssetProperties
from core.asset.reference import AssetReference
from core.asset.serialization import AssetSerializer
from core.asset.state import AssetState
from core.asset.types import AssetType
from core.asset.validator import AssetValidator

__all__ = [
    # Models
    "Asset",
    "AssetMetadata",
    "AssetReference",
    "AssetProperties",
    "AssetState",
    "AssetType",
    # Validator
    "AssetValidator",
    # Collection
    "AssetCollection",
    # Serializer
    "AssetSerializer",
    # Exceptions
    "AssetError",
    "AssetValidationError",
    "AssetNotFoundError",
    "AssetDuplicateIDError",
    "AssetSerializationError",
    "AssetReferenceError",
    "AssetTypeError",
]
