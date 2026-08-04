"""Registry for Core entities."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)


class Registry:
    """Generic registry for Core entities.

    Provides basic CRUD operations for managing entities by ID.
    Must be explicitly instantiated - not a singleton.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._entities: dict[str, T] = {}

    def register(self, entity: T) -> T:
        """Register an entity.

        Args:
            entity: Entity to register. Must have an `id` attribute.

        Returns:
            The registered entity.

        Raises:
            DuplicateRegistrationError: If entity ID already exists.
        """
        from integration.exceptions import DuplicateRegistrationError

        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            raise ValueError("Entity must have an 'id' attribute")

        if entity_id in self._entities:
            raise DuplicateRegistrationError(f"Entity with ID '{entity_id}' already exists")

        self._entities[entity_id] = entity
        return entity

    def unregister(self, entity_id: str) -> T:
        """Unregister an entity.

        Args:
            entity_id: ID of entity to unregister.

        Returns:
            The unregistered entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        from integration.exceptions import EntityNotFoundError

        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity with ID '{entity_id}' not found")

        return self._entities.pop(entity_id)

    def get(self, entity_id: str) -> T:
        """Get an entity by ID.

        Args:
            entity_id: ID of entity to get.

        Returns:
            The entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        from integration.exceptions import EntityNotFoundError

        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity with ID '{entity_id}' not found")
        return self._entities[entity_id]

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists.

        Args:
            entity_id: ID to check.

        Returns:
            True if entity exists, False otherwise.
        """
        return entity_id in self._entities

    def list(self) -> list[T]:
        """List all entities.

        Returns:
            List of all entities sorted by ID.
        """
        return sorted(self._entities.values(), key=lambda e: getattr(e, "id", ""))

    def count(self) -> int:
        """Get the number of entities.

        Returns:
            Number of entities in registry.
        """
        return len(self._entities)

    def clear(self) -> None:
        """Remove all entities from the registry."""
        self._entities.clear()

    def __len__(self) -> int:
        """Get registry length."""
        return len(self._entities)

    def __contains__(self, entity_id: str) -> bool:
        """Check if entity ID is in registry."""
        return entity_id in self._entities

    def __iter__(self) -> Iterator[T]:
        """Iterate over entities."""
        return iter(self.list())

    def __getitem__(self, entity_id: str) -> T:
        """Get entity by ID using bracket notation.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        return self.get(entity_id)
