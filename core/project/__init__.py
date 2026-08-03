"""Core Project Module.

This module provides the foundation for representing, creating, saving,
loading, validating and versioning a Manga2Anime project.
"""

from core.project.exceptions import (
    ProjectError,
    ProjectFormatError,
    ProjectLoadError,
    ProjectSaveError,
    ProjectValidationError,
    ProjectVersionError,
)
from core.project.model import (
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    Project,
    ProjectMetadata,
    ProjectSettings,
    ProjectState,
)
from core.project.repository import ProjectRepository
from core.project.serialization import ProjectSerializer
from core.project.validator import ProjectValidator

__all__ = [
    # Models
    "Project",
    "ProjectMetadata",
    "ProjectSettings",
    "ProjectState",
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    # Repository
    "ProjectRepository",
    # Validator
    "ProjectValidator",
    # Serializer
    "ProjectSerializer",
    # Exceptions
    "ProjectError",
    "ProjectValidationError",
    "ProjectLoadError",
    "ProjectSaveError",
    "ProjectFormatError",
    "ProjectVersionError",
]
