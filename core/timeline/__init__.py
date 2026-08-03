"""Core Timeline Module.

This module provides the animation timeline system for Manga2Anime.
It handles time representation, keyframes, tracks, and evaluation.
"""

from core.timeline.exceptions import (
    TimelineDuplicateIDError,
    TimelineError,
    TimelineEvaluationError,
    TimelineKeyframeError,
    TimelineNotFoundError,
    TimelineSerializationError,
    TimelineTrackError,
    TimelineValidationError,
)
from core.timeline.keyframe import InterpolationType, Keyframe
from core.timeline.serialization import TimelineSerializer
from core.timeline.time import Time, TimeRange, frame_to_seconds, seconds_to_frame
from core.timeline.timeline import Timeline, TimelineMetadata, TimelineSettings
from core.timeline.track import Track

__all__ = [
    # Models
    "Timeline",
    "TimelineMetadata",
    "TimelineSettings",
    "Track",
    "Keyframe",
    "InterpolationType",
    # Time utilities
    "Time",
    "TimeRange",
    "seconds_to_frame",
    "frame_to_seconds",
    # Serializer
    "TimelineSerializer",
    # Exceptions
    "TimelineError",
    "TimelineValidationError",
    "TimelineTrackError",
    "TimelineKeyframeError",
    "TimelineEvaluationError",
    "TimelineSerializationError",
    "TimelineNotFoundError",
    "TimelineDuplicateIDError",
]
