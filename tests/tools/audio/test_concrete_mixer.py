"""Tests for concrete WaveMixer."""

import struct
import wave
from pathlib import Path

import pytest

from tools.audio import (
    AudioConfigError,
    AudioMixer,
    AudioTrack,
    AudioTrackError,
    MixConfig,
    MixResult,
    WaveMixer,
)


def _read_samples(path: Path) -> list[int]:
    with wave.open(str(path), "rb") as wf:
        data = wf.readframes(wf.getnframes())
    return list(struct.unpack(f"<{len(data) // 2}h", data))


class TestWaveMixerBasics:
    """Tests for WaveMixer basic functionality."""

    def test_satisfies_audio_mixer_protocol(self) -> None:
        """Test that WaveMixer satisfies the AudioMixer protocol."""
        assert isinstance(WaveMixer(), AudioMixer)

    def test_empty_mix_writes_valid_wav(self, tmp_path: Path) -> None:
        """Test that an empty mix writes a valid (zero-length) WAV."""
        out = tmp_path / "empty.wav"
        result = WaveMixer().mix(
            MixConfig(sample_rate=44100, channels=1, tracks=[]), output_path=out
        )

        assert out.exists()
        assert isinstance(result, MixResult)
        assert result.duration_seconds == 0.0
        assert result.track_count == 0
        assert result.sample_rate == 44100
        assert result.channels == 1

    def test_creates_parent_directory(self, tmp_path: Path, make_wav) -> None:
        """Test that the mixer creates missing parent directories."""
        a = make_wav()
        out = tmp_path / "nested" / "deep" / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[AudioTrack(track_id="t", source_path=a)],
            ),
            output_path=out,
        )
        assert out.exists()


class TestWaveMixerTimestampPlacement:
    """Tests for track placement by start_time."""

    def test_single_track_start_at_zero(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that a track at start_time 0 is placed at the beginning."""
        a = make_wav(value=16000, duration_seconds=0.1)
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[AudioTrack(track_id="t", source_path=a, start_time=0.0)],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        assert len(samples) == 4410
        assert samples[0] == 16000
        assert samples[-1] == 16000

    def test_track_start_time_offsets_placement(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that start_time offsets the track in the output."""
        a = make_wav(value=16000, duration_seconds=0.1)
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[AudioTrack(track_id="t", source_path=a, start_time=0.05)],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        # 0.05s = 2205 frames of silence then 4410 frames of the track.
        assert len(samples) == 2205 + 4410
        assert samples[0] == 0
        assert samples[2205] == 16000
        assert samples[-1] == 16000


class TestWaveMixerSumming:
    """Tests for sample summing across tracks."""

    def test_overlapping_tracks_are_summed(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that overlapping track samples are summed."""
        a = make_wav(value=16000, duration_seconds=0.1, name="a.wav")
        b = make_wav(value=8000, duration_seconds=0.1, name="b.wav")
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[
                    AudioTrack(track_id="bgm", source_path=a, start_time=0.0, gain=0.5),
                    AudioTrack(track_id="sfx", source_path=b, start_time=0.05, gain=0.5),
                ],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        # bgm only region (before 2205): 16000*0.5 = 8000
        assert samples[100] == 8000
        # overlap region: 8000 + (8000*0.5) = 12000
        assert samples[3000] == 12000
        # sfx tail region (after 4410): 8000*0.5 = 4000
        assert samples[5000] == 4000

    def test_clamping_prevents_overflow(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that summed samples are clamped to int16 range."""
        a = make_wav(value=30000, duration_seconds=0.05, name="a.wav")
        b = make_wav(value=30000, duration_seconds=0.05, name="b.wav")
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[
                    AudioTrack(track_id="a", source_path=a, start_time=0.0, gain=1.0),
                    AudioTrack(track_id="b", source_path=b, start_time=0.0, gain=1.0),
                ],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        # 30000 + 30000 = 60000 -> clamped to 32767
        assert samples[0] == 32767

    def test_master_gain_applied(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that master_gain is applied to the summed output."""
        a = make_wav(value=10000, duration_seconds=0.05)
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                master_gain=0.5,
                tracks=[AudioTrack(track_id="t", source_path=a, gain=1.0)],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        assert samples[0] == 5000

    def test_zero_gain_track_is_silent(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that a track with gain 0 contributes nothing."""
        a = make_wav(value=16000, duration_seconds=0.05)
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=1,
                tracks=[AudioTrack(track_id="t", source_path=a, gain=0.0)],
            ),
            output_path=out,
        )
        samples = _read_samples(out)
        assert all(s == 0 for s in samples)


class TestWaveMixerChannels:
    """Tests for channel handling."""

    def test_mono_to_stereo_duplication(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that a mono track is duplicated into stereo output."""
        a = make_wav(channels=1, value=1234, duration_seconds=0.05)
        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=44100,
                channels=2,
                tracks=[AudioTrack(track_id="t", source_path=a)],
            ),
            output_path=out,
        )
        with wave.open(str(out), "rb") as wf:
            assert wf.getnchannels() == 2
        samples = _read_samples(out)
        # Interleaved L,R should both be 1234.
        assert samples[0] == 1234
        assert samples[1] == 1234

    def test_stereo_to_mono_averaging(
        self, tmp_path: Path
    ) -> None:
        """Test that a stereo track is averaged into mono output."""
        sr = 44100
        stereo_path = tmp_path / "stereo.wav"
        # Left = 1000, right = 2000, 0.05s
        frames = int(0.05 * sr)
        samples = []
        for _ in range(frames):
            samples.append(1000)
            samples.append(2000)
        with wave.open(str(stereo_path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

        out = tmp_path / "mix.wav"
        WaveMixer().mix(
            MixConfig(
                sample_rate=sr,
                channels=1,
                tracks=[AudioTrack(track_id="t", source_path=stereo_path)],
            ),
            output_path=out,
        )
        mono = _read_samples(out)
        assert mono[0] == 1500  # (1000 + 2000) // 2


class TestWaveMixerErrors:
    """Tests for error handling in WaveMixer."""

    def test_missing_file_raises_track_error(self, tmp_path: Path) -> None:
        """Test that a missing track file raises AudioTrackError."""
        out = tmp_path / "mix.wav"
        with pytest.raises(AudioTrackError, match="not found"):
            WaveMixer().mix(
                MixConfig(
                    sample_rate=44100,
                    channels=1,
                    tracks=[AudioTrack(track_id="t", source_path=tmp_path / "nope.wav")],
                ),
                output_path=out,
            )

    def test_sample_rate_mismatch_raises_track_error(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that a sample-rate mismatch raises AudioTrackError."""
        a = make_wav(sample_rate=48000, value=1000)
        out = tmp_path / "mix.wav"
        with pytest.raises(AudioTrackError, match="sample rate"):
            WaveMixer().mix(
                MixConfig(
                    sample_rate=44100,
                    channels=1,
                    tracks=[AudioTrack(track_id="t", source_path=a)],
                ),
                output_path=out,
            )

    def test_non_16bit_wav_raises_track_error(self, tmp_path: Path) -> None:
        """Test that an 8-bit WAV raises AudioTrackError."""
        path = tmp_path / "8bit.wav"
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)
            wf.setframerate(44100)
            wf.writeframes(b"\x80" * 100)
        out = tmp_path / "mix.wav"
        with pytest.raises(AudioTrackError, match="16-bit PCM"):
            WaveMixer().mix(
                MixConfig(
                    sample_rate=44100,
                    channels=1,
                    tracks=[AudioTrack(track_id="t", source_path=path)],
                ),
                output_path=out,
            )

    def test_none_output_path_raises_config_error(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that a None output_path raises AudioConfigError."""
        a = make_wav()
        with pytest.raises(AudioConfigError, match="output_path"):
            WaveMixer().mix(
                MixConfig(
                    sample_rate=44100,
                    channels=1,
                    tracks=[AudioTrack(track_id="t", source_path=a)],
                ),
                output_path=None,  # type: ignore[arg-type]
            )


class TestWaveMixerDeterminism:
    """Tests for deterministic mixing."""

    def test_repeated_mix_produces_identical_output(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that the same config produces identical output across runs."""
        a = make_wav(value=12345, duration_seconds=0.05)
        config = MixConfig(
            sample_rate=44100,
            channels=1,
            tracks=[AudioTrack(track_id="t", source_path=a, start_time=0.01, gain=0.7)],
        )
        out1 = tmp_path / "mix1.wav"
        out2 = tmp_path / "mix2.wav"
        WaveMixer().mix(config, output_path=out1)
        WaveMixer().mix(config, output_path=out2)
        assert _read_samples(out1) == _read_samples(out2)
