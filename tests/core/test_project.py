"""Tests for core/project module."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.project import (
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    Project,
    ProjectFormatError,
    ProjectLoadError,
    ProjectMetadata,
    ProjectRepository,
    ProjectSaveError,
    ProjectSerializer,
    ProjectSettings,
    ProjectState,
    ProjectValidationError,
    ProjectValidator,
)


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class TestProjectMetadata:
    """Tests for ProjectMetadata model."""

    def test_create_metadata_with_defaults(self) -> None:
        """Test creating metadata with default values."""
        metadata = ProjectMetadata()
        assert metadata.name == ""
        assert metadata.description == ""
        assert metadata.author == ""
        assert metadata.tags == []
        assert metadata.created_at is not None
        assert metadata.updated_at is not None

    def test_create_metadata_with_values(self) -> None:
        """Test creating metadata with custom values."""
        now = utcnow()
        metadata = ProjectMetadata(
            name="Test Project",
            description="A test project",
            author="Test Author",
            tags=["anime", "manga"],
            created_at=now,
            updated_at=now,
        )
        assert metadata.name == "Test Project"
        assert metadata.description == "A test project"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["anime", "manga"]
        assert metadata.created_at == now
        assert metadata.updated_at == now

    def test_metadata_model_dump(self) -> None:
        """Test that metadata can be serialized."""
        metadata = ProjectMetadata(name="Test")
        data = metadata.model_dump()
        assert data["name"] == "Test"
        assert "created_at" in data
        assert "updated_at" in data


class TestProjectSettings:
    """Tests for ProjectSettings model."""

    def test_create_settings_with_defaults(self) -> None:
        """Test creating settings with default values."""
        settings = ProjectSettings()
        assert settings.resolution_width == 1280
        assert settings.resolution_height == 720
        assert settings.frame_rate == 24
        assert settings.audio_sample_rate == 48000
        assert settings.default_duration_seconds == 3.0

    def test_create_settings_custom_values(self) -> None:
        """Test creating settings with custom values."""
        settings = ProjectSettings(
            resolution_width=1920,
            resolution_height=1080,
            frame_rate=60,
        )
        assert settings.resolution_width == 1920
        assert settings.resolution_height == 1080
        assert settings.frame_rate == 60

    def test_invalid_resolution_odd_width(self) -> None:
        """Test that odd resolution width is rejected."""
        with pytest.raises(ValueError, match="divisible by 2"):
            ProjectSettings(resolution_width=1281)

    def test_invalid_resolution_odd_height(self) -> None:
        """Test that odd resolution height is rejected."""
        with pytest.raises(ValueError, match="divisible by 2"):
            ProjectSettings(resolution_height=721)

    def test_invalid_frame_rate_too_low(self) -> None:
        """Test that frame rate below minimum is rejected."""
        with pytest.raises(ValueError):
            ProjectSettings(frame_rate=5)

    def test_invalid_frame_rate_too_high(self) -> None:
        """Test that frame rate above maximum is rejected."""
        with pytest.raises(ValueError):
            ProjectSettings(frame_rate=200)


class TestProjectState:
    """Tests for ProjectState model."""

    def test_create_state_with_defaults(self) -> None:
        """Test creating state with default values."""
        state = ProjectState()
        assert state.status == "created"
        assert state.scenes == []
        assert state.assets == []

    def test_create_state_with_values(self) -> None:
        """Test creating state with custom values."""
        state = ProjectState(
            status="in_progress",
            scenes=["scene-1", "scene-2"],
            assets=["asset-1"],
        )
        assert state.status == "in_progress"
        assert state.scenes == ["scene-1", "scene-2"]
        assert state.assets == ["asset-1"]


class TestProject:
    """Tests for Project model."""

    def test_create_project_with_defaults(self) -> None:
        """Test creating project with default values."""
        project = Project()
        assert project.id is not None
        assert len(project.id) > 0
        assert project.version == CURRENT_VERSION
        assert isinstance(project.metadata, ProjectMetadata)
        assert isinstance(project.settings, ProjectSettings)
        assert isinstance(project.state, ProjectState)
        assert project.state.scenes == []
        assert project.state.assets == []

    def test_create_project_with_custom_values(self) -> None:
        """Test creating project with custom values."""
        project = Project(
            id="custom-id-123",
            metadata=ProjectMetadata(name="Custom Project"),
            settings=ProjectSettings(resolution_width=1920),
        )
        assert project.id == "custom-id-123"
        assert project.metadata.name == "Custom Project"
        assert project.settings.resolution_width == 1920

    def test_project_unique_id(self) -> None:
        """Test that each project gets a unique ID."""
        project1 = Project()
        project2 = Project()
        assert project1.id != project2.id

    def test_add_scene(self) -> None:
        """Test adding a scene to project."""
        project = Project()
        original_updated_at = project.metadata.updated_at

        project.add_scene("scene-1")
        assert "scene-1" in project.state.scenes
        assert project.metadata.updated_at >= original_updated_at

    def test_add_duplicate_scene(self) -> None:
        """Test adding duplicate scene doesn't duplicate."""
        project = Project()
        project.add_scene("scene-1")
        project.add_scene("scene-1")
        assert len(project.state.scenes) == 1

    def test_add_empty_scene_ignored(self) -> None:
        """Test adding empty scene ID is ignored."""
        project = Project()
        project.add_scene("")
        assert "" not in project.state.scenes

    def test_remove_scene(self) -> None:
        """Test removing a scene from project."""
        project = Project()
        project.add_scene("scene-1")
        project.remove_scene("scene-1")
        assert "scene-1" not in project.state.scenes

    def test_add_asset(self) -> None:
        """Test adding an asset to project."""
        project = Project()
        project.add_asset("asset-1")
        assert "asset-1" in project.state.assets

    def test_remove_asset(self) -> None:
        """Test removing an asset from project."""
        project = Project()
        project.add_asset("asset-1")
        project.remove_asset("asset-1")
        assert "asset-1" not in project.state.assets

    def test_update_metadata(self) -> None:
        """Test updating project metadata."""
        project = Project()
        project.update_metadata(name="Updated Name", description="New description")
        assert project.metadata.name == "Updated Name"
        assert project.metadata.description == "New description"


class TestProjectVersioning:
    """Tests for project versioning."""

    def test_current_version_is_supported(self) -> None:
        """Test that current version is in supported versions."""
        assert CURRENT_VERSION in SUPPORTED_VERSIONS

    def test_project_version_matches_current(self) -> None:
        """Test that new project uses current version."""
        project = Project()
        assert project.version == CURRENT_VERSION

    def test_invalid_version_rejected(self) -> None:
        """Test that invalid version is rejected."""
        with pytest.raises(ValueError, match="Unsupported project version"):
            Project(version="99.0.0")


class TestProjectSerializer:
    """Tests for ProjectSerializer."""

    def test_serialize_project(self) -> None:
        """Test serializing a project to dictionary."""
        project = Project(
            metadata=ProjectMetadata(name="Test"),
        )
        data = ProjectSerializer.serialize(project)

        assert data["id"] == project.id
        assert data["version"] == project.version
        assert data["metadata"]["name"] == "Test"
        assert data["state"]["scenes"] == []
        assert data["state"]["assets"] == []

    def test_deserialize_project(self) -> None:
        """Test deserializing a project from dictionary."""
        project = Project(metadata=ProjectMetadata(name="Test"))
        data = ProjectSerializer.serialize(project)

        restored = ProjectSerializer.deserialize(data)
        assert restored.id == project.id
        assert restored.metadata.name == "Test"

    def test_roundtrip_preservation(self) -> None:
        """Test that serialization roundtrip preserves all data."""
        original = Project(
            metadata=ProjectMetadata(
                name="Roundtrip Test",
                description="Testing serialization",
                author="Test Author",
                tags=["test", "serialization"],
            ),
            settings=ProjectSettings(
                resolution_width=1920,
                resolution_height=1080,
                frame_rate=30,
            ),
            state=ProjectState(
                status="in_progress",
                scenes=["scene-1", "scene-2"],
                assets=["asset-1"],
            ),
        )

        data = ProjectSerializer.serialize(original)
        restored = ProjectSerializer.deserialize(data)

        assert restored.id == original.id
        assert restored.version == original.version
        assert restored.metadata.name == original.metadata.name
        assert restored.metadata.description == original.metadata.description
        assert restored.metadata.tags == original.metadata.tags
        assert restored.settings.resolution_width == original.settings.resolution_width
        assert restored.settings.frame_rate == original.settings.frame_rate
        assert restored.state.status == original.state.status
        assert restored.state.scenes == original.state.scenes
        assert restored.state.assets == original.state.assets

    def test_to_json(self) -> None:
        """Test serializing project to JSON string."""
        project = Project(metadata=ProjectMetadata(name="JSON Test"))
        json_str = ProjectSerializer.to_json(project)

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "JSON Test"

    def test_from_json(self) -> None:
        """Test deserializing project from JSON string."""
        project = Project(metadata=ProjectMetadata(name="JSON Test"))
        json_str = ProjectSerializer.to_json(project)

        restored = ProjectSerializer.from_json(json_str)
        assert restored.metadata.name == "JSON Test"

    def test_deserialize_invalid_data(self) -> None:
        """Test that deserializing invalid data raises error."""
        with pytest.raises(ProjectFormatError, match="Missing required field"):
            ProjectSerializer.deserialize({"version": "invalid"})

    def test_from_invalid_json(self) -> None:
        """Test that from_json raises error for invalid JSON."""
        with pytest.raises(ProjectFormatError, match="Invalid JSON"):
            ProjectSerializer.from_json("not valid json {{{")


class TestProjectRepository:
    """Tests for ProjectRepository."""

    def test_save_and_load_project(self) -> None:
        """Test saving and loading a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Project(metadata=ProjectMetadata(name="Saved Project"))
            repo = ProjectRepository()

            saved_path = repo.save(project, Path(tmpdir))
            assert saved_path.exists()

            loaded_project = repo.load(Path(tmpdir))
            assert loaded_project.id == project.id
            assert loaded_project.metadata.name == "Saved Project"

    def test_save_creates_directory(self) -> None:
        """Test that save creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Project()
            repo = ProjectRepository()

            new_dir = Path(tmpdir) / "subdir" / "project"
            saved_path = repo.save(project, new_dir)
            assert saved_path.exists()

    def test_load_nonexistent_project(self) -> None:
        """Test loading a nonexistent project raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ProjectRepository()
            with pytest.raises(ProjectLoadError, match="not found"):
                repo.load(Path(tmpdir) / "nonexistent")

    def test_load_invalid_json(self) -> None:
        """Test loading invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "project.json"
            project_path.write_text("invalid json {{{")

            repo = ProjectRepository()
            with pytest.raises(ProjectFormatError, match="Invalid JSON"):
                repo.load(Path(tmpdir))

    def test_load_malformed_project(self) -> None:
        """Test loading malformed project data raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "project.json"
            project_path.write_text('{"id": "test", "version": "invalid"}')

            repo = ProjectRepository()
            with pytest.raises(ProjectFormatError, match="Unsupported project version"):
                repo.load(Path(tmpdir))

    def test_exists(self) -> None:
        """Test checking if project exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ProjectRepository()
            assert not repo.exists(Path(tmpdir))

            project = Project()
            repo.save(project, Path(tmpdir))
            assert repo.exists(Path(tmpdir))

    def test_get_project_path(self) -> None:
        """Test getting project file path."""
        repo = ProjectRepository()
        path = repo.get_project_path(Path("/some/path"))
        assert path == Path("/some/path") / "project.json"


class TestProjectValidator:
    """Tests for ProjectValidator."""

    def test_validate_valid_project(self) -> None:
        """Test validating a valid project."""
        project = Project(metadata=ProjectMetadata(name="Valid Project"))
        validator = ProjectValidator()
        errors = validator.validate(project)
        assert errors == []

    def test_validate_invalid_settings(self) -> None:
        """Test validation fails for invalid settings."""
        data = {
            "id": "test-id",
            "version": "0.1.0",
            "metadata": {"name": "Test"},
            "settings": {"frame_rate": 5},
            "state": {},
        }
        with pytest.raises(ValueError):
            Project.from_dict(data)

    def test_validate_invalid_scene_id(self) -> None:
        """Test validation fails for invalid scene ID."""
        project = Project(state=ProjectState(scenes=[""]))
        validator = ProjectValidator()
        errors = validator.validate(project)
        assert any("scene" in e.lower() for e in errors)

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise raises on invalid project."""
        project = Project(state=ProjectState(scenes=[""]))
        validator = ProjectValidator()
        with pytest.raises(ProjectValidationError) as exc_info:
            validator.validate_or_raise(project)
        assert len(exc_info.value.errors) > 0

    def test_validate_error_message(self) -> None:
        """Test that validation error message is descriptive."""
        project = Project(state=ProjectState(scenes=[""]))
        validator = ProjectValidator()
        with pytest.raises(ProjectValidationError) as exc_info:
            validator.validate_or_raise(project)
        assert "scene" in str(exc_info.value).lower()


class TestProjectExceptions:
    """Tests for project exceptions."""

    def test_validation_error_contains_errors(self) -> None:
        """Test that ValidationError contains error list."""
        error = ProjectValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)
        assert "error2" in str(error)

    def test_project_load_error(self) -> None:
        """Test ProjectLoadError can be raised."""
        with pytest.raises(ProjectLoadError):
            raise ProjectLoadError("Test error")

    def test_project_save_error(self) -> None:
        """Test ProjectSaveError can be raised."""
        with pytest.raises(ProjectSaveError):
            raise ProjectSaveError("Test error")

    def test_project_format_error(self) -> None:
        """Test ProjectFormatError can be raised."""
        with pytest.raises(ProjectFormatError):
            raise ProjectFormatError("Test error")
