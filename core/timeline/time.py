"""Time and frame representation utilities."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class Time(BaseModel):
    """Represents a timeline position with both seconds and frame representations."""

    seconds: float = Field(ge=0.0)
    frame_rate: int = Field(gt=0)

    def model_post_init(self, _info: object) -> None:
        """Validate time values."""
        if self.seconds < 0:
            raise ValueError("Time in seconds cannot be negative")
        if self.frame_rate <= 0:
            raise ValueError("Frame rate must be positive")

    @property
    def frame(self) -> int:
        """Get the frame number (rounded down/truncated).

        Uses truncation (floor) for consistent behavior.
        Example: 1.5s at 24fps → frame 36
        """
        return int(self.seconds * self.frame_rate)

    @classmethod
    def from_frame(cls, frame: int, frame_rate: int) -> "Time":
        """Create Time from frame number.

        Args:
            frame: Frame number (must be >= 0).
            frame_rate: Frames per second.

        Returns:
            Time instance.
        """
        if frame < 0:
            raise ValueError("Frame number cannot be negative")
        seconds = frame / frame_rate
        return cls(seconds=seconds, frame_rate=frame_rate)

    def to_frame_rounded(self) -> int:
        """Get the frame number rounded to nearest.

        Uses round-half-up convention.
        Example: 1.5s at 24fps → frame 36
        Example: 1.51s at 24fps → frame 36
        """
        return int(round(self.seconds * self.frame_rate))


@dataclass
class TimeRange:
    """Represents a range of time."""

    start_seconds: float
    end_seconds: float
    frame_rate: int

    def __post_init__(self) -> None:
        """Validate time range."""
        if self.start_seconds < 0:
            raise ValueError("Start time cannot be negative")
        if self.end_seconds < self.start_seconds:
            raise ValueError("End time must be >= start time")

    @property
    def start(self) -> Time:
        """Get start time."""
        return Time(seconds=self.start_seconds, frame_rate=self.frame_rate)

    @property
    def end(self) -> Time:
        """Get end time."""
        return Time(seconds=self.end_seconds, frame_rate=self.frame_rate)

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return self.end_seconds - self.start_seconds

    @property
    def start_frame(self) -> int:
        """Get start frame."""
        return int(self.start_seconds * self.frame_rate)

    @property
    def end_frame(self) -> int:
        """Get end frame (inclusive)."""
        return int(self.end_seconds * self.frame_rate)


def seconds_to_frame(seconds: float, frame_rate: int) -> int:
    """Convert seconds to frame number.

    Uses truncation (floor) behavior.

    Args:
        seconds: Time in seconds.
        frame_rate: Frames per second.

    Returns:
        Frame number (>= 0).

    Raises:
        ValueError: If seconds < 0 or frame_rate <= 0.
    """
    if seconds < 0:
        raise ValueError("Seconds cannot be negative")
    if frame_rate <= 0:
        raise ValueError("Frame rate must be positive")
    return int(seconds * frame_rate)


def frame_to_seconds(frame: int, frame_rate: int) -> float:
    """Convert frame number to seconds.

    Args:
        frame: Frame number (>= 0).
        frame_rate: Frames per second.

    Returns:
        Time in seconds.

    Raises:
        ValueError: If frame < 0 or frame_rate <= 0.
    """
    if frame < 0:
        raise ValueError("Frame number cannot be negative")
    if frame_rate <= 0:
        raise ValueError("Frame rate must be positive")
    return frame / frame_rate
