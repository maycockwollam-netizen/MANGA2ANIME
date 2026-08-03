"""Character collection and registry."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.character.character import Character


class CharacterCollection:
    """Lightweight collection/registry for characters.

    Provides basic CRUD operations for managing multiple characters.
    Must be explicitly instantiated - not a singleton.
    """

    def __init__(self) -> None:
        """Initialize an empty collection."""
        self._characters: dict[str, Character] = {}

    def add(self, character: Character) -> Character:
        """Add a character to the collection.

        Args:
            character: Character to add.

        Returns:
            The added character.

        Raises:
            CharacterDuplicateIDError: If character ID already exists.
            CharacterValidationError: If character is invalid.
        """
        from core.character.exceptions import (
            CharacterDuplicateIDError,
            CharacterValidationError,
        )

        if character.id in self._characters:
            raise CharacterDuplicateIDError(
                f"Character with ID '{character.id}' already exists"
            )

        # Validate before adding
        errors = character.validate()
        if errors:
            raise CharacterValidationError(
                "Character validation failed", errors=errors
            )

        self._characters[character.id] = character
        return character

    def remove(self, character_id: str) -> Character:
        """Remove a character from the collection.

        Args:
            character_id: ID of character to remove.

        Returns:
            The removed character.

        Raises:
            CharacterNotFoundError: If character not found.
        """
        from core.character.exceptions import CharacterNotFoundError

        if character_id not in self._characters:
            raise CharacterNotFoundError(f"Character '{character_id}' not found")

        return self._characters.pop(character_id)

    def get(self, character_id: str) -> Character:
        """Get a character by ID.

        Args:
            character_id: ID of character to get.

        Returns:
            The character.

        Raises:
            CharacterNotFoundError: If character not found.
        """
        from core.character.exceptions import CharacterNotFoundError

        if character_id not in self._characters:
            raise CharacterNotFoundError(f"Character '{character_id}' not found")
        return self._characters[character_id]

    def has(self, character_id: str) -> bool:
        """Check if character exists in collection.

        Args:
            character_id: ID to check.

        Returns:
            True if character exists, False otherwise.
        """
        return character_id in self._characters

    def list(self) -> list[Character]:
        """List all characters.

        Returns:
            List of characters sorted by name.
        """
        return sorted(self._characters.values(), key=lambda c: c.name)

    def list_by_tag(self, tag: str) -> list[Character]:
        """List characters with a specific tag.

        Args:
            tag: Tag to filter by.

        Returns:
            List of characters with the tag.
        """
        return [c for c in self._characters.values() if c.has_tag(tag)]

    def find_by_name(self, name: str) -> Character | None:
        """Find a character by exact name match.

        Args:
            name: Name to search for.

        Returns:
            Character if found, None otherwise.
        """
        for character in self._characters.values():
            if character.name == name:
                return character
        return None

    def find_by_display_name(self, display_name: str) -> Character | None:
        """Find a character by exact display name match.

        Args:
            display_name: Display name to search for.

        Returns:
            Character if found, None otherwise.
        """
        for character in self._characters.values():
            if character.display_name == display_name:
                return character
        return None

    def count(self) -> int:
        """Get the number of characters.

        Returns:
            Number of characters in collection.
        """
        return len(self._characters)

    def clear(self) -> None:
        """Remove all characters from the collection."""
        self._characters.clear()

    def update(self, character_id: str, **kwargs: str) -> Character:
        """Update a character's properties.

        Args:
            character_id: ID of character to update.
            **kwargs: Properties to update (name, display_name).

        Returns:
            The updated character.

        Raises:
            CharacterNotFoundError: If character not found.
        """
        character = self.get(character_id)

        for key, value in kwargs.items():
            if key == "name":
                character.update_name(value)
            elif key == "display_name":
                character.update_display_name(value)

        return character

    def validate_all(self) -> list[tuple[str, list[str]]]:
        """Validate all characters in collection.

        Returns:
            List of tuples containing (character_id, errors).
        """
        results: list[tuple[str, list[str]]] = []
        for character_id, character in self._characters.items():
            errors = character.validate()
            if errors:
                results.append((character_id, errors))
        return results

    def get_invalid_characters(self) -> list[tuple[str, list[str]]]:
        """Get all invalid characters.

        Returns:
            List of tuples containing (character_id, errors).
        """
        return self.validate_all()

    def __len__(self) -> int:
        """Get collection length."""
        return len(self._characters)

    def __contains__(self, character_id: str) -> bool:
        """Check if character ID is in collection."""
        return character_id in self._characters

    def __iter__(self) -> Iterator[Character]:
        """Iterate over characters."""
        return iter(sorted(self._characters.values(), key=lambda c: c.name))

    def __getitem__(self, character_id: str) -> Character:
        """Get character by ID using bracket notation.

        Raises:
            CharacterNotFoundError: If character not found.
        """
        return self.get(character_id)
