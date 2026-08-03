"""Core Scene Module.

This module provides the foundation for representing scenes in Manga2Anime.
It handles scene structure, objects, transforms, and hierarchy.
"""

from core.scene.exceptions import (
    SceneDuplicateIDError,
    SceneError,
    SceneHierarchyError,
    SceneNotFoundError,
    SceneObjectError,
    SceneSerializationError,
    SceneValidationError,
)
from core.scene.object import ObjectMetadata, SceneObject
from core.scene.scene import Scene, SceneMetadata, SceneSettings
from core.scene.serialization import SceneSerializer
from core.scene.transform import EulerRotation, Transform, Vector2, Vector3

__all__ = [
    # Models
    "Scene",
    "SceneMetadata",
    "SceneSettings",
    "SceneObject",
    "ObjectMetadata",
    "Transform",
    "Vector2",
    "Vector3",
    "EulerRotation",
    # Serializer
    "SceneSerializer",
    # Exceptions
    "SceneError",
    "SceneValidationError",
    "SceneObjectError",
    "SceneHierarchyError",
    "SceneSerializationError",
    "SceneNotFoundError",
    "SceneDuplicateIDError",
]
