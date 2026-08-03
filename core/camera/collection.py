"""Camera collection and registry."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.camera.camera import Camera


class CameraCollection:
    """Lightweight collection/registry for cameras.

    Provides basic CRUD operations for managing multiple cameras.
    Must be explicitly instantiated - not a singleton.
    """

    def __init__(self) -> None:
        """Initialize an empty collection."""
        self._cameras: dict[str, Camera] = {}

    def add(self, camera: Camera) -> Camera:
        """Add a camera to the collection.

        Args:
            camera: Camera to add.

        Returns:
            The added camera.

        Raises:
            CameraDuplicateIDError: If camera ID already exists.
            CameraValidationError: If camera is invalid.
        """
        from core.camera.exceptions import (
            CameraDuplicateIDError,
            CameraValidationError,
        )

        if camera.id in self._cameras:
            raise CameraDuplicateIDError(
                f"Camera with ID '{camera.id}' already exists"
            )

        # Validate before adding
        errors = camera.validate()
        if errors:
            raise CameraValidationError(
                "Camera validation failed", errors=errors
            )

        self._cameras[camera.id] = camera
        return camera

    def remove(self, camera_id: str) -> Camera:
        """Remove a camera from the collection.

        Args:
            camera_id: ID of camera to remove.

        Returns:
            The removed camera.

        Raises:
            CameraNotFoundError: If camera not found.
        """
        from core.camera.exceptions import CameraNotFoundError

        if camera_id not in self._cameras:
            raise CameraNotFoundError(f"Camera '{camera_id}' not found")

        return self._cameras.pop(camera_id)

    def get(self, camera_id: str) -> Camera:
        """Get a camera by ID.

        Args:
            camera_id: ID of camera to get.

        Returns:
            The camera.

        Raises:
            CameraNotFoundError: If camera not found.
        """
        from core.camera.exceptions import CameraNotFoundError

        if camera_id not in self._cameras:
            raise CameraNotFoundError(f"Camera '{camera_id}' not found")
        return self._cameras[camera_id]

    def has(self, camera_id: str) -> bool:
        """Check if camera exists in collection.

        Args:
            camera_id: ID to check.

        Returns:
            True if camera exists, False otherwise.
        """
        return camera_id in self._cameras

    def list(self) -> list[Camera]:
        """List all cameras.

        Returns:
            List of cameras sorted by name.
        """
        return sorted(self._cameras.values(), key=lambda c: c.name)

    def list_by_tag(self, tag: str) -> list[Camera]:
        """List cameras with a specific tag.

        Args:
            tag: Tag to filter by.

        Returns:
            List of cameras with the tag.
        """
        return [c for c in self._cameras.values() if c.has_tag(tag)]

    def find_by_name(self, name: str) -> Camera | None:
        """Find a camera by exact name match.

        Args:
            name: Name to search for.

        Returns:
            Camera if found, None otherwise.
        """
        for camera in self._cameras.values():
            if camera.name == name:
                return camera
        return None

    def get_active(self) -> list[Camera]:
        """Get all active cameras.

        Returns:
            List of active cameras.
        """
        return [c for c in self._cameras.values() if c.state.active]

    def count(self) -> int:
        """Get the number of cameras.

        Returns:
            Number of cameras in collection.
        """
        return len(self._cameras)

    def clear(self) -> None:
        """Remove all cameras from the collection."""
        self._cameras.clear()

    def update(self, camera_id: str, **kwargs: str) -> Camera:
        """Update a camera's properties.

        Args:
            camera_id: ID of camera to update.
            **kwargs: Properties to update (name).

        Returns:
            The updated camera.

        Raises:
            CameraNotFoundError: If camera not found.
        """
        camera = self.get(camera_id)

        for key, value in kwargs.items():
            if key == "name":
                camera.update_name(value)

        return camera

    def validate_all(self) -> list[tuple[str, list[str]]]:
        """Validate all cameras in collection.

        Returns:
            List of tuples containing (camera_id, errors).
        """
        results: list[tuple[str, list[str]]] = []
        for camera_id, camera in self._cameras.items():
            errors = camera.validate()
            if errors:
                results.append((camera_id, errors))
        return results

    def get_invalid_cameras(self) -> list[tuple[str, list[str]]]:
        """Get all invalid cameras.

        Returns:
            List of tuples containing (camera_id, errors).
        """
        return self.validate_all()

    def __len__(self) -> int:
        """Get collection length."""
        return len(self._cameras)

    def __contains__(self, camera_id: str) -> bool:
        """Check if camera ID is in collection."""
        return camera_id in self._cameras

    def __iter__(self) -> Iterator[Camera]:
        """Iterate over cameras."""
        return iter(sorted(self._cameras.values(), key=lambda c: c.name))

    def __getitem__(self, camera_id: str) -> Camera:
        """Get camera by ID using bracket notation.

        Raises:
            CameraNotFoundError: If camera not found.
        """
        return self.get(camera_id)
