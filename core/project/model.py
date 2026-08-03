"""Project data models."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

SUPPORTED_VERSIONS = ["0.1.0"]
CURRENT_VERSION = "0.1.0"


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class ProjectMetadata(BaseModel):
    """Metadata for a manga2anime project."""

    name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=2000)
    author: str = Field(default="", max_length=255)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ProjectSettings(BaseModel):
    """Settings for a manga2anime project."""

    resolution_width: int = Field(default=1280, ge=640, le=3840)
    resolution_height: int = Field(default=720, ge=360, le=2160)
    frame_rate: int = Field(default=24, ge=12, le=120)
    audio_sample_rate: int = Field(default=48000, ge=16000, le=96000)
    default_duration_seconds: float = Field(default=3.0, ge=0.1, le=60.0)

    def model_post_init(self, _info: Any) -> None:
        """Validate resolution dimensions are even."""
        if self.resolution_width % 2 != 0:
            raise ValueError("resolution_width must be divisible by 2")
        if self.resolution_height % 2 != 0:
            raise ValueError("resolution_height must be divisible by 2")


class ProjectState(BaseModel):
    """State of a manga2anime project."""

    status: str = Field(default="created")
    scenes: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)


class Project(BaseModel):
    """Main project model for manga2anime."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    version: str = Field(default=CURRENT_VERSION)
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    state: ProjectState = Field(default_factory=ProjectState)

    def model_post_init(self, _info: Any) -> None:
        """Validate project version."""
        if self.version not in SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported project version: {self.version}. "
                f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Create a Project from a dictionary.

        Args:
            data: Dictionary containing project data.

        Returns:
            Project instance.
        """
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert project to dictionary.

        Returns:
            Dictionary representation.
        """
        return self.model_dump(mode="json")

    def update_metadata(self, **kwargs: Any) -> None:
        """Update project metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.metadata.updated_at = utcnow()

    def add_scene(self, scene_id: str) -> None:
        """Add a scene to the project."""
        if scene_id and scene_id not in self.state.scenes:
            self.state.scenes.append(scene_id)
            self.metadata.updated_at = utcnow()

    def remove_scene(self, scene_id: str) -> None:
        """Remove a scene from the project."""
        if scene_id in self.state.scenes:
            self.state.scenes.remove(scene_id)
            self.metadata.updated_at = utcnow()

    def add_asset(self, asset_id: str) -> None:
        """Add an asset to the project."""
        if asset_id and asset_id not in self.state.assets:
            self.state.assets.append(asset_id)
            self.metadata.updated_at = utcnow()

    def remove_asset(self, asset_id: str) -> None:
        """Remove an asset from the project."""
        if asset_id in self.state.assets:
            self.state.assets.remove(asset_id)
            self.metadata.updated_at = utcnow()
