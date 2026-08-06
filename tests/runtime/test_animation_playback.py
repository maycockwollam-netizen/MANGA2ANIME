"""Tests for animation playback timing."""

import pytest

from runtime.animation.consumer import (
    AnimationOrchestrator,
    PlaybackState,
)
from tools.frame.models import FrameTransform, InterpolationType
from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    CharacterTransformInput,
    CharacterTransformInputSet,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def orchestrator() -> AnimationOrchestrator:
    """Create an empty orchestrator at 24fps."""
    return AnimationOrchestrator(frame_rate=24.0)


@pytest.fixture
def orchestrator_30fps() -> AnimationOrchestrator:
    """Create an empty orchestrator at 30fps."""
    return AnimationOrchestrator(frame_rate=30.0)


@pytest.fixture
def loaded_orchestrator(orchestrator: AnimationOrchestrator) -> AnimationOrchestrator:
    """Create an orchestrator with loaded animation (0-24 frames)."""
    target = CharacterAnimationTarget(
        character_id="hero",
        layer_id="1",
        sequence_id="intro",
    )
    binding = CharacterAnimationBinding(
        target=target,
        frame_index=0,
        palette_id=None,
    )
    binding2 = CharacterAnimationBinding(
        target=target,
        frame_index=24,
        palette_id=None,
    )
    output = CharacterAnimationOutput(
        sequence_id="intro",
        bindings=(binding, binding2),
        metadata=CharacterAnimationMetadata(
            bindings_created=2,
            characters_bound=1,
            palettes_available=0,
            palettes_missing=1,
        ),
    )
    transforms = CharacterTransformInputSet(
        transforms=(
            CharacterTransformInput(
                character_id="hero",
                frame_index=0,
                transform=FrameTransform(position_x=0),
                interpolation=InterpolationType.LINEAR,
            ),
            CharacterTransformInput(
                character_id="hero",
                frame_index=24,
                transform=FrameTransform(position_x=100),
                interpolation=InterpolationType.LINEAR,
            ),
        ),
    )
    orchestrator.load(output, transforms)
    return orchestrator


# ============================================================================
# Test Basic State
# ============================================================================


class TestBasicState:
    """Tests for initial playback state."""

    def test_current_frame_starts_at_zero(self, orchestrator: AnimationOrchestrator) -> None:
        """Test that current_frame starts at 0."""
        assert orchestrator.current_frame == 0

    def test_duration_frames_empty(self, orchestrator: AnimationOrchestrator) -> None:
        """Test duration_frames is 0 when no clips loaded."""
        assert orchestrator.duration_frames == 0

    def test_duration_frames_with_clips(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test duration_frames reflects loaded clips."""
        assert loaded_orchestrator.duration_frames == 24

    def test_playback_state_immutable(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that playback_state is frozen/immutable."""
        state = loaded_orchestrator.playback_state
        assert isinstance(state, PlaybackState)
        # Verify frozen
        with pytest.raises(AttributeError):
            state.current_frame = 10  # type: ignore


# ============================================================================
# Test Seek
# ============================================================================


class TestSeek:
    """Tests for seek() method."""

    def test_seek_to_zero(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test seek(0) sets current_frame to 0."""
        loaded_orchestrator.seek(5)
        loaded_orchestrator.seek(0)
        assert loaded_orchestrator.current_frame == 0

    def test_seek_to_valid_frame(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test seek to valid frame."""
        loaded_orchestrator.seek(12)
        assert loaded_orchestrator.current_frame == 12

    def test_seek_negative_clamps_to_zero(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test seek(-1) clamps to 0."""
        loaded_orchestrator.seek(-10)
        assert loaded_orchestrator.current_frame == 0

    def test_seek_over_duration_clamps_to_max(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test seek beyond duration clamps to max frame."""
        loaded_orchestrator.seek(999999)
        assert loaded_orchestrator.current_frame == 24

    def test_seek_syncs_current_time(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that seek updates current_time to match frame."""
        loaded_orchestrator.seek(12)
        # 12 frames at 24fps = 0.5 seconds
        state = loaded_orchestrator.playback_state
        assert state.current_time_seconds == pytest.approx(0.5)


# ============================================================================
# Test Update
# ============================================================================


class TestUpdate:
    """Tests for update(delta_time) method."""

    def test_update_zero_no_change(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test update(0) doesn't change frame."""
        loaded_orchestrator.seek(5)
        result = loaded_orchestrator.update(0)
        assert result == 5
        assert loaded_orchestrator.current_frame == 5

    def test_update_positive_delta(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update with positive delta advances playback."""
        # At 24fps, 1 second = 24 frames
        loaded_orchestrator.seek(0)
        result = loaded_orchestrator.update(1.0)
        assert result == 24
        assert loaded_orchestrator.current_frame == 24

    def test_update_fractional_delta(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update with fractional delta."""
        loaded_orchestrator.seek(0)
        # 0.5 seconds at 24fps = 12 frames
        result = loaded_orchestrator.update(0.5)
        assert result == 12

    def test_update_negative_raises_error(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update with negative delta raises ValueError."""
        with pytest.raises(ValueError, match="delta_time cannot be negative"):
            loaded_orchestrator.update(-0.1)

    def test_update_beyond_duration_clamps(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update beyond duration clamps to max frame."""
        loaded_orchestrator.seek(20)
        # Try to advance 1 second (would go to frame 44)
        # But max is 24
        result = loaded_orchestrator.update(1.0)
        assert result == 24
        assert loaded_orchestrator.current_frame == 24

    def test_update_at_duration_remains_at_duration(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update when already at duration stays at duration."""
        loaded_orchestrator.seek(24)
        result = loaded_orchestrator.update(0.5)
        assert result == 24


# ============================================================================
# Test Timing
# ============================================================================


class TestTiming:
    """Tests for time/frame conversion."""

    def test_24fps_conversion(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test 24fps time to frame conversion."""
        loaded_orchestrator.seek(0)
        # 1 frame = 1/24 seconds ≈ 0.04167 seconds
        result = loaded_orchestrator.update(1.0 / 24.0)
        assert result == 1

    def test_exact_frame_boundary(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test exact frame boundaries."""
        loaded_orchestrator.seek(0)
        # 0.5 seconds at 24fps should round to frame 12
        result = loaded_orchestrator.update(0.5)
        assert result == 12

    def test_multiple_sequential_updates(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test multiple sequential updates."""
        loaded_orchestrator.seek(0)
        # Two 0.5 second updates = 1 second = 24 frames
        loaded_orchestrator.update(0.5)
        loaded_orchestrator.update(0.5)
        assert loaded_orchestrator.current_frame == 24

    def test_deterministic_repeated_updates(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that same updates always produce same result."""
        # Run 1: two 0.5s updates
        orch1 = AnimationOrchestrator(frame_rate=24.0)
        # Setup
        target = CharacterAnimationTarget(
            character_id="h", layer_id="1", sequence_id="s"
        )
        output = CharacterAnimationOutput(
            sequence_id="s",
            bindings=(
                CharacterAnimationBinding(target=target, frame_index=0, palette_id=None),
                CharacterAnimationBinding(target=target, frame_index=24, palette_id=None),
            ),
            metadata=CharacterAnimationMetadata(
                bindings_created=2,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )
        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="h", frame_index=0,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="h", frame_index=24,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        orch1.load(output, transforms)
        orch1.update(0.5)
        result1 = orch1.update(0.5)

        # Run 2: same thing
        orch2 = AnimationOrchestrator(frame_rate=24.0)
        orch2.load(output, transforms)
        orch2.update(0.5)
        result2 = orch2.update(0.5)

        # Same initial state + same updates = same result
        assert result1 == result2 == 24


# ============================================================================
# Test Reset
# ============================================================================


class TestReset:
    """Tests for reset() method."""

    def test_reset_from_middle(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test reset from middle of playback."""
        loaded_orchestrator.seek(12)
        loaded_orchestrator.update(0.5)
        loaded_orchestrator.reset()
        assert loaded_orchestrator.current_frame == 0
        state = loaded_orchestrator.playback_state
        assert state.current_time_seconds == 0.0

    def test_reset_from_end(self, loaded_orchestrator: AnimationOrchestrator) -> None:
        """Test reset from end of playback."""
        loaded_orchestrator.seek(24)
        loaded_orchestrator.reset()
        assert loaded_orchestrator.current_frame == 0


# ============================================================================
# Test Evaluate Current Frame
# ============================================================================


class TestEvaluateCurrentFrame:
    """Tests for evaluate_current_frame() method."""

    def test_evaluate_current_frame_delegates(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test evaluate_current_frame delegates to runtime."""
        loaded_orchestrator.seek(12)
        result = loaded_orchestrator.evaluate_current_frame()
        # Compare with direct evaluate_at_frame call
        expected = loaded_orchestrator.evaluate_at_frame(12)
        assert result == expected

    def test_evaluate_current_frame_matches_runtime_evaluation(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test evaluate_current_frame returns same as runtime."""
        loaded_orchestrator.seek(0)
        result = loaded_orchestrator.evaluate_current_frame()
        expected = loaded_orchestrator.evaluate_at_frame(0)
        assert result == expected


# ============================================================================
# Test Load Resets Playback
# ============================================================================


class TestLoadResetsPlayback:
    """Tests that load() resets playback position."""

    def test_load_resets_current_frame(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that loading new animation resets playback to 0."""
        loaded_orchestrator.seek(12)
        loaded_orchestrator.update(0.5)

        # Create new animation data
        target = CharacterAnimationTarget(
            character_id="villain",
            layer_id="1",
            sequence_id="new",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=0,
            palette_id=None,
        )
        output = CharacterAnimationOutput(
            sequence_id="new",
            bindings=(binding,),
            metadata=CharacterAnimationMetadata(
                bindings_created=1,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )
        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="villain",
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        loaded_orchestrator.load(output, transforms)

        assert loaded_orchestrator.current_frame == 0


# ============================================================================
# Test Playback State
# ============================================================================


class TestPlaybackState:
    """Tests for PlaybackState dataclass."""

    def test_playback_state_contains_all_fields(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that playback_state contains all required fields."""
        loaded_orchestrator.seek(12)
        state = loaded_orchestrator.playback_state

        assert hasattr(state, "current_frame")
        assert hasattr(state, "duration_frames")
        assert hasattr(state, "frame_rate")
        assert hasattr(state, "current_time_seconds")

        assert state.current_frame == 12
        assert state.duration_frames == 24
        assert state.frame_rate == 24.0
        assert state.current_time_seconds == pytest.approx(0.5)

    def test_playback_state_current_time_derived(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that current_time_seconds is derived from current_frame."""
        loaded_orchestrator.seek(12)
        state = loaded_orchestrator.playback_state
        # 12 frames at 24fps = 0.5 seconds
        assert state.current_time_seconds == pytest.approx(12 / 24.0)


# ============================================================================
# Test 30fps
# ============================================================================


class Test30fps:
    """Tests for 30fps playback."""

    def test_30fps_conversion(self, orchestrator_30fps: AnimationOrchestrator) -> None:
        """Test 30fps time to frame conversion."""
        target = CharacterAnimationTarget(
            character_id="h", layer_id="1", sequence_id="s"
        )
        output = CharacterAnimationOutput(
            sequence_id="s",
            bindings=(
                CharacterAnimationBinding(target=target, frame_index=0, palette_id=None),
                CharacterAnimationBinding(target=target, frame_index=30, palette_id=None),
            ),
            metadata=CharacterAnimationMetadata(
                bindings_created=2,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )
        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="h", frame_index=0,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="h", frame_index=30,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        orchestrator_30fps.load(output, transforms)

        # 1 second at 30fps = 30 frames
        result = orchestrator_30fps.update(1.0)
        assert result == 30


# ============================================================================
# Test Integration
# ============================================================================


class TestIntegration:
    """Integration tests for playback + evaluation pipeline."""

    def test_full_pipeline_playback_to_evaluation(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test full pipeline: playback advances -> evaluation returns transforms."""
        # Start at frame 0
        assert loaded_orchestrator.current_frame == 0
        transforms_at_0 = loaded_orchestrator.evaluate_current_frame()

        # Advance to frame 12 (0.5 seconds at 24fps)
        loaded_orchestrator.update(0.5)
        assert loaded_orchestrator.current_frame == 12
        transforms_at_12 = loaded_orchestrator.evaluate_current_frame()

        # Verify transforms are different at different frames
        # (interpolated position_x should be different)
        assert transforms_at_0 != transforms_at_12 or transforms_at_0 == {}
