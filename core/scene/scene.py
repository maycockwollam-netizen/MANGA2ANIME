"""Scene model and scene management."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.scene.exceptions import (
    SceneDuplicateIDError,
    SceneHierarchyError,
    SceneNotFoundError,
    SceneValidationError,
)
from core.scene.object import SceneObject


class SceneMetadata(BaseModel):
    """Metadata for a scene."""

    name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SceneSettings(BaseModel):
    """Settings for a scene."""

    background_color: str = Field(default="#000000")
    ambient_light: float = Field(default=0.5, ge=0.0, le=1.0)


class Scene(BaseModel):
    """Scene model representing a collection of scene objects."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    metadata: SceneMetadata = Field(default_factory=SceneMetadata)
    settings: SceneSettings = Field(default_factory=SceneSettings)
    objects: dict[str, SceneObject] = Field(default_factory=dict)

    def model_post_init(self, _info: Any) -> None:
        """Validate scene state."""
        errors = self._validate_hierarchy()
        if errors:
            raise ValueError(f"Invalid scene hierarchy: {errors}")

    def add_object(self, obj: SceneObject) -> SceneObject:
        """Add an object to the scene.

        Args:
            obj: SceneObject to add.

        Returns:
            The added object.

        Raises:
            SceneDuplicateIDError: If object ID already exists.
            SceneHierarchyError: If parent ID is invalid.
        """
        if obj.id in self.objects:
            raise SceneDuplicateIDError(f"Object with ID '{obj.id}' already exists")

        if obj.parent_id is not None and obj.parent_id not in self.objects:
            raise SceneHierarchyError(f"Parent object '{obj.parent_id}' not found")

        if obj.parent_id == obj.id:
            raise SceneHierarchyError("Object cannot be its own parent")

        self.objects[obj.id] = obj
        self._update_timestamp()
        return obj

    def remove_object(self, object_id: str, cascade: bool = False) -> None:
        """Remove an object from the scene.

        Args:
            object_id: ID of object to remove.
            cascade: If True, remove children recursively.

        Raises:
            SceneNotFoundError: If object not found.
        """
        if object_id not in self.objects:
            raise SceneNotFoundError(f"Object '{object_id}' not found")

        children = self._get_children(object_id)

        if cascade:
            for child_id in children:
                del self.objects[child_id]
        else:
            for child_id in children:
                self.objects[child_id].parent_id = None

        del self.objects[object_id]
        self._update_timestamp()

    def get_object(self, object_id: str) -> SceneObject:
        """Get an object by ID.

        Args:
            object_id: ID of object to get.

        Returns:
            The scene object.

        Raises:
            SceneNotFoundError: If object not found.
        """
        if object_id not in self.objects:
            raise SceneNotFoundError(f"Object '{object_id}' not found")
        return self.objects[object_id]

    def has_object(self, object_id: str) -> bool:
        """Check if scene contains an object.

        Args:
            object_id: ID to check.

        Returns:
            True if object exists, False otherwise.
        """
        return object_id in self.objects

    def update_object(self, object_id: str, **kwargs: Any) -> SceneObject:
        """Update an object's properties.

        Args:
            object_id: ID of object to update.
            **kwargs: Properties to update.

        Returns:
            The updated object.

        Raises:
            SceneNotFoundError: If object not found.
        """
        obj = self.get_object(object_id)

        for key, value in kwargs.items():
            if hasattr(obj, key) and key != "id":
                setattr(obj, key, value)

        obj.metadata.updated_at = datetime.now(UTC)
        self._update_timestamp()
        return obj

    def set_parent(self, object_id: str, parent_id: str | None) -> SceneObject:
        """Set the parent of an object.

        Args:
            object_id: ID of object to reparent.
            parent_id: New parent ID, or None to remove parent.

        Returns:
            The updated object.

        Raises:
            SceneNotFoundError: If object not found.
            SceneHierarchyError: If parent is invalid.
        """
        obj = self.get_object(object_id)

        if parent_id is not None:
            if parent_id not in self.objects:
                raise SceneHierarchyError(f"Parent object '{parent_id}' not found")
            if parent_id == object_id:
                raise SceneHierarchyError("Object cannot be its own parent")
            if self._would_create_cycle(object_id, parent_id):
                raise SceneHierarchyError("Would create circular hierarchy")

        obj.set_parent(parent_id)
        self._update_timestamp()
        return obj

    def get_children(self, object_id: str) -> list[SceneObject]:
        """Get direct children of an object.

        Args:
            object_id: ID of parent object.

        Returns:
            List of child objects.
        """
        return self._get_children(object_id)

    def get_root_objects(self) -> list[SceneObject]:
        """Get all objects without a parent.

        Returns:
            List of root-level objects.
        """
        return [obj for obj in self.objects.values() if obj.parent_id is None]

    def get_hierarchy_tree(self) -> dict[str, Any]:
        """Get the scene hierarchy as a tree structure.

        Returns:
            Dictionary representing the hierarchy.
        """
        roots = self.get_root_objects()
        return {
            "id": self.id,
            "name": self.metadata.name,
            "children": [self._build_subtree(obj.id) for obj in roots],
        }

    def _get_children(self, object_id: str) -> list[str]:
        """Get IDs of direct children."""
        return [obj.id for obj in self.objects.values() if obj.parent_id == object_id]

    def _would_create_cycle(self, object_id: str, new_parent_id: str | None) -> bool:
        """Check if setting new parent would create a cycle."""
        if new_parent_id is None:
            return False

        current = new_parent_id
        visited = {object_id}

        while current is not None:
            if current in visited:
                return True
            visited.add(current)
            if current not in self.objects:
                break
            current = self.objects[current].parent_id

        return False

    def _build_subtree(self, object_id: str) -> dict[str, Any]:
        """Build subtree dictionary for hierarchy tree."""
        obj = self.objects[object_id]
        children = self._get_children(object_id)
        return {
            "id": obj.id,
            "name": obj.name,
            "type": obj.object_type,
            "children": [self._build_subtree(child_id) for child_id in children],
        }

    def _update_timestamp(self) -> None:
        """Update scene metadata timestamp."""
        self.metadata.updated_at = datetime.now(UTC)

    def _validate_hierarchy(self) -> list[str]:
        """Validate the entire hierarchy.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        # Check for self-parenting
        for obj in self.objects.values():
            if obj.parent_id == obj.id:
                errors.append(f"Object '{obj.id}' is its own parent")

        # Check for dangling parent references
        for obj in self.objects.values():
            if obj.parent_id is not None and obj.parent_id not in self.objects:
                errors.append(f"Object '{obj.id}' has invalid parent '{obj.parent_id}'")

        # Check for cycles (only for objects with valid parents)
        for obj_id in self.objects:
            obj = self.objects[obj_id]
            if obj.parent_id is not None and obj.parent_id in self.objects:
                if self._would_create_cycle(obj_id, obj.parent_id):
                    errors.append(f"Circular hierarchy detected starting from '{obj_id}'")

        return errors

    def validate(self) -> list[str]:
        """Validate the scene.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Scene ID is required")

        if len(self.metadata.name) > 255:
            errors.append("Scene name must be 255 characters or less")

        errors.extend(self._validate_hierarchy())

        for obj in self.objects.values():
            if not obj.name:
                errors.append(f"Object '{obj.id}' has empty name")

        return errors

    def validate_or_raise(self) -> None:
        """Validate the scene and raise if invalid.

        Raises:
            SceneValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise SceneValidationError("Scene validation failed", errors=errors)
