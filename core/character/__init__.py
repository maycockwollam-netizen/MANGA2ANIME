"""Core Character Module.

This module provides the character data model for Manga2Anime.
It defines what a character is without handling rendering, animation,
AI, or asset loading.
"""

from core.character.appearance import CharacterAppearance
from core.character.character import (
    Character,
    CharacterMetadata,
    CharacterProperties,
    CharacterReferences,
    CharacterState,
)
from core.character.collection import CharacterCollection
from core.character.exceptions import (
    CharacterDuplicateIDError,
    CharacterError,
    CharacterNotFoundError,
    CharacterReferenceError,
    CharacterSerializationError,
    CharacterValidationError,
)
from core.character.serialization import CharacterSerializer

__all__ = [
    # Models
    "Character",
    "CharacterMetadata",
    "CharacterProperties",
    "CharacterState",
    "CharacterReferences",
    "CharacterAppearance",
    # Collection
    "CharacterCollection",
    # Serializer
    "CharacterSerializer",
    # Exceptions
    "CharacterError",
    "CharacterValidationError",
    "CharacterNotFoundError",
    "CharacterDuplicateIDError",
    "CharacterSerializationError",
    "CharacterReferenceError",
]
