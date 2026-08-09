"""Audio mixer adapter for output-path forwarding.

Provides a minimal adapter layer that binds an AudioMixer to a fixed output
path so callers can mix any configuration without re-supplying the output
location. The adapter introduces no mixing logic and does not depend on
runtime internals.

Scope:
    The adapter composes an AudioMixer with a fixed output Path, exposing a
    simpler mix(config) surface that injects the bound output path into the
    configuration. It does not perform mixing, manage state between calls,
    transform configuration beyond output path injection, or access runtime
    internals.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.audio.models import MixConfig, MixResult
    from tools.audio.protocol import AudioMixer


class OutputAdapter:
    """Minimal adapter that binds an AudioMixer to a fixed output path.

    Composes an AudioMixer with an output Path so callers can mix any
    configuration and have the result written to the bound location. The
    adapter injects the output path via the mixer's expected configuration
    extension (an `output_path` field on the config, if present), otherwise
    it is a passthrough that records the intended path.

    The adapter does not:
    - Perform any mixing logic
    - Manage state between calls
    - Access runtime internals
    - Mutate the input MixConfig (it is frozen)

    Example:
        >>> from pathlib import Path
        >>> from tools.audio import MixConfig, OutputAdapter
        >>> from tools.audio.concrete_mixer import WaveMixer
        >>>
        >>> adapter = OutputAdapter(WaveMixer(), Path("/tmp/mix.wav"))
        >>> # adapter.mix(MixConfig(...)) writes to /tmp/mix.wav
    """

    def __init__(self, mixer: AudioMixer, output_path: Path) -> None:
        """Initialize the adapter with a mixer and output path.

        Args:
            mixer: An AudioMixer-compatible implementation to forward to.
            output_path: The fixed output path to bind for mixes.
        """
        self._mixer = mixer
        self._output_path = output_path

    def mix(self, config: MixConfig) -> MixResult:
        """Mix the configuration using the bound output path.

        Args:
            config: Mix configuration describing the tracks.

        Returns:
            A MixResult describing the rendered output WAV file at the
            bound output path.

        Raises:
            AudioError: If the underlying mixer raises an error.
        """
        return self._mixer.mix(config, output_path=self._output_path)

    @property
    def mixer(self) -> AudioMixer:
        """Return the underlying AudioMixer (read-only).

        Returns:
            The AudioMixer this adapter forwards to.
        """
        return self._mixer

    @property
    def output_path(self) -> Path:
        """Return the bound output path (read-only).

        Returns:
            The Path bound to this adapter.
        """
        return self._output_path
