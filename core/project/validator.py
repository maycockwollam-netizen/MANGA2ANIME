"""Project validation logic."""

from core.project.exceptions import ProjectValidationError
from core.project.model import SUPPORTED_VERSIONS, Project


class ProjectValidator:
    """Validator for project data."""

    def validate(self, project: Project) -> list[str]:
        """Validate a project.

        Args:
            project: The project to validate.

        Returns:
            List of validation errors. Empty list if valid.
        """
        errors: list[str] = []

        errors.extend(self._validate_id(project))
        errors.extend(self._validate_version(project))
        errors.extend(self._validate_metadata(project))
        errors.extend(self._validate_settings(project))
        errors.extend(self._validate_state(project))

        return errors

    def _validate_id(self, project: Project) -> list[str]:
        """Validate project ID."""
        errors: list[str] = []

        if not project.id:
            errors.append("Project ID is required")
        elif len(project.id) > 255:
            errors.append("Project ID must be 255 characters or less")

        return errors

    def _validate_version(self, project: Project) -> list[str]:
        """Validate project version."""
        errors: list[str] = []

        if not project.version:
            errors.append("Project version is required")
        elif project.version not in SUPPORTED_VERSIONS:
            errors.append(
                f"Unsupported project version: {project.version}. "
                f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
            )

        return errors

    def _validate_metadata(self, project: Project) -> list[str]:
        """Validate project metadata."""
        errors: list[str] = []

        if len(project.metadata.name) > 255:
            errors.append("Project name must be 255 characters or less")

        if len(project.metadata.description) > 2000:
            errors.append("Project description must be 2000 characters or less")

        if len(project.metadata.author) > 255:
            errors.append("Project author must be 255 characters or less")

        return errors

    def _validate_settings(self, project: Project) -> list[str]:
        """Validate project settings."""
        errors: list[str] = []
        settings = project.settings

        if settings.resolution_width < 640 or settings.resolution_width > 3840:
            errors.append("Resolution width must be between 640 and 3840")

        if settings.resolution_height < 360 or settings.resolution_height > 2160:
            errors.append("Resolution height must be between 360 and 2160")

        if settings.frame_rate < 12 or settings.frame_rate > 120:
            errors.append("Frame rate must be between 12 and 120")

        if settings.audio_sample_rate < 16000 or settings.audio_sample_rate > 96000:
            errors.append("Audio sample rate must be between 16000 and 96000")

        if settings.default_duration_seconds < 0.1 or settings.default_duration_seconds > 60:
            errors.append("Default duration must be between 0.1 and 60 seconds")

        return errors

    def _validate_state(self, project: Project) -> list[str]:
        """Validate project state."""
        errors: list[str] = []

        for scene_id in project.state.scenes:
            if not scene_id or len(scene_id) > 255:
                errors.append(f"Invalid scene ID: {scene_id}")

        for asset_id in project.state.assets:
            if not asset_id or len(asset_id) > 255:
                errors.append(f"Invalid asset ID: {asset_id}")

        return errors

    def validate_or_raise(self, project: Project) -> None:
        """Validate a project and raise if invalid.

        Args:
            project: The project to validate.

        Raises:
            ProjectValidationError: If validation fails.
        """
        errors = self.validate(project)
        if errors:
            raise ProjectValidationError(
                "Project validation failed",
                errors=errors,
            )
