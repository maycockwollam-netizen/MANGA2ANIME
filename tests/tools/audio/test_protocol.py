"""Tests for audio mixer protocol contract."""

import pytest

from tools.audio import (
    AudioConfigError,
    AudioError,
    AudioMixer,
    AudioMixError,
    AudioTrackError,
    MixConfig,
    MixResult,
    WaveMixer,
)


class TestAudioMixerProtocolCompliance:
    """Tests for AudioMixer protocol structural typing."""

    def test_wave_mixer_satisfies_protocol(self) -> None:
        """Test that WaveMixer satisfies the AudioMixer protocol."""
        assert isinstance(WaveMixer(), AudioMixer)

    def test_class_without_mix_method_does_not_satisfy(self) -> None:
        """Test that a class without mix method does not satisfy AudioMixer."""

        class NotAMixer:
            def render(self, config: MixConfig) -> MixResult:  # pragma: no cover
                ...

        assert not isinstance(NotAMixer(), AudioMixer)

    def test_audio_mixer_is_runtime_checkable(self) -> None:
        """Test that isinstance() works at runtime for AudioMixer."""
        assert isinstance(WaveMixer(), AudioMixer)
        assert not isinstance("not a mixer", AudioMixer)
        assert not isinstance(123, AudioMixer)

    def test_audio_mixer_protocol_is_type(self) -> None:
        """Test that AudioMixer itself is a type/class."""
        assert isinstance(AudioMixer, type)


class TestAudioMixerImports:
    """Tests for audio module imports."""

    def test_audio_mixer_importable(self) -> None:
        """Test AudioMixer is importable from tools.audio."""
        assert AudioMixer is not None

    def test_wave_mixer_importable(self) -> None:
        """Test WaveMixer is importable from tools.audio."""
        assert WaveMixer is not None

    def test_audio_error_hierarchy(self) -> None:
        """Test audio exception hierarchy."""
        assert issubclass(AudioConfigError, AudioError)
        assert issubclass(AudioTrackError, AudioError)
        assert issubclass(AudioMixError, AudioError)

    def test_audio_errors_can_be_raised(self) -> None:
        """Test that audio exceptions can be raised."""
        with pytest.raises(AudioError):
            raise AudioError("test")
        with pytest.raises(AudioConfigError):
            raise AudioConfigError("config")
        with pytest.raises(AudioTrackError):
            raise AudioTrackError("track")
        with pytest.raises(AudioMixError):
            raise AudioMixError("mix")
