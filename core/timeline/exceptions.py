"""Timeline-specific exceptions."""


class TimelineError(Exception):
    """Base exception for timeline-related errors."""

    pass


class TimelineValidationError(TimelineError):
    """Raised when timeline validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            return f"{self.args[0]}:\n  - {error_list}"
        return self.args[0]


class TimelineTrackError(TimelineError):
    """Raised when track operation fails."""

    pass


class TimelineKeyframeError(TimelineError):
    """Raised when keyframe operation fails."""

    pass


class TimelineEvaluationError(TimelineError):
    """Raised when timeline evaluation fails."""

    pass


class TimelineSerializationError(TimelineError):
    """Raised when timeline serialization fails."""

    pass


class TimelineNotFoundError(TimelineTrackError):
    """Raised when track or keyframe is not found."""

    pass


class TimelineDuplicateIDError(TimelineTrackError):
    """Raised when duplicate ID is detected."""

    pass
