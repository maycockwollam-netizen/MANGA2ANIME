"""Tests for audio output adapter."""

from pathlib import Path

import pytest

from tools.audio import (
    AudioError,
    AudioTrack,
    MixConfig,
    MixResult,
    OutputAdapter,
    WaveMixer,
)


class TestOutputAdapterBasics:
    """Tests for OutputAdapter basic functionality."""

    def test_adapter_binds_mixer_and_path(self, tmp_path: Path) -> None:
        """Test that adapter exposes the bound mixer and output path."""
        mixer = WaveMixer()
        out = tmp_path / "mix.wav"
        adapter = OutputAdapter(mixer, out)

        assert adapter.mixer is mixer
        assert adapter.output_path == out

    def test_adapter_mix_writes_to_bound_path(self, tmp_path: Path) -> None:
        """Test that the adapter writes to the bound output path."""
        out = tmp_path / "bound.wav"
        adapter = OutputAdapter(WaveMixer(), out)

        config = MixConfig(sample_rate=44100, channels=1, tracks=[])
        adapter.mix(config)

        assert out.exists()


class TestOutputAdapterForwarding:
    """Tests for OutputAdapter forwarding behavior."""

    def test_adapter_produces_mix_result(
        self, tmp_path: Path, make_wav
    ) -> None:
        """Test that the adapter returns a MixResult pointing at the bound path."""
        a = make_wav(value=10000)
        out = tmp_path / "res.wav"
        adapter = OutputAdapter(WaveMixer(), out)

        config = MixConfig(
            sample_rate=44100,
            channels=1,
            tracks=[AudioTrack(track_id="t", source_path=a)],
        )
        result = adapter.mix(config)

        assert isinstance(result, MixResult)
        assert result.output_path == out

    def test_adapter_empty_mix_writes_valid_wav(self, tmp_path: Path) -> None:
        """Test that an empty mix via the adapter writes a valid WAV."""
        out = tmp_path / "empty.wav"
        adapter = OutputAdapter(WaveMixer(), out)

        config = MixConfig(sample_rate=44100, channels=1, tracks=[])
        result = adapter.mix(config)

        import wave

        assert out.exists()
        with wave.open(str(out), "rb") as wf:
            assert wf.getframerate() == 44100
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
        assert result.duration_seconds == 0.0
        assert result.track_count == 0


class TestOutputAdapterExceptions:
    """Tests for OutputAdapter exception propagation."""

    def test_audio_error_propagates(self, tmp_path: Path) -> None:
        """Test that AudioError propagates from the underlying mixer."""

        class FailingMixer:
            def mix(self, config: MixConfig, output_path: Path):
                raise AudioError("mix failed")

        out = tmp_path / "fail.wav"
        adapter = OutputAdapter(FailingMixer(), out)
        with pytest.raises(AudioError, match="mix failed"):
            adapter.mix(MixConfig())
