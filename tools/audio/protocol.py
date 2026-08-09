"""Audio mixer protocol.

Defines the minimal structural contract for audio mixers that consume a
MixConfig and produce a MixResult. This module contains no concrete mixing
implementation.

Scope:
    An AudioMixer combines multiple audio tracks into a single output file,
    placing each track on a shared timeline according to its start_time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tools.audio.models import MixConfig, MixResult


@runtime_checkable
class AudioMixer(Protocol):
    """Minimal audio mixer protocol.

    An AudioMixer mixes a set of tracks described by a MixConfig into a
    single output WAV file and returns a MixResult describing the artifact.

    Protocol Requirements:
        - Accept a MixConfig as primary input.
        - Return a MixResult pointing to the rendered output file.
        - Not mutate the input MixConfig (it is frozen).

    Dependency Constraints:
        AudioMixer implementations must NOT depend on:
        - runtime.animation (ANY module)
        - AnimationRuntime internals
        - tools.manga_frame

    Usage:
        The AudioMixer is a runtime-checkable Protocol. Use isinstance() to
        verify that an object implements the protocol:

        >>> class NoopMixer:
        ...     def mix(self, config):
        ...         from pathlib import Path
        ...         from tools.audio import MixResult
        ...         return MixResult(
        ...             output_path=Path("/tmp/out.wav"),
        ...             sample_rate=config.sample_rate,
        ...             channels=config.channels,
        ...             duration_seconds=0.0,
        ...             track_count=len(config.tracks),
        ...         )
        >>>
        >>> mixer: AudioMixer = NoopMixer()
        >>> assert isinstance(mixer, AudioMixer)

    Example:
        >>> from tools.audio import MixConfig, WaveMixer
        >>> from pathlib import Path
        >>>
        >>> config = MixConfig(sample_rate=44100, channels=1, tracks=())
        >>> # WaveMixer requires at least an output path strategy; see
        >>> # concrete_mixer.py for full usage.
    """

    def mix(self, config: MixConfig) -> MixResult:
        """Mix the tracks described by the config into a single output.

        Args:
            config: Mix configuration describing the output format and tracks.

        Returns:
            A MixResult describing the rendered output WAV file.
        """
        ...
