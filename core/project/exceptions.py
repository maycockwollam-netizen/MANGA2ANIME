"""Project-specific exceptions."""


class ProjectError(Exception):
    """Base exception for project-related errors."""

    pass


class ProjectValidationError(ProjectError):
    """Raised when project validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class ProjectLoadError(ProjectError):
    """Raised when loading a project fails."""

    pass


class ProjectSaveError(ProjectError):
    """Raised when saving a project fails."""

    pass


class ProjectFormatError(ProjectError):
    """Raised when project format is invalid."""

    pass


class ProjectVersionError(ProjectError):
    """Raised when project version is incompatible."""

    pass
