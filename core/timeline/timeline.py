"""Timeline model and timeline management."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.timeline.exceptions import (
    TimelineDuplicateIDError,
    TimelineNotFoundError,
    TimelineValidationError,
)
from core.timeline.time import seconds_to_frame
from core.timeline.track import Track


class TimelineMetadata(BaseModel):
    """Metadata for a timeline."""

    name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TimelineSettings(BaseModel):
    """Settings for a timeline."""

    frame_rate: int = Field(default=24, ge=1, le=240)
    duration: float = Field(default=10.0, ge=0.0)


class Timeline(BaseModel):
    """Main timeline model for animation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    metadata: TimelineMetadata = Field(default_factory=TimelineMetadata)
    settings: TimelineSettings = Field(default_factory=TimelineSettings)
    tracks: dict[str, Track] = Field(default_factory=dict)

    def model_post_init(self, _info: object) -> None:
        """Validate timeline state."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid timeline state: {errors}")

    @property
    def frame_rate(self) -> int:
        """Get frame rate."""
        return self.settings.frame_rate

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return self.settings.duration

    @property
    def total_frames(self) -> int:
        """Get total number of frames."""
        return seconds_to_frame(self.duration, self.frame_rate)

    def add_track(self, track: Track) -> Track:
        """Add a track to the timeline.

        Args:
            track: Track to add.

        Returns:
            The added track.

        Raises:
            TimelineDuplicateIDError: If track ID already exists.
        """
        if track.id in self.tracks:
            raise TimelineDuplicateIDError(f"Track with ID '{track.id}' already exists")

        self.tracks[track.id] = track
        self._update_timestamp()
        return track

    def remove_track(self, track_id: str) -> None:
        """Remove a track from the timeline.

        Args:
            track_id: ID of track to remove.

        Raises:
            TimelineNotFoundError: If track not found.
        """
        if track_id not in self.tracks:
            raise TimelineNotFoundError(f"Track '{track_id}' not found")

        del self.tracks[track_id]
        self._update_timestamp()

    def get_track(self, track_id: str) -> Track:
        """Get a track by ID.

        Args:
            track_id: ID of track to get.

        Returns:
            The track.

        Raises:
            TimelineNotFoundError: If track not found.
        """
        if track_id not in self.tracks:
            raise TimelineNotFoundError(f"Track '{track_id}' not found")
        return self.tracks[track_id]

    def has_track(self, track_id: str) -> bool:
        """Check if timeline contains a track.

        Args:
            track_id: ID to check.

        Returns:
            True if track exists, False otherwise.
        """
        return track_id in self.tracks

    def update_track(self, track_id: str, **kwargs: Any) -> Track:
        """Update a track's properties.

        Args:
            track_id: ID of track to update.
            **kwargs: Properties to update.

        Returns:
            The updated track.

        Raises:
            TimelineNotFoundError: If track not found.
        """
        track = self.get_track(track_id)
        for key, value in kwargs.items():
            if hasattr(track, key) and key != "id":
                setattr(track, key, value)
        self._update_timestamp()
        return track

    def get_tracks(self) -> list[Track]:
        """Get all tracks.

        Returns:
            List of tracks.
        """
        return list(self.tracks.values())

    def evaluate(self, time: float) -> dict[str, Any]:
        """Evaluate all tracks at a given time.

        Args:
            time: Time in seconds.

        Returns:
            Dictionary mapping track_id to evaluated value.
        """
        results: dict[str, Any] = {}
        for track_id, track in self.tracks.items():
            results[track_id] = track.evaluate(time)
        return results

    def evaluate_frame(self, frame: int) -> dict[str, Any]:
        """Evaluate all tracks at a given frame.

        Args:
            frame: Frame number.

        Returns:
            Dictionary mapping track_id to evaluated value.
        """
        time = frame / self.frame_rate
        return self.evaluate(time)

    def get_track_evaluations(self, track_id: str, times: list[float]) -> list[Any]:
        """Get evaluated values for a track at multiple times.

        Args:
            track_id: ID of track to evaluate.
            times: List of times to evaluate at.

        Returns:
            List of evaluated values.
        """
        track = self.get_track(track_id)
        return [track.evaluate(t) for t in times]

    def _update_timestamp(self) -> None:
        """Update timeline metadata timestamp."""
        self.metadata.updated_at = datetime.now(UTC)

    def validate(self) -> list[str]:
        """Validate the timeline.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Timeline ID is required")

        if len(self.metadata.name) > 255:
            errors.append("Timeline name must be 255 characters or less")

        if self.settings.duration < 0:
            errors.append("Duration must be non-negative")

        if self.settings.frame_rate <= 0:
            errors.append("Frame rate must be positive")

        # Validate tracks
        for track in self.tracks.values():
            track_errors = track.validate()
            for error in track_errors:
                errors.append(f"Track '{track.id}': {error}")

        return errors

    def validate_or_raise(self) -> None:
        """Validate the timeline and raise if invalid.

        Raises:
            TimelineValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise TimelineValidationError("Timeline validation failed", errors=errors)
