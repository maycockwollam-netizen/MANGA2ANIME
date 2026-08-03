"""Project repository for file-based persistence."""

import json
from pathlib import Path

from core.project.exceptions import ProjectFormatError, ProjectLoadError, ProjectSaveError
from core.project.model import Project
from core.project.serialization import ProjectSerializer


class ProjectRepository:
    """Repository for saving and loading projects to/from disk."""

    PROJECT_FILE = "project.json"

    def save(self, project: Project, directory: Path) -> Path:
        """Save a project to a directory.

        Args:
            project: The project to save.
            directory: The directory to save to.

        Returns:
            Path to the saved project file.

        Raises:
            ProjectSaveError: If saving fails.
        """
        directory = Path(directory)
        project_path = directory / self.PROJECT_FILE

        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ProjectSaveError(f"Failed to create directory: {e}") from e

        try:
            json_content = ProjectSerializer.to_json(project)
            project_path.write_text(json_content, encoding="utf-8")
        except OSError as e:
            raise ProjectSaveError(f"Failed to write project file: {e}") from e
        except Exception as e:
            raise ProjectSaveError(f"Failed to serialize project: {e}") from e

        return project_path

    def load(self, directory: Path) -> Project:
        """Load a project from a directory.

        Args:
            directory: The directory containing the project file.

        Returns:
            Loaded Project instance.

        Raises:
            ProjectLoadError: If loading fails.
        """
        directory = Path(directory)
        project_path = directory / self.PROJECT_FILE

        if not project_path.exists():
            raise ProjectLoadError(
                f"Project file not found: {project_path}"
            )

        try:
            json_content = project_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ProjectLoadError(f"Failed to read project file: {e}") from e

        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ProjectFormatError(f"Invalid JSON in project file: {e}") from e

        try:
            return ProjectSerializer.deserialize(data)
        except ProjectFormatError:
            raise
        except Exception as e:
            raise ProjectFormatError(f"Invalid project format: {e}") from e

    def exists(self, directory: Path) -> bool:
        """Check if a project exists in the directory.

        Args:
            directory: The directory to check.

        Returns:
            True if project file exists, False otherwise.
        """
        return (Path(directory) / self.PROJECT_FILE).exists()

    def get_project_path(self, directory: Path) -> Path:
        """Get the path to the project file.

        Args:
            directory: The project directory.

        Returns:
            Path to the project file.
        """
        return Path(directory) / self.PROJECT_FILE
