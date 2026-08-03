"""Track representation."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from core.timeline.exceptions import (
    TimelineNotFoundError,
)
from core.timeline.keyframe import Keyframe


class Track(BaseModel):
    """Represents an animation track.

    A track animates a single property of a target object.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="", max_length=255)
    target_id: str = Field(default="", max_length=255)
    property_name: str = Field(default="", max_length=255)
    keyframes: list[Keyframe] = Field(default_factory=list)

    def model_post_init(self, _info: object) -> None:
        """Sort keyframes by time after initialization."""
        self.keyframes.sort()

    def add_keyframe(self, keyframe: Keyframe) -> Keyframe:
        """Add a keyframe to the track.

        If a keyframe at the same time exists, it will be replaced.

        Args:
            keyframe: Keyframe to add.

        Returns:
            The added (or replaced) keyframe.
        """
        # Check for existing keyframe at same time
        for i, existing in enumerate(self.keyframes):
            if abs(existing.time - keyframe.time) < 1e-9:
                self.keyframes[i] = keyframe
                return keyframe

        self.keyframes.append(keyframe)
        self.keyframes.sort()
        return keyframe

    def remove_keyframe(self, time: float) -> Keyframe:
        """Remove a keyframe at a specific time.

        Args:
            time: Time of keyframe to remove.

        Returns:
            The removed keyframe.

        Raises:
            TimelineNotFoundError: If no keyframe at that time exists.
        """
        for i, kf in enumerate(self.keyframes):
            if abs(kf.time - time) < 1e-9:
                removed = self.keyframes.pop(i)
                return removed

        raise TimelineNotFoundError(f"No keyframe found at time {time}")

    def get_keyframe(self, time: float) -> Keyframe:
        """Get a keyframe at a specific time.

        Args:
            time: Time of keyframe.

        Returns:
            The keyframe at that time.

        Raises:
            TimelineNotFoundError: If no keyframe at that time exists.
        """
        for kf in self.keyframes:
            if abs(kf.time - time) < 1e-9:
                return kf
        raise TimelineNotFoundError(f"No keyframe found at time {time}")

    def get_keyframes(self) -> list[Keyframe]:
        """Get all keyframes ordered by time.

        Returns:
            List of keyframes.
        """
        return sorted(self.keyframes)

    def update_keyframe(self, time: float, **kwargs: Any) -> Keyframe:
        """Update a keyframe's properties.

        Args:
            time: Time of keyframe to update.
            **kwargs: Properties to update.

        Returns:
            The updated keyframe.

        Raises:
            TimelineNotFoundError: If no keyframe at that time exists.
        """
        keyframe = self.get_keyframe(time)
        for key, value in kwargs.items():
            if hasattr(keyframe, key):
                setattr(keyframe, key, value)
        self.keyframes.sort()
        return keyframe

    def has_keyframe(self, time: float) -> bool:
        """Check if a keyframe exists at a specific time.

        Args:
            time: Time to check.

        Returns:
            True if keyframe exists, False otherwise.
        """
        for kf in self.keyframes:
            if abs(kf.time - time) < 1e-9:
                return True
        return False

    def evaluate(self, time: float) -> Any:
        """Evaluate the track at a given time.

        Behavior:
        - Before first keyframe: Returns first keyframe's value (hold)
        - Exactly on keyframe: Returns keyframe's value
        - Between keyframes: Interpolates using keyframe's interpolation mode
        - After last keyframe: Returns last keyframe's value (hold)

        Args:
            time: Time to evaluate at.

        Returns:
            The evaluated value.
        """
        if not self.keyframes:
            return None

        # Before first keyframe
        if time <= self.keyframes[0].time:
            return self.keyframes[0].value

        # After last keyframe
        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        # Find surrounding keyframes
        prev_kf: Keyframe = self.keyframes[0]
        next_kf: Keyframe = self.keyframes[0]

        for kf in self.keyframes:
            if kf.time <= time:
                prev_kf = kf
            if kf.time > time:
                next_kf = kf
                break

        # Exactly on keyframe
        if abs(prev_kf.time - time) < 1e-9:
            return prev_kf.value

        # Interpolate
        if prev_kf == next_kf:
            return prev_kf.value

        # Calculate normalized time
        duration = next_kf.time - prev_kf.time
        if duration <= 0:
            return prev_kf.value

        t = (time - prev_kf.time) / duration
        return prev_kf.interpolate_to(next_kf, t)

    def validate(self) -> list[str]:
        """Validate the track.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not self.id:
            errors.append("Track ID is required")

        if len(self.name) > 255:
            errors.append("Track name must be 255 characters or less")

        if not self.property_name:
            errors.append("Track property name is required")

        # Check for duplicate keyframes (should not happen due to sorting)
        seen_times: set[float] = set()
        for kf in self.keyframes:
            rounded_time = round(kf.time, 9)
            if rounded_time in seen_times:
                errors.append(f"Duplicate keyframe at time {kf.time}")
            seen_times.add(rounded_time)

        return errors
