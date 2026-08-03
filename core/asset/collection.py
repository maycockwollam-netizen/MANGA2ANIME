"""Asset collection and registry."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from core.asset.types import AssetType

if TYPE_CHECKING:
    from core.asset.asset import Asset


class AssetCollection:
    """Lightweight collection/registry for assets.

    Provides basic CRUD operations for managing multiple assets.
    Must be explicitly instantiated - not a singleton.
    """

    def __init__(self) -> None:
        """Initialize an empty collection."""
        self._assets: dict[str, Asset] = {}

    def add(self, asset: Asset) -> Asset:
        """Add an asset to the collection.

        Args:
            asset: Asset to add.

        Returns:
            The added asset.

        Raises:
            AssetDuplicateIDError: If asset ID already exists.
            AssetValidationError: If asset is invalid.
        """
        from core.asset.exceptions import (
            AssetDuplicateIDError,
            AssetValidationError,
        )

        if asset.id in self._assets:
            raise AssetDuplicateIDError(
                f"Asset with ID '{asset.id}' already exists"
            )

        # Validate before adding
        errors = asset.validate()
        if errors:
            raise AssetValidationError(
                "Asset validation failed", errors=errors
            )

        self._assets[asset.id] = asset
        return asset

    def remove(self, asset_id: str) -> Asset:
        """Remove an asset from the collection.

        Args:
            asset_id: ID of asset to remove.

        Returns:
            The removed asset.

        Raises:
            AssetNotFoundError: If asset not found.
        """
        from core.asset.exceptions import AssetNotFoundError

        if asset_id not in self._assets:
            raise AssetNotFoundError(f"Asset '{asset_id}' not found")

        return self._assets.pop(asset_id)

    def get(self, asset_id: str) -> Asset:
        """Get an asset by ID.

        Args:
            asset_id: ID of asset to get.

        Returns:
            The asset.

        Raises:
            AssetNotFoundError: If asset not found.
        """
        from core.asset.exceptions import AssetNotFoundError

        if asset_id not in self._assets:
            raise AssetNotFoundError(f"Asset '{asset_id}' not found")
        return self._assets[asset_id]

    def has(self, asset_id: str) -> bool:
        """Check if asset exists in collection.

        Args:
            asset_id: ID to check.

        Returns:
            True if asset exists, False otherwise.
        """
        return asset_id in self._assets

    def list(self) -> list[Asset]:
        """List all assets.

        Returns:
            List of assets sorted by name.
        """
        return sorted(self._assets.values(), key=lambda a: a.name)

    def list_by_type(self, asset_type: AssetType) -> list[Asset]:
        """List assets of a specific type.

        Args:
            asset_type: Asset type to filter by.

        Returns:
            List of assets with the specified type.
        """
        return [a for a in self._assets.values() if a.asset_type == asset_type]

    def list_by_tag(self, tag: str) -> list[Asset]:
        """List assets with a specific tag.

        Args:
            tag: Tag to filter by.

        Returns:
            List of assets with the tag.
        """
        return [a for a in self._assets.values() if a.has_tag(tag)]

    def find_by_name(self, name: str) -> Asset | None:
        """Find an asset by exact name match.

        Args:
            name: Name to search for.

        Returns:
            Asset if found, None otherwise.
        """
        for asset in self._assets.values():
            if asset.name == name:
                return asset
        return None

    def find_by_display_name(self, display_name: str) -> Asset | None:
        """Find an asset by exact display name match.

        Args:
            display_name: Display name to search for.

        Returns:
            Asset if found, None otherwise.
        """
        for asset in self._assets.values():
            if asset.metadata.display_name == display_name:
                return asset
        return None

    def get_available(self) -> list[Asset]:
        """Get all available assets.

        Returns:
            List of available assets.
        """
        return [a for a in self._assets.values() if a.state.available]

    def get_verified(self) -> list[Asset]:
        """Get all verified assets.

        Returns:
            List of verified assets.
        """
        return [a for a in self._assets.values() if a.state.verified]

    def count(self) -> int:
        """Get the number of assets.

        Returns:
            Number of assets in collection.
        """
        return len(self._assets)

    def clear(self) -> None:
        """Remove all assets from the collection."""
        self._assets.clear()

    def update(self, asset_id: str, **kwargs: str) -> Asset:
        """Update an asset's properties.

        Args:
            asset_id: ID of asset to update.
            **kwargs: Properties to update (name, display_name).

        Returns:
            The updated asset.

        Raises:
            AssetNotFoundError: If asset not found.
        """
        asset = self.get(asset_id)

        for key, value in kwargs.items():
            if key == "name":
                asset.update_name(value)
            elif key == "display_name":
                asset.update_display_name(value)

        return asset

    def validate_all(self) -> list[tuple[str, list[str]]]:
        """Validate all assets in collection.

        Returns:
            List of tuples containing (asset_id, errors).
        """
        results: list[tuple[str, list[str]]] = []
        for asset_id, asset in self._assets.items():
            errors = asset.validate()
            if errors:
                results.append((asset_id, errors))
        return results

    def get_invalid_assets(self) -> list[tuple[str, list[str]]]:
        """Get all invalid assets.

        Returns:
            List of tuples containing (asset_id, errors).
        """
        return self.validate_all()

    def __len__(self) -> int:
        """Get collection length."""
        return len(self._assets)

    def __contains__(self, asset_id: str) -> bool:
        """Check if asset ID is in collection."""
        return asset_id in self._assets

    def __iter__(self) -> Iterator[Asset]:
        """Iterate over assets."""
        return iter(sorted(self._assets.values(), key=lambda a: a.name))

    def __getitem__(self, asset_id: str) -> Asset:
        """Get asset by ID using bracket notation.

        Raises:
            AssetNotFoundError: If asset not found.
        """
        return self.get(asset_id)
