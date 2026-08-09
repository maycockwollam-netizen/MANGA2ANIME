"""Tests for audio data models."""

import pytest
from pydantic import ValidationError

from tools.audio import AudioTrack, MixConfig, MixResult


class TestAudioTrack:
    """Tests for AudioTrack model."""

    def test_defaults(self) -> None:
        """Test AudioTrack default values."""
        from pathlib import Path

        track = AudioTrack(track_id="bgm", source_path=Path("/tmp/a.wav"))
        assert track.start_time == 0.0
        assert track.gain == 1.0

    def test_track_id_trimmed(self) -> None:
        """Test that track_id is stripped of surrounding whitespace."""
        from pathlib import Path

        track = AudioTrack(track_id="  bgm  ", source_path=Path("/tmp/a.wav"))
        assert track.track_id == "bgm"

    def test_empty_track_id_rejected(self) -> None:
        """Test that empty track_id is rejected."""
        from pathlib import Path

        with pytest.raises(ValidationError):
            AudioTrack(track_id="   ", source_path=Path("/tmp/a.wav"))

    def test_negative_start_time_rejected(self) -> None:
        """Test that negative start_time is rejected."""
        from pathlib import Path

        with pytest.raises(ValidationError):
            AudioTrack(track_id="bgm", source_path=Path("/tmp/a.wav"), start_time=-0.1)

    def test_negative_gain_rejected(self) -> None:
        """Test that negative gain is rejected."""
        from pathlib import Path

        with pytest.raises(ValidationError):
            AudioTrack(track_id="bgm", source_path=Path("/tmp/a.wav"), gain=-0.1)

    def test_zero_gain_allowed(self) -> None:
        """Test that zero gain (muted) is allowed."""
        from pathlib import Path

        track = AudioTrack(track_id="bgm", source_path=Path("/tmp/a.wav"), gain=0.0)
        assert track.gain == 0.0


class TestMixConfig:
    """Tests for MixConfig model."""

    def test_defaults(self) -> None:
        """Test MixConfig default values."""
        config = MixConfig()
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.tracks == ()
        assert config.master_gain == 1.0

    def test_is_frozen(self) -> None:
        """Test that MixConfig is immutable."""
        config = MixConfig()
        with pytest.raises(ValidationError):
            config.sample_rate = 48000  # type: ignore[misc]

    def test_channels_must_be_1_or_2(self) -> None:
        """Test that channels must be 1 or 2."""
        with pytest.raises(ValidationError):
            MixConfig(channels=0)
        with pytest.raises(ValidationError):
            MixConfig(channels=3)

    def test_sample_rate_must_be_positive(self) -> None:
        """Test that sample rate must be positive."""
        with pytest.raises(ValidationError):
            MixConfig(sample_rate=0)

    def test_tracks_list_converted_to_tuple(self) -> None:
        """Test that a list of tracks is converted to a tuple."""
        from pathlib import Path

        t1 = AudioTrack(track_id="a", source_path=Path("/tmp/a.wav"))
        config = MixConfig(tracks=[t1])
        assert isinstance(config.tracks, tuple)
        assert len(config.tracks) == 1

    def test_duplicate_track_ids_rejected(self) -> None:
        """Test that duplicate track_ids are rejected."""
        from pathlib import Path

        t1 = AudioTrack(track_id="dup", source_path=Path("/tmp/a.wav"))
        t2 = AudioTrack(track_id="dup", source_path=Path("/tmp/b.wav"))
        with pytest.raises(ValidationError, match="duplicate track_id"):
            MixConfig(tracks=[t1, t2])

    def test_unique_track_ids_accepted(self) -> None:
        """Test that unique track_ids are accepted."""
        from pathlib import Path

        t1 = AudioTrack(track_id="a", source_path=Path("/tmp/a.wav"))
        t2 = AudioTrack(track_id="b", source_path=Path("/tmp/b.wav"))
        config = MixConfig(tracks=[t1, t2])
        assert len(config.tracks) == 2


class TestMixResult:
    """Tests for MixResult model."""

    def test_valid_result(self) -> None:
        """Test that a valid MixResult can be constructed."""
        from pathlib import Path

        result = MixResult(
            output_path=Path("/tmp/out.wav"),
            sample_rate=44100,
            channels=2,
            duration_seconds=1.5,
            track_count=3,
        )
        assert result.track_count == 3
        assert result.duration_seconds == 1.5

    def test_is_frozen(self) -> None:
        """Test that MixResult is immutable."""
        from pathlib import Path

        result = MixResult(
            output_path=Path("/tmp/out.wav"),
            sample_rate=44100,
            channels=2,
            duration_seconds=1.5,
            track_count=3,
        )
        with pytest.raises(ValidationError):
            result.track_count = 0  # type: ignore[misc]
