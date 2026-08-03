"""Tests for core/timeline module."""

import json

import pytest
from pydantic import ValidationError

from core.timeline import (
    InterpolationType,
    Keyframe,
    Time,
    Timeline,
    TimelineDuplicateIDError,
    TimelineError,
    TimelineKeyframeError,
    TimelineMetadata,
    TimelineNotFoundError,
    TimelineSerializationError,
    TimelineSerializer,
    TimelineSettings,
    TimelineTrackError,
    TimelineValidationError,
    TimeRange,
    Track,
    frame_to_seconds,
    seconds_to_frame,
)


class TestTime:
    """Tests for Time class."""

    def test_create_time_defaults(self) -> None:
        """Test creating Time with defaults."""
        t = Time(seconds=1.0, frame_rate=24)
        assert t.seconds == 1.0
        assert t.frame_rate == 24

    def test_time_negative_seconds(self) -> None:
        """Test that negative seconds are rejected."""
        with pytest.raises(ValueError):
            Time(seconds=-1.0, frame_rate=24)

    def test_time_invalid_frame_rate(self) -> None:
        """Test that invalid frame rate is rejected."""
        with pytest.raises(ValueError):
            Time(seconds=1.0, frame_rate=0)

    def test_time_frame_property(self) -> None:
        """Test frame property (truncation)."""
        t = Time(seconds=1.5, frame_rate=24)
        assert t.frame == 36  # 1.5 * 24 = 36

    def test_time_from_frame(self) -> None:
        """Test creating Time from frame."""
        t = Time.from_frame(48, 24)
        assert t.seconds == 2.0
        assert t.frame_rate == 24

    def test_time_negative_frame(self) -> None:
        """Test that negative frame is rejected."""
        with pytest.raises(ValueError):
            Time.from_frame(-1, 24)


class TestTimeRange:
    """Tests for TimeRange class."""

    def test_create_time_range(self) -> None:
        """Test creating TimeRange."""
        tr = TimeRange(start_seconds=0.0, end_seconds=10.0, frame_rate=24)
        assert tr.start_seconds == 0.0
        assert tr.end_seconds == 10.0
        assert tr.duration == 10.0

    def test_time_range_negative_start(self) -> None:
        """Test that negative start is rejected."""
        with pytest.raises(ValueError):
            TimeRange(start_seconds=-1.0, end_seconds=10.0, frame_rate=24)

    def test_time_range_invalid_order(self) -> None:
        """Test that end < start is rejected."""
        with pytest.raises(ValueError):
            TimeRange(start_seconds=10.0, end_seconds=5.0, frame_rate=24)

    def test_time_range_frames(self) -> None:
        """Test frame properties."""
        tr = TimeRange(start_seconds=0.0, end_seconds=2.0, frame_rate=24)
        assert tr.start_frame == 0
        assert tr.end_frame == 48


class TestSecondsFrameConversion:
    """Tests for seconds/frame conversion functions."""

    def test_seconds_to_frame(self) -> None:
        """Test seconds to frame conversion."""
        assert seconds_to_frame(1.0, 24) == 24
        assert seconds_to_frame(1.5, 24) == 36
        assert seconds_to_frame(0.0, 24) == 0

    def test_seconds_to_frame_truncation(self) -> None:
        """Test that conversion truncates."""
        assert seconds_to_frame(1.9, 24) == 45

    def test_seconds_to_frame_negative(self) -> None:
        """Test that negative seconds are rejected."""
        with pytest.raises(ValueError):
            seconds_to_frame(-1.0, 24)

    def test_frame_to_seconds(self) -> None:
        """Test frame to seconds conversion."""
        assert frame_to_seconds(24, 24) == 1.0
        assert frame_to_seconds(48, 24) == 2.0
        assert frame_to_seconds(0, 24) == 0.0

    def test_frame_to_seconds_negative(self) -> None:
        """Test that negative frame is rejected."""
        with pytest.raises(ValueError):
            frame_to_seconds(-1, 24)


class TestInterpolationType:
    """Tests for InterpolationType enum."""

    def test_step_value(self) -> None:
        """Test STEP interpolation value."""
        assert InterpolationType.STEP.value == "step"

    def test_linear_value(self) -> None:
        """Test LINEAR interpolation value."""
        assert InterpolationType.LINEAR.value == "linear"


class TestKeyframe:
    """Tests for Keyframe."""

    def test_create_keyframe_defaults(self) -> None:
        """Test creating Keyframe with defaults."""
        kf = Keyframe(time=1.0, value=100)
        assert kf.time == 1.0
        assert kf.value == 100
        assert kf.interpolation == InterpolationType.LINEAR

    def test_create_keyframe_values(self) -> None:
        """Test creating Keyframe with values."""
        kf = Keyframe(
            time=2.5,
            value=200,
            interpolation=InterpolationType.STEP,
        )
        assert kf.time == 2.5
        assert kf.value == 200
        assert kf.interpolation == InterpolationType.STEP

    def test_negative_time_rejected(self) -> None:
        """Test that negative time is rejected."""
        with pytest.raises(ValueError):
            Keyframe(time=-1.0, value=100)

    def test_is_numeric(self) -> None:
        """Test numeric detection."""
        kf_int = Keyframe(time=0.0, value=100)
        kf_float = Keyframe(time=0.0, value=100.5)
        kf_str = Keyframe(time=0.0, value="hello")
        assert kf_int.is_numeric() is True
        assert kf_float.is_numeric() is True
        assert kf_str.is_numeric() is False

    def test_interpolate_linear(self) -> None:
        """Test LINEAR interpolation."""
        kf1 = Keyframe(time=0.0, value=0, interpolation=InterpolationType.LINEAR)
        kf2 = Keyframe(time=10.0, value=100, interpolation=InterpolationType.LINEAR)
        assert kf1.interpolate_to(kf2, 0.5) == 50

    def test_interpolate_step(self) -> None:
        """Test STEP interpolation."""
        kf1 = Keyframe(time=0.0, value=0, interpolation=InterpolationType.STEP)
        kf2 = Keyframe(time=10.0, value=100, interpolation=InterpolationType.STEP)
        assert kf1.interpolate_to(kf2, 0.5) == 0

    def test_keyframe_sorting(self) -> None:
        """Test keyframe comparison for sorting."""
        kf1 = Keyframe(time=1.0, value=100)
        kf2 = Keyframe(time=0.0, value=50)
        assert kf2 < kf1


class TestTrack:
    """Tests for Track."""

    def test_create_track_defaults(self) -> None:
        """Test creating Track with defaults."""
        track = Track()
        assert track.id is not None
        assert track.name == ""
        assert track.keyframes == []

    def test_create_track_values(self) -> None:
        """Test creating Track with values."""
        track = Track(
            name="Position Track",
            target_id="character_01",
            property_name="position",
        )
        assert track.name == "Position Track"
        assert track.target_id == "character_01"
        assert track.property_name == "position"

    def test_add_keyframe(self) -> None:
        """Test adding keyframe to track."""
        track = Track()
        kf = Keyframe(time=1.0, value=100)
        added = track.add_keyframe(kf)
        assert kf in track.keyframes
        assert added == kf

    def test_add_duplicate_time_replaces(self) -> None:
        """Test that adding keyframe at same time replaces."""
        track = Track()
        kf1 = Keyframe(time=1.0, value=100)
        kf2 = Keyframe(time=1.0, value=200)
        track.add_keyframe(kf1)
        track.add_keyframe(kf2)
        assert len(track.keyframes) == 1
        assert track.keyframes[0].value == 200

    def test_remove_keyframe(self) -> None:
        """Test removing keyframe."""
        track = Track()
        kf = Keyframe(time=1.0, value=100)
        track.add_keyframe(kf)
        removed = track.remove_keyframe(1.0)
        assert removed.value == 100
        assert len(track.keyframes) == 0

    def test_remove_nonexistent_keyframe(self) -> None:
        """Test removing nonexistent keyframe raises error."""
        track = Track()
        with pytest.raises(TimelineNotFoundError):
            track.remove_keyframe(1.0)

    def test_get_keyframe(self) -> None:
        """Test getting keyframe."""
        track = Track()
        kf = Keyframe(time=1.0, value=100)
        track.add_keyframe(kf)
        retrieved = track.get_keyframe(1.0)
        assert retrieved.value == 100

    def test_update_keyframe(self) -> None:
        """Test updating keyframe."""
        track = Track()
        kf = Keyframe(time=1.0, value=100)
        track.add_keyframe(kf)
        updated = track.update_keyframe(1.0, value=200)
        assert updated.value == 200

    def test_evaluate_empty_track(self) -> None:
        """Test evaluating empty track returns None."""
        track = Track()
        assert track.evaluate(1.0) is None

    def test_evaluate_before_first_keyframe(self) -> None:
        """Test evaluation before first keyframe returns first value."""
        track = Track()
        track.add_keyframe(Keyframe(time=1.0, value=100))
        track.add_keyframe(Keyframe(time=2.0, value=200))
        assert track.evaluate(0.5) == 100

    def test_evaluate_after_last_keyframe(self) -> None:
        """Test evaluation after last keyframe returns last value."""
        track = Track()
        track.add_keyframe(Keyframe(time=1.0, value=100))
        track.add_keyframe(Keyframe(time=2.0, value=200))
        assert track.evaluate(3.0) == 200

    def test_evaluate_on_keyframe(self) -> None:
        """Test evaluation exactly on keyframe."""
        track = Track()
        track.add_keyframe(Keyframe(time=1.0, value=100))
        track.add_keyframe(Keyframe(time=2.0, value=200))
        assert track.evaluate(1.0) == 100

    def test_evaluate_linear_interpolation(self) -> None:
        """Test LINEAR interpolation between keyframes."""
        track = Track()
        track.add_keyframe(Keyframe(time=0.0, value=0))
        track.add_keyframe(Keyframe(time=10.0, value=100))
        assert track.evaluate(5.0) == 50

    def test_evaluate_step_interpolation(self) -> None:
        """Test STEP interpolation."""
        track = Track()
        track.add_keyframe(Keyframe(time=0.0, value=0, interpolation=InterpolationType.STEP))
        track.add_keyframe(Keyframe(time=10.0, value=100))
        assert track.evaluate(5.0) == 0

    def test_keyframes_sorted(self) -> None:
        """Test that keyframes are kept sorted."""
        track = Track()
        track.add_keyframe(Keyframe(time=3.0, value=300))
        track.add_keyframe(Keyframe(time=1.0, value=100))
        track.add_keyframe(Keyframe(time=2.0, value=200))
        times = [kf.time for kf in track.keyframes]
        assert times == [1.0, 2.0, 3.0]


class TestTimeline:
    """Tests for Timeline."""

    def test_create_timeline_defaults(self) -> None:
        """Test creating Timeline with defaults."""
        timeline = Timeline()
        assert timeline.id is not None
        assert timeline.frame_rate == 24
        assert timeline.duration == 10.0
        assert timeline.tracks == {}

    def test_create_timeline_values(self) -> None:
        """Test creating Timeline with values."""
        timeline = Timeline(
            metadata=TimelineMetadata(name="Test Timeline"),
            settings=TimelineSettings(frame_rate=30, duration=60.0),
        )
        assert timeline.metadata.name == "Test Timeline"
        assert timeline.frame_rate == 30
        assert timeline.duration == 60.0

    def test_timeline_unique_id(self) -> None:
        """Test that each timeline gets unique ID."""
        t1 = Timeline()
        t2 = Timeline()
        assert t1.id != t2.id

    def test_total_frames(self) -> None:
        """Test total frames calculation."""
        timeline = Timeline(settings=TimelineSettings(frame_rate=24, duration=2.0))
        assert timeline.total_frames == 48

    def test_add_track(self) -> None:
        """Test adding track to timeline."""
        timeline = Timeline()
        track = Track(name="Position")
        added = timeline.add_track(track)
        assert track.id in timeline.tracks
        assert added == track

    def test_add_duplicate_track_rejected(self) -> None:
        """Test that adding duplicate track ID is rejected."""
        timeline = Timeline()
        track = Track(id="same-id")
        timeline.add_track(track)
        with pytest.raises(TimelineDuplicateIDError):
            timeline.add_track(Track(id="same-id"))

    def test_remove_track(self) -> None:
        """Test removing track."""
        timeline = Timeline()
        track = Track(id="track-1")
        timeline.add_track(track)
        timeline.remove_track("track-1")
        assert "track-1" not in timeline.tracks

    def test_remove_nonexistent_track(self) -> None:
        """Test removing nonexistent track raises error."""
        timeline = Timeline()
        with pytest.raises(TimelineNotFoundError):
            timeline.remove_track("nonexistent")

    def test_get_track(self) -> None:
        """Test getting track."""
        timeline = Timeline()
        track = Track(id="track-1", name="Test")
        timeline.add_track(track)
        retrieved = timeline.get_track("track-1")
        assert retrieved.name == "Test"

    def test_has_track(self) -> None:
        """Test checking track existence."""
        timeline = Timeline()
        track = Track(id="track-1")
        timeline.add_track(track)
        assert timeline.has_track("track-1") is True
        assert timeline.has_track("nonexistent") is False

    def test_update_track(self) -> None:
        """Test updating track."""
        timeline = Timeline()
        track = Track(id="track-1", name="Original")
        timeline.add_track(track)
        updated = timeline.update_track("track-1", name="Updated")
        assert updated.name == "Updated"

    def test_evaluate(self) -> None:
        """Test timeline evaluation."""
        timeline = Timeline()
        track = Track(id="track-1")
        track.add_keyframe(Keyframe(time=0.0, value=0))
        track.add_keyframe(Keyframe(time=10.0, value=100))
        timeline.add_track(track)

        result = timeline.evaluate(5.0)
        assert result["track-1"] == 50

    def test_evaluate_frame(self) -> None:
        """Test timeline evaluation by frame."""
        timeline = Timeline(settings=TimelineSettings(frame_rate=24))
        track = Track(id="track-1")
        track.add_keyframe(Keyframe(time=0.0, value=0))
        track.add_keyframe(Keyframe(time=1.0, value=24))
        timeline.add_track(track)

        result = timeline.evaluate_frame(12)  # 0.5 seconds at 24fps
        assert result["track-1"] == 12

    def test_get_tracks(self) -> None:
        """Test getting all tracks."""
        timeline = Timeline()
        timeline.add_track(Track(id="t1"))
        timeline.add_track(Track(id="t2"))
        tracks = timeline.get_tracks()
        assert len(tracks) == 2


class TestTimelineValidation:
    """Tests for timeline validation."""

    def test_validate_valid_timeline(self) -> None:
        """Test validating a valid timeline."""
        timeline = Timeline(metadata=TimelineMetadata(name="Valid"))
        errors = timeline.validate()
        assert errors == []

    def test_validate_invalid_frame_rate_rejected(self) -> None:
        """Test that invalid frame rate is rejected at creation."""
        with pytest.raises(ValidationError):
            Timeline(settings=TimelineSettings(frame_rate=0))

    def test_validate_negative_duration_rejected(self) -> None:
        """Test that negative duration is rejected at creation."""
        with pytest.raises(ValidationError):
            Timeline(settings=TimelineSettings(duration=-1.0))

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise works for valid timeline."""
        timeline = Timeline(metadata=TimelineMetadata(name="Valid"))
        timeline.validate_or_raise()  # Should not raise


class TestTimelineSerialization:
    """Tests for timeline serialization."""

    def test_serialize_empty_timeline(self) -> None:
        """Test serializing empty timeline."""
        timeline = Timeline()
        data = TimelineSerializer.serialize(timeline)
        assert data["id"] == timeline.id
        assert data["tracks"] == {}

    def test_serialize_timeline_with_tracks(self) -> None:
        """Test serializing timeline with tracks."""
        timeline = Timeline(metadata=TimelineMetadata(name="Test"))
        track = Track(id="track-1", name="Position", property_name="position")
        track.add_keyframe(Keyframe(time=0.0, value=0))
        track.add_keyframe(Keyframe(time=10.0, value=100))
        timeline.add_track(track)

        data = TimelineSerializer.serialize(timeline)
        assert "track-1" in data["tracks"]
        assert len(data["tracks"]["track-1"]["keyframes"]) == 2

    def test_deserialize_timeline(self) -> None:
        """Test deserializing timeline."""
        timeline = Timeline(metadata=TimelineMetadata(name="Original"))
        data = TimelineSerializer.serialize(timeline)
        restored = TimelineSerializer.deserialize(data)
        assert restored.id == timeline.id
        assert restored.metadata.name == "Original"

    def test_roundtrip_preservation(self) -> None:
        """Test serialization roundtrip preserves data."""
        timeline = Timeline(metadata=TimelineMetadata(name="Roundtrip Test"))
        track = Track(id="track-1", name="Test Track", property_name="position")
        track.add_keyframe(Keyframe(time=0.0, value=0, interpolation=InterpolationType.STEP))
        track.add_keyframe(Keyframe(time=5.0, value=100))
        timeline.add_track(track)

        data = TimelineSerializer.serialize(timeline)
        restored = TimelineSerializer.deserialize(data)

        assert restored.id == timeline.id
        assert restored.metadata.name == "Roundtrip Test"
        assert "track-1" in restored.tracks
        restored_track = restored.tracks["track-1"]
        assert restored_track.name == "Test Track"
        assert len(restored_track.keyframes) == 2
        assert restored_track.keyframes[0].interpolation == InterpolationType.STEP

    def test_to_json(self) -> None:
        """Test serializing to JSON."""
        timeline = Timeline(metadata=TimelineMetadata(name="JSON Test"))
        json_str = TimelineSerializer.to_json(timeline)
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "JSON Test"

    def test_from_json(self) -> None:
        """Test deserializing from JSON."""
        timeline = Timeline(metadata=TimelineMetadata(name="JSON Test"))
        json_str = TimelineSerializer.to_json(timeline)
        restored = TimelineSerializer.from_json(json_str)
        assert restored.metadata.name == "JSON Test"

    def test_deserialize_invalid_data(self) -> None:
        """Test deserializing invalid data raises error."""
        with pytest.raises(TimelineSerializationError, match="Missing required field"):
            TimelineSerializer.deserialize({})

    def test_from_invalid_json(self) -> None:
        """Test from_json raises error for invalid JSON."""
        with pytest.raises(TimelineSerializationError, match="Invalid JSON"):
            TimelineSerializer.from_json("not valid json {{{")


class TestTimelineExceptions:
    """Tests for timeline exceptions."""

    def test_validation_error_with_errors(self) -> None:
        """Test TimelineValidationError contains error list."""
        error = TimelineValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)

    def test_exception_hierarchy(self) -> None:
        """Test exception hierarchy."""
        assert issubclass(TimelineTrackError, TimelineError)
        assert issubclass(TimelineKeyframeError, TimelineError)
        assert issubclass(TimelineNotFoundError, TimelineTrackError)
        assert issubclass(TimelineDuplicateIDError, TimelineTrackError)

    def test_exception_raising(self) -> None:
        """Test exceptions can be raised."""
        with pytest.raises(TimelineNotFoundError):
            raise TimelineNotFoundError("Not found")

        with pytest.raises(TimelineDuplicateIDError):
            raise TimelineDuplicateIDError("Duplicate ID")

        with pytest.raises(TimelineKeyframeError):
            raise TimelineKeyframeError("Keyframe error")
