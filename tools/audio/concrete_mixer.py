"""Concrete audio mixer implementation using stdlib wave.

V1 implementation that mixes audio tracks into a single output WAV file
(PCM 16-bit) using only the Python standard library (wave + struct). No
external audio dependencies (numpy, ffmpeg) are required.

Mixing model:
    Each AudioTrack is placed on a shared timeline starting at its
    start_time (seconds). Samples are summed across tracks with per-track
    gain and a master gain, then clamped to the int16 range and written as
    PCM 16-bit.

This module does NOT:
- Implement resampling (tracks must match the config sample rate)
- Implement GPU audio processing
- Access runtime animation internals
- Implement caching or batching
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from tools.audio.exceptions import AudioConfigError, AudioMixError, AudioTrackError
from tools.audio.models import AudioTrack, MixConfig, MixResult

if TYPE_CHECKING:
    from tools.audio.protocol import AudioMixer as _AudioMixin  # noqa: F401


# int16 signed range
_INT16_MAX = 32767
_INT16_MIN = -32768


class WaveMixer:
    """Concrete audio mixer using stdlib wave for PCM 16-bit output.

    V1 mixes tracks by summing int16 samples per channel with per-track and
    master gains, clamping to the int16 range. All tracks must share the
    config sample rate; channel mismatches are handled by broadcasting mono
    to stereo (or stereo to mono by averaging) as needed.

    Example:
        >>> from pathlib import Path
        >>> from tools.audio import MixConfig, WaveMixer
        >>> mixer = WaveMixer()
        >>> config = MixConfig(sample_rate=44100, channels=1, tracks=())
        >>> # result = mixer.mix(config, output_path=Path("/tmp/out.wav"))
    """

    def mix(self, config: MixConfig, output_path: Path) -> MixResult:
        """Mix the tracks described by config into a single output WAV file.

        Args:
            config: Mix configuration describing the output format and tracks.
            output_path: Path to write the output WAV file (PCM 16-bit).

        Returns:
            A MixResult describing the rendered output.

        Raises:
            AudioConfigError: If the configuration is inconsistent.
            AudioTrackError: If a track file cannot be opened or decoded.
            AudioMixError: If the mixing or write pass fails.
        """
        if output_path is None:
            raise AudioConfigError("output_path must not be None")
        output_path = Path(output_path)

        sample_rate = config.sample_rate
        channels = config.channels

        # Compute each track's per-channel sample buffer and timeline offset.
        loaded = []
        max_samples = 0
        for track in config.tracks:
            track_samples, track_channels = self._load_track(track, sample_rate)
            # Normalize track channels to the output channel count.
            track_samples = self._convert_channels(track_samples, track_channels, channels)
            offset = self._start_time_to_samples(track.start_time, sample_rate, channels)
            end = offset + len(track_samples)
            loaded.append((offset, track_samples, track.gain))
            if end > max_samples:
                max_samples = end

        # Sum samples across tracks with gains, clamping to int16 range.
        # Use a list of ints sized to the output; empty mixes yield silence.
        output = [0] * max_samples
        for offset, track_samples, gain in loaded:
            self._accumulate(output, offset, track_samples, gain)

        # Apply master gain.
        if config.master_gain != 1.0:
            self._apply_master_gain(output, config.master_gain)

        # Write the output WAV file.
        self._write_wav(output_path, output, sample_rate, channels)

        duration_seconds = (max_samples // channels) / sample_rate if sample_rate > 0 else 0.0
        return MixResult(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            duration_seconds=duration_seconds,
            track_count=len(config.tracks),
        )

    def _load_track(
        self, track: AudioTrack, expected_rate: int
    ) -> tuple[list[int], int]:
        """Load a track's PCM samples from its WAV file.

        Args:
            track: The audio track to load.
            expected_rate: Expected sample rate in Hz.

        Returns:
            Tuple of (samples list, channel count).

        Raises:
            AudioTrackError: If the file cannot be opened or has an
                unsupported format.
        """
        path = track.source_path
        try:
            with wave.open(str(path), "rb") as wf:
                if wf.getsampwidth() != 2:
                    raise AudioTrackError(
                        f"track '{track.track_id}' must be 16-bit PCM, "
                        f"got sample width {wf.getsampwidth()}"
                    )
                if wf.getframerate() != expected_rate:
                    raise AudioTrackError(
                        f"track '{track.track_id}' sample rate {wf.getframerate()} "
                        f"does not match mix rate {expected_rate}"
                    )
                channels = wf.getnchannels()
                if channels not in (1, 2):
                    raise AudioTrackError(
                        f"track '{track.track_id}' has unsupported channels {channels}"
                    )
                frames = wf.readframes(wf.getnframes())
        except AudioTrackError:
            raise
        except FileNotFoundError as e:
            raise AudioTrackError(f"track '{track.track_id}' not found: {path}") from e
        except wave.Error as e:
            raise AudioTrackError(f"track '{track.track_id}' is not a valid WAV: {e}") from e

        samples = list(struct.unpack(f"<{len(frames) // 2}h", frames))
        return samples, channels

    def _convert_channels(
        self, samples: list[int], from_channels: int, to_channels: int
    ) -> list[int]:
        """Convert a sample buffer between mono and stereo.

        Args:
            samples: Flat list of int16 samples interleaved by channel.
            from_channels: Source channel count (1 or 2).
            to_channels: Target channel count (1 or 2).

        Returns:
            Converted sample list matching the target channel count.

        Raises:
            AudioConfigError: If channels are unsupported.
        """
        if from_channels == to_channels:
            return samples
        if from_channels == 1 and to_channels == 2:
            # Mono -> stereo: duplicate each sample.
            out = []
            for s in samples:
                out.append(s)
                out.append(s)
            return out
        if from_channels == 2 and to_channels == 1:
            # Stereo -> mono: average left and right, clamp.
            out = []
            for i in range(0, len(samples) - 1, 2):
                avg = (samples[i] + samples[i + 1]) // 2
                out.append(self._clamp(avg))
            return out
        raise AudioConfigError(
            f"unsupported channel conversion {from_channels}->{to_channels}"
        )

    def _start_time_to_samples(
        self, start_time: float, sample_rate: int, channels: int
    ) -> int:
        """Convert a start time in seconds to a sample-frame offset.

        The offset is in interleaved samples (frames * channels) so it can be
        used directly as an index into the flat output buffer.

        Args:
            start_time: Start offset in seconds.
            sample_rate: Sample rate in Hz.
            channels: Channel count.

        Returns:
            Interleaved-sample offset into the flat buffer.
        """
        frames = int(round(start_time * sample_rate))
        return max(0, frames * channels)

    def _accumulate(
        self,
        output: list[int],
        offset: int,
        track_samples: list[int],
        gain: float,
    ) -> None:
        """Accumulate a track's samples into the output buffer with gain.

        Sums in 32-bit space and clamps back to int16 to avoid overflow wrap.
        Mutates `output` in place.

        Args:
            output: Flat output buffer (mutated).
            offset: Starting index in the output buffer.
            track_samples: Track's interleaved samples.
            gain: Linear gain applied to this track.
        """
        if gain == 0.0:
            return
        for i, sample in enumerate(track_samples):
            idx = offset + i
            if idx >= len(output):
                break
            output[idx] = self._clamp(output[idx] + int(round(sample * gain)))

    def _apply_master_gain(self, output: list[int], master_gain: float) -> None:
        """Apply a master gain to the output buffer in place.

        Args:
            output: Flat output buffer (mutated).
            master_gain: Linear master gain.
        """
        if master_gain == 1.0:
            return
        for i in range(len(output)):
            output[i] = self._clamp(int(round(output[i] * master_gain)))

    def _write_wav(
        self,
        path: Path,
        samples: list[int],
        sample_rate: int,
        channels: int,
    ) -> None:
        """Write the output samples to a PCM 16-bit WAV file.

        Args:
            path: Destination file path.
            samples: Flat interleaved int16 samples.
            sample_rate: Sample rate in Hz.
            channels: Channel count (1 or 2).

        Raises:
            AudioMixError: If the file cannot be written.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(path), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        except (OSError, wave.Error) as e:
            raise AudioMixError(f"failed to write output WAV '{path}': {e}") from e

    @staticmethod
    def _clamp(value: int) -> int:
        """Clamp a sample to the int16 signed range.

        Args:
            value: Sample value to clamp.

        Returns:
            Value clamped to [-32768, 32767].
        """
        if value > _INT16_MAX:
            return _INT16_MAX
        if value < _INT16_MIN:
            return _INT16_MIN
        return value
