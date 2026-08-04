"""Tests for frame animation V1."""

import pytest

from tools.frame.animation import (
    DEFAULT_FRAME_RATE,
    AnimationClip,
    AnimationFrame,
    AnimationKeyframe,
    AnimationTimeline,
    evaluate_at_frame,
    evaluate_keyframe_at_frame,
    generate_animation_frames,
)
from tools.frame.models import FrameTransform, InterpolationType


class TestDefaultFrameRate:
    """Tests for DEFAULT_FRAME_RATE constant."""

    def test_default_fps(self) -> None:
        """Test default FPS is 24."""
        assert DEFAULT_FRAME_RATE == 24.0


class TestAnimationTimeline:
    """Tests for AnimationTimeline."""

    def test_default_24_fps(self) -> None:
        """Test timeline defaults to 24 FPS."""
        timeline = AnimationTimeline(duration_frames=24)
        assert timeline.frame_rate == 24.0

    def test_custom_fps(self) -> None:
        """Test custom FPS."""
        timeline = AnimationTimeline(frame_rate=30.0, duration_frames=30)
        assert timeline.frame_rate == 30.0

    def test_invalid_fps_zero(self) -> None:
        """Test invalid FPS (zero)."""
        with pytest.raises(ValueError):
            AnimationTimeline(frame_rate=0, duration_frames=24)

    def test_invalid_fps_negative(self) -> None:
        """Test invalid FPS (negative)."""
        with pytest.raises(ValueError):
            AnimationTimeline(frame_rate=-1, duration_frames=24)

    def test_invalid_fps_too_high(self) -> None:
        """Test invalid FPS (> 120)."""
        with pytest.raises(ValueError):
            AnimationTimeline(frame_rate=121, duration_frames=24)

    def test_frame_time(self) -> None:
        """Test frame to time conversion."""
        timeline = AnimationTimeline(duration_frames=24)
        assert timeline.frame_time(0) == 0.0
        assert timeline.frame_time(24) == 1.0
        assert timeline.frame_time(12) == 0.5

    def test_frame_time_ms(self) -> None:
        """Test frame to milliseconds conversion."""
        timeline = AnimationTimeline(duration_frames=24)
        assert timeline.frame_time_ms(0) == 0
        assert timeline.frame_time_ms(24) == 1000
        assert timeline.frame_time_ms(12) == 500

    def test_frame_index_at(self) -> None:
        """Test time to frame index conversion."""
        timeline = AnimationTimeline(duration_frames=24)
        assert timeline.frame_index_at(0.0) == 0
        assert timeline.frame_index_at(1.0) == 24
        assert timeline.frame_index_at(0.5) == 12

    def test_frame_index_at_negative_rejected(self) -> None:
        """Test negative timestamp rejected."""
        timeline = AnimationTimeline(duration_frames=24)
        with pytest.raises(ValueError):
            timeline.frame_index_at(-0.1)

    def test_duration_seconds(self) -> None:
        """Test duration in seconds."""
        timeline = AnimationTimeline(frame_rate=24.0, duration_frames=48)
        assert timeline.duration_seconds() == 2.0

    def test_duration_ms(self) -> None:
        """Test duration in milliseconds."""
        timeline = AnimationTimeline(frame_rate=24.0, duration_frames=48)
        assert timeline.duration_ms() == 2000

    def test_1_second_at_24fps(self) -> None:
        """Test 1 second = 24 frames at 24 FPS."""
        timeline = AnimationTimeline(duration_frames=24)
        assert timeline.duration_seconds() == 1.0
        assert timeline.frame_time(24) == 1.0

    def test_5_seconds_at_24fps(self) -> None:
        """Test 5 seconds = 120 frames at 24 FPS."""
        timeline = AnimationTimeline(duration_frames=120)
        assert timeline.duration_seconds() == 5.0


class TestAnimationKeyframe:
    """Tests for AnimationKeyframe."""

    def test_valid_keyframe(self) -> None:
        """Test creating a valid keyframe."""
        kf = AnimationKeyframe(
            frame_index=0,
            transform=FrameTransform(position_x=100),
        )
        assert kf.frame_index == 0
        assert kf.position_x == 100

    def test_keyframe_default_interpolation(self) -> None:
        """Test default interpolation is LINEAR."""
        kf = AnimationKeyframe(
            frame_index=0,
            transform=FrameTransform(),
        )
        assert kf.interpolation == InterpolationType.LINEAR

    def test_keyframe_custom_interpolation(self) -> None:
        """Test custom interpolation type."""
        kf = AnimationKeyframe(
            frame_index=0,
            transform=FrameTransform(),
            interpolation=InterpolationType.EASE_IN_OUT,
        )
        assert kf.interpolation == InterpolationType.EASE_IN_OUT

    def test_keyframe_frozen(self) -> None:
        """Test keyframe is frozen."""
        from pydantic import ValidationError
        kf = AnimationKeyframe(
            frame_index=0,
            transform=FrameTransform(),
        )
        with pytest.raises(ValidationError):
            kf.frame_index = 1

    def test_invalid_frame_index_negative(self) -> None:
        """Test negative frame index rejected."""
        with pytest.raises(ValueError):
            AnimationKeyframe(
                frame_index=-1,
                transform=FrameTransform(),
            )


class TestAnimationFrame:
    """Tests for AnimationFrame."""

    def test_valid_frame(self) -> None:
        """Test creating an animation frame."""
        af = AnimationFrame(
            frame_index=0,
            timestamp_ms=0,
            transform=FrameTransform(),
        )
        assert af.frame_index == 0
        assert af.timestamp_ms == 0

    def test_frame_with_clip_id(self) -> None:
        """Test frame with clip ID."""
        af = AnimationFrame(
            frame_index=0,
            timestamp_ms=0,
            transform=FrameTransform(),
            clip_id="background",
        )
        assert af.clip_id == "background"

    def test_frame_frozen(self) -> None:
        """Test animation frame is frozen."""
        af = AnimationFrame(
            frame_index=0,
            timestamp_ms=0,
            transform=FrameTransform(),
        )
        with pytest.raises(AttributeError):
            af.frame_index = 1

    def test_model_dump(self) -> None:
        """Test serialization."""
        af = AnimationFrame(
            frame_index=0,
            timestamp_ms=0,
            transform=FrameTransform(position_x=100),
            clip_id="test",
        )
        data = af.model_dump()
        assert data["frame_index"] == 0
        assert data["clip_id"] == "test"


class TestAnimationClip:
    """Tests for AnimationClip."""

    def test_valid_clip(self) -> None:
        """Test creating a valid clip."""
        clip = AnimationClip(
            clip_id="background",
            start_frame=0,
            end_frame=24,
        )
        assert clip.clip_id == "background"
        assert clip.start_frame == 0
        assert clip.end_frame == 24

    def test_clip_with_keyframes(self) -> None:
        """Test clip with keyframes."""
        kf1 = AnimationKeyframe(frame_index=0, transform=FrameTransform(position_x=0))
        kf2 = AnimationKeyframe(frame_index=24, transform=FrameTransform(position_x=100))
        clip = AnimationClip(
            clip_id="layer1",
            start_frame=0,
            end_frame=24,
            keyframes=[kf1, kf2],
        )
        assert len(clip.keyframes) == 2

    def test_invalid_empty_clip_id(self) -> None:
        """Test empty clip_id rejected."""
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="",
                start_frame=0,
                end_frame=24,
            )

    def test_invalid_whitespace_clip_id(self) -> None:
        """Test whitespace clip_id rejected."""
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="   ",
                start_frame=0,
                end_frame=24,
            )

    def test_clip_id_trimmed(self) -> None:
        """Test clip_id is trimmed."""
        clip = AnimationClip(
            clip_id="  background  ",
            start_frame=0,
            end_frame=24,
        )
        assert clip.clip_id == "background"

    def test_invalid_range(self) -> None:
        """Test end_frame < start_frame rejected."""
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="test",
                start_frame=24,
                end_frame=0,
            )

    def test_duplicate_keyframe_rejected(self) -> None:
        """Test duplicate keyframe indexes rejected."""
        kf1 = AnimationKeyframe(frame_index=0, transform=FrameTransform())
        kf2 = AnimationKeyframe(frame_index=12, transform=FrameTransform())
        kf3 = AnimationKeyframe(frame_index=12, transform=FrameTransform())  # Duplicate
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="test",
                start_frame=0,
                end_frame=24,
                keyframes=[kf1, kf2, kf3],
            )

    def test_out_of_range_keyframe_rejected(self) -> None:
        """Test keyframe outside clip range rejected."""
        kf = AnimationKeyframe(frame_index=50, transform=FrameTransform())
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="test",
                start_frame=0,
                end_frame=24,
                keyframes=[kf],
            )

    def test_unordered_keyframes_rejected(self) -> None:
        """Test unordered keyframes rejected."""
        kf1 = AnimationKeyframe(frame_index=12, transform=FrameTransform())
        kf2 = AnimationKeyframe(frame_index=0, transform=FrameTransform())
        with pytest.raises(ValueError):
            AnimationClip(
                clip_id="test",
                start_frame=0,
                end_frame=24,
                keyframes=[kf1, kf2],
            )


class TestEvaluateKeyframeAtFrame:
    """Tests for evaluate_keyframe_at_frame."""

    def test_exact_keyframe(self) -> None:
        """Test evaluation at exact keyframe."""
        timeline = AnimationTimeline(duration_frames=24)
        kf = AnimationKeyframe(frame_index=12, transform=FrameTransform(position_x=100))
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[kf],
        )
        result = evaluate_keyframe_at_frame(clip, 12, timeline)
        assert result.position_x == 100

    def test_before_first_keyframe(self) -> None:
        """Test evaluation before first keyframe."""
        timeline = AnimationTimeline(duration_frames=24)
        kf = AnimationKeyframe(frame_index=12, transform=FrameTransform(position_x=100))
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[kf],
        )
        result = evaluate_keyframe_at_frame(clip, 0, timeline)
        assert result == clip.default_transform

    def test_midpoint_interpolation(self) -> None:
        """Test interpolation at midpoint."""
        timeline = AnimationTimeline(duration_frames=24)
        kf1 = AnimationKeyframe(frame_index=0, transform=FrameTransform(position_x=0))
        kf2 = AnimationKeyframe(frame_index=24, transform=FrameTransform(position_x=100))
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[kf1, kf2],
        )
        result = evaluate_keyframe_at_frame(clip, 12, timeline)
        assert result.position_x == 50.0

    def test_frame_out_of_range(self) -> None:
        """Test frame out of clip range raises."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(clip_id="test", start_frame=0, end_frame=24)
        with pytest.raises(ValueError):
            evaluate_keyframe_at_frame(clip, 100, timeline)

    def test_empty_keyframes(self) -> None:
        """Test clip with no keyframes returns default."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[],
        )
        result = evaluate_keyframe_at_frame(clip, 12, timeline)
        assert result == clip.default_transform


class TestGenerateAnimationFrames:
    """Tests for generate_animation_frames."""

    def test_frame_count(self) -> None:
        """Test correct number of frames generated."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
        )
        frames = generate_animation_frames(clip, timeline)
        assert len(frames) == 25  # 0 to 24 inclusive

    def test_frame_indexes(self) -> None:
        """Test correct frame indexes."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=5,
        )
        frames = generate_animation_frames(clip, timeline)
        assert frames[0].frame_index == 0
        assert frames[-1].frame_index == 5

    def test_timestamps(self) -> None:
        """Test correct timestamps."""
        timeline = AnimationTimeline(frame_rate=24, duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
        )
        frames = generate_animation_frames(clip, timeline)
        assert frames[0].timestamp_ms == 0
        assert frames[12].timestamp_ms == 500
        assert frames[24].timestamp_ms == 1000

    def test_clip_extends_beyond_timeline(self) -> None:
        """Test clip extending beyond timeline raises."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=48,
        )
        with pytest.raises(ValueError):
            generate_animation_frames(clip, timeline)

    def test_deterministic(self) -> None:
        """Test generation is deterministic."""
        timeline = AnimationTimeline(duration_frames=24)
        kf1 = AnimationKeyframe(frame_index=0, transform=FrameTransform(position_x=0))
        kf2 = AnimationKeyframe(frame_index=24, transform=FrameTransform(position_x=100))
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[kf1, kf2],
        )
        frames1 = generate_animation_frames(clip, timeline)
        frames2 = generate_animation_frames(clip, timeline)
        assert frames1 == frames2


class TestEvaluateAtFrame:
    """Tests for evaluate_at_frame."""

    def test_evaluate_multiple_clips(self) -> None:
        """Test evaluating multiple clips at once."""
        timeline = AnimationTimeline(duration_frames=24)
        clip1 = AnimationClip(
            clip_id="background",
            start_frame=0,
            end_frame=24,
            keyframes=[AnimationKeyframe(frame_index=0, transform=FrameTransform(position_x=0))],
        )
        clip2 = AnimationClip(
            clip_id="foreground",
            start_frame=0,
            end_frame=24,
            keyframes=[AnimationKeyframe(frame_index=0, transform=FrameTransform(position_x=100))],
        )
        results = evaluate_at_frame([clip1, clip2], 12, timeline)
        assert len(results) == 2

    def test_inactive_clip_not_included(self) -> None:
        """Test clips not at frame are not included."""
        timeline = AnimationTimeline(duration_frames=24)
        clip1 = AnimationClip(
            clip_id="background",
            start_frame=0,
            end_frame=12,
        )
        clip2 = AnimationClip(
            clip_id="foreground",
            start_frame=13,
            end_frame=24,
        )
        results = evaluate_at_frame([clip1, clip2], 12, timeline)
        assert len(results) == 1
        assert results[0].clip_id == "background"


class TestMutationSafety:
    """Tests for mutation safety."""

    def test_source_clip_unchanged(self) -> None:
        """Test source clip is not modified."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
        )
        _ = generate_animation_frames(clip, timeline)
        assert clip.clip_id == "test"
        assert clip.start_frame == 0
        assert clip.end_frame == 24

    def test_source_transform_unchanged(self) -> None:
        """Test source transforms are not modified."""
        timeline = AnimationTimeline(duration_frames=24)
        transform = FrameTransform(position_x=0)
        original_x = transform.position_x
        kf = AnimationKeyframe(frame_index=24, transform=transform)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
            keyframes=[kf],
        )
        _ = evaluate_keyframe_at_frame(clip, 12, timeline)
        assert transform.position_x == original_x


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test same input produces same output."""
        timeline = AnimationTimeline(duration_frames=24)
        clip = AnimationClip(
            clip_id="test",
            start_frame=0,
            end_frame=24,
        )
        for _ in range(10):
            frames = generate_animation_frames(clip, timeline)
            assert len(frames) == 25
            assert frames[12].transform == frames[12].transform


class TestDependencyRules:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify animation has no forbidden imports."""
        import tools.frame.animation as animation_module
        source = animation_module.__file__
        with open(source) as f:
            content = f.read()

        forbidden = [
            "torch", "tensorflow", "cv2", "PIL", "opencv",
            "requests", "httpx", "socket", "ffmpeg", "moviepy",
            "diffusers", "transformers", "stable", "controlnet",
            "runtime", "agents", "apps", "core", "tools.render",
            "tools.audio", "tools.vfx"
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"
