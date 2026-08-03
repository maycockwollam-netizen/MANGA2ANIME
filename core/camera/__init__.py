"""Core Camera Module.

This module provides the camera data model for Manga2Anime.
It defines camera state, projection, and framing configuration.
Does NOT handle rendering or GPU interaction.
"""

from core.camera.camera import (
    Camera,
    CameraMetadata,
    CameraReferences,
    CameraState,
    CameraTransform,
    Framing,
    OrthographicProjection,
    PerspectiveProjection,
    Projection,
    ProjectionType,
    Viewport,
)
from core.camera.collection import CameraCollection
from core.camera.exceptions import (
    CameraDuplicateIDError,
    CameraError,
    CameraNotFoundError,
    CameraProjectionError,
    CameraReferenceError,
    CameraSerializationError,
    CameraValidationError,
)
from core.camera.serialization import CameraSerializer

__all__ = [
    # Models
    "Camera",
    "CameraMetadata",
    "CameraState",
    "CameraTransform",
    "CameraReferences",
    "Projection",
    "ProjectionType",
    "OrthographicProjection",
    "PerspectiveProjection",
    "Viewport",
    "Framing",
    # Collection
    "CameraCollection",
    # Serializer
    "CameraSerializer",
    # Exceptions
    "CameraError",
    "CameraValidationError",
    "CameraNotFoundError",
    "CameraDuplicateIDError",
    "CameraProjectionError",
    "CameraSerializationError",
    "CameraReferenceError",
]
