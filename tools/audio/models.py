"""Audio data models V1.

Pure data contracts for the audio mixer. No execution or I/O beyond
configuration description.

Scope:
    This module defines the configuration and result contracts for audio
    mixing. It does NOT implement mixing logic (see concrete_mixer.py) nor
    depend on runtime.animation internals.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class AudioTrack(BaseModel):
    """Configuration for a single audio track in a mix.

    Represents a track placed on a shared timeline. The track's PCM samples
    are read from a WAV file and mixed starting at `start_time`.

    Attributes:
        track_id: Unique identifier for this track within the mix.
        source_path: Path to the WAV file (PCM 16-bit).
        start_time: Offset in seconds from the mix origin where this track
            begins. Must be >= 0.0.
        gain: Linear amplitude multiplier applied to this track (0.0 mute,
            1.0 unity). Must be >= 0.0.

    Invariant: track_id must be unique within a mix (enforced at mix level).
    A track with gain 0.0 is allowed (effectively muted).
    """

    track_id: str = Field(min_length=1, description="Unique track identifier")
    source_path: Path = Field(description="Path to the WAV file")
    start_time: float = Field(default=0.0, ge=0.0, description="Start offset in seconds")
    gain: float = Field(default=1.0, ge=0.0, description="Linear gain multiplier")

    @field_validator("track_id", mode="before")
    @classmethod
    def validate_track_id(cls, v: str) -> str:
        """Validate track_id is non-empty and trimmed."""
        if not isinstance(v, str):
            raise ValueError(f"track_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("track_id cannot be empty or whitespace-only")
        return stripped


class MixConfig(BaseModel):
    """Configuration for an audio mix.

    Describes how a set of AudioTracks are combined into a single output.

    Attributes:
        sample_rate: Output sample rate in Hz. All tracks must match this
            rate (resampling is out of scope for V1). Must be > 0.
        channels: Number of output channels (1 = mono, 2 = stereo). Must be
            1 or 2.
        tracks: Ordered tuple of AudioTrack to mix. Stored as tuple for
            immutability.
        master_gain: Linear master gain applied after summing (default 1.0).

    Invariant: All tracks must have a unique track_id. This is enforced at
    the model level because uniqueness only requires this object's context.
    Sample-rate consistency with each track is enforced at mix time because
    it requires reading each WAV file.
    """

    model_config = {"frozen": True}

    sample_rate: int = Field(default=44100, gt=0, description="Output sample rate in Hz")
    channels: int = Field(default=2, description="Output channels (1 mono, 2 stereo)")
    tracks: tuple[AudioTrack, ...] = Field(default_factory=tuple, description="Tracks to mix")
    master_gain: float = Field(default=1.0, ge=0.0, description="Master linear gain")

    @field_validator("channels", mode="before")
    @classmethod
    def validate_channels(cls, v: int) -> int:
        """Validate channel count is 1 or 2."""
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"channels must be int, got {type(v).__name__}")
        if v not in (1, 2):
            raise ValueError("channels must be 1 (mono) or 2 (stereo)")
        return v

    @field_validator("tracks", mode="before")
    @classmethod
    def convert_tracks_to_tuple(
        cls, v: list[AudioTrack] | tuple[AudioTrack, ...] | None
    ) -> tuple[AudioTrack, ...]:
        """Convert tracks list to tuple for immutability."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        return ()

    @model_validator(mode="after")
    def validate_unique_track_ids(self) -> MixConfig:
        """Validate that all track_ids are unique within the mix."""
        if self.tracks:
            ids = [track.track_id for track in self.tracks]
            if len(ids) != len(set(ids)):
                seen: set[str] = set()
                dup = next(i for i in ids if i in seen or seen.add(i))
                raise ValueError(f"duplicate track_id: {dup}")
        return self


class MixResult(BaseModel):
    """Result of an audio mix.

    Pure data contract describing the output of a mix. Does not hold the
    audio bytes themselves; the path points to the artifact.

    Attributes:
        output_path: Path to the rendered output WAV file (PCM 16-bit).
        sample_rate: Output sample rate in Hz.
        channels: Number of output channels.
        duration_seconds: Total duration of the mix in seconds.
        track_count: Number of tracks included in the mix.
    """

    model_config = {"frozen": True}

    output_path: Path = Field(description="Path to the rendered output WAV file")
    sample_rate: int = Field(gt=0, description="Output sample rate in Hz")
    channels: int = Field(description="Output channels (1 or 2)")
    duration_seconds: float = Field(ge=0.0, description="Total mix duration in seconds")
    track_count: int = Field(ge=0, description="Number of tracks in the mix")


__all__ = [
    "AudioTrack",
    "MixConfig",
    "MixResult",
]
