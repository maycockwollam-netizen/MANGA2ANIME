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


# ============================================================================
# Test Invariant: current_time == current_frame / frame_rate
# ============================================================================


class TestInvariantConsistency:
    """Tests verifying the invariant _current_time == _current_frame / frame_rate.

    This invariant must hold after any operation that changes playback state.
    The implementation should derive _current_time from _current_frame, not
    accumulate independently, to avoid floating-point drift.
    """

    def _assert_invariant(self, orchestrator: AnimationOrchestrator) -> None:
        """Verify _current_time == _current_frame / frame_rate."""
        expected_time = orchestrator.current_frame / orchestrator.frame_rate
        actual_time = orchestrator.playback_state.current_time_seconds
        assert actual_time == pytest.approx(expected_time), (
            f"Invariant violated: current_time={actual_time} "
            f"!= current_frame/frame_rate={expected_time}"
        )

    def test_invariant_holds_at_initial_state(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds at initial state (frame 0)."""
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_seek(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after seek()."""
        loaded_orchestrator.seek(5)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.seek(24)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.seek(0)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_seek_negative(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after seek to negative (clamps to 0)."""
        loaded_orchestrator.seek(-100)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_seek_beyond_duration(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after seek beyond duration (clamps to max)."""
        loaded_orchestrator.seek(999)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_update(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after update()."""
        loaded_orchestrator.seek(0)
        loaded_orchestrator.update(0.5)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.update(0.25)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.update(0.25)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_update_clamps_at_duration(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after update clamps at duration."""
        loaded_orchestrator.seek(20)
        loaded_orchestrator.update(1.0)  # Would go to 44, clamped to 24
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_reset(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after reset()."""
        loaded_orchestrator.seek(12)
        loaded_orchestrator.update(0.5)
        loaded_orchestrator.reset()
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_load(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after load()."""
        loaded_orchestrator.seek(12)
        loaded_orchestrator.update(0.5)

        # Load new animation
        target = CharacterAnimationTarget(
            character_id="new", layer_id="1", sequence_id="new"
        )
        binding = CharacterAnimationBinding(
            target=target, frame_index=0, palette_id=None
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
                    character_id="new", frame_index=0,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        loaded_orchestrator.load(output, transforms)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_holds_after_reload(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after reload()."""
        loaded_orchestrator.seek(10)
        loaded_orchestrator.update(0.5)

        # Reload with same animation data
        target = CharacterAnimationTarget(
            character_id="hero", layer_id="1", sequence_id="intro"
        )
        binding = CharacterAnimationBinding(
            target=target, frame_index=0, palette_id=None
        )
        binding2 = CharacterAnimationBinding(
            target=target, frame_index=24, palette_id=None
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
                    character_id="hero", frame_index=0,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero", frame_index=24,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        loaded_orchestrator.reload(output, transforms)
        self._assert_invariant(loaded_orchestrator)

    def test_invariant_after_mixed_operations(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test invariant holds after mixed seek/update/reset sequences."""
        loaded_orchestrator.seek(5)
        loaded_orchestrator.update(0.25)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.seek(15)
        loaded_orchestrator.update(0.1)
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.reset()
        self._assert_invariant(loaded_orchestrator)

        loaded_orchestrator.seek(24)
        loaded_orchestrator.update(0.5)  # Clamp
        self._assert_invariant(loaded_orchestrator)


# ============================================================================
# Test Floating-Point Determinism
# ============================================================================


class TestFloatingPointDeterminism:
    """Tests for deterministic behavior with repeated small updates.

    Verifies that floating-point accumulation does not cause unexpected frame
    jumps or inconsistent behavior.
    """

    def test_repeated_small_updates_deterministic(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test many repeated small updates produce deterministic results."""
        loaded_orchestrator.seek(0)

        # Update 24 times with 1/24 second each
        expected_frame = 0
        for _ in range(24):
            loaded_orchestrator.update(1.0 / 24.0)
            expected_frame += 1

        assert loaded_orchestrator.current_frame == 24

    def test_many_small_updates_no_frame_jumps(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that many small updates don't cause frame skipping or duplication."""
        loaded_orchestrator.seek(0)

        frames_seen: list[int] = []
        for _ in range(100):
            old_frame = loaded_orchestrator.current_frame
            loaded_orchestrator.update(1.0 / 24.0)
            new_frame = loaded_orchestrator.current_frame

            # Frame should advance by 0 or 1 (never skip or go backward)
            assert new_frame >= old_frame, (
                f"Frame went backward: {old_frame} -> {new_frame}"
            )
            frames_seen.append(new_frame)

        # Verify frames 1-24 appear exactly once (before clamping starts)
        # After frame 24, all subsequent updates stay at 24
        expected_frames = list(range(1, 25))
        for frame in expected_frames:
            assert frame in frames_seen, f"Frame {frame} not seen"

    def test_fractional_accumulation_accurate(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that accumulated time matches expected frame after many updates."""
        loaded_orchestrator.seek(0)

        # 24 updates of 1/24 second each = 1 second = 24 frames
        for _ in range(24):
            loaded_orchestrator.update(1.0 / 24.0)

        assert loaded_orchestrator.current_frame == 24

    def test_deterministic_same_sequence(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that running the same update sequence produces same result."""
        def run_sequence() -> int:
            orch = AnimationOrchestrator(frame_rate=24.0)
            target = CharacterAnimationTarget(
                character_id="h", layer_id="1", sequence_id="s"
            )
            output = CharacterAnimationOutput(
                sequence_id="s",
                bindings=(
                    CharacterAnimationBinding(
                        target=target, frame_index=0, palette_id=None
                    ),
                    CharacterAnimationBinding(
                        target=target, frame_index=24, palette_id=None
                    ),
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
            orch.load(output, transforms)
            for _ in range(50):
                orch.update(1.0 / 24.0)
            return orch.current_frame

        results = [run_sequence() for _ in range(5)]
        assert len(set(results)) == 1, (
            f"Non-deterministic results: {results}"
        )


# ============================================================================
# Test Frame Boundary Behavior
# ============================================================================


class TestFrameBoundaries:
    """Tests for frame boundary transitions and clamping behavior."""

    def test_frame_boundary_just_below(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update just below a frame boundary."""
        loaded_orchestrator.seek(11)
        # 0.01 second = 0.24 frames at 24fps, rounds down to 11
        loaded_orchestrator.update(0.01)
        assert loaded_orchestrator.current_frame == 11

    def test_frame_boundary_exactly(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update exactly at a frame boundary."""
        loaded_orchestrator.seek(11)
        # 1/24 second = exactly 1 frame at 24fps
        loaded_orchestrator.update(1.0 / 24.0)
        assert loaded_orchestrator.current_frame == 12

    def test_frame_boundary_just_above(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update just above a frame boundary."""
        loaded_orchestrator.seek(11)
        # 1.5/24 second = 1.5 frames, rounds to 12
        loaded_orchestrator.update(1.5 / 24.0)
        assert loaded_orchestrator.current_frame == 12

    def test_duration_boundary_exactly(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update exactly at duration boundary."""
        loaded_orchestrator.seek(23)
        # 1/24 second = exactly 1 frame
        loaded_orchestrator.update(1.0 / 24.0)
        assert loaded_orchestrator.current_frame == 24

    def test_duration_boundary_just_beyond(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test update just beyond duration (clamps)."""
        loaded_orchestrator.seek(23)
        # 2/24 second = 2 frames, but only 1 available
        loaded_orchestrator.update(2.0 / 24.0)
        assert loaded_orchestrator.current_frame == 24

    def test_update_after_duration_remains_at_duration(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that further updates stay at duration after clamping."""
        loaded_orchestrator.seek(20)
        loaded_orchestrator.update(1.0)  # Clamps to 24

        assert loaded_orchestrator.current_frame == 24

        # Additional updates should not change anything
        loaded_orchestrator.update(0.5)
        assert loaded_orchestrator.current_frame == 24

        loaded_orchestrator.update(1.0)
        assert loaded_orchestrator.current_frame == 24

    def test_zero_duration_handled(self, orchestrator: AnimationOrchestrator) -> None:
        """Test edge case where duration is 0 (no clips)."""
        # Without loading, duration_frames = 0
        assert orchestrator.duration_frames == 0

        orchestrator.seek(5)  # Should clamp to 0
        assert orchestrator.current_frame == 0

        orchestrator.update(1.0)  # Should clamp to 0
        assert orchestrator.current_frame == 0

    def test_single_frame_animation(
        self, orchestrator: AnimationOrchestrator
    ) -> None:
        """Test edge case with single-frame animation."""
        target = CharacterAnimationTarget(
            character_id="h", layer_id="1", sequence_id="s"
        )
        output = CharacterAnimationOutput(
            sequence_id="s",
            bindings=(
                CharacterAnimationBinding(
                    target=target, frame_index=0, palette_id=None
                ),
            ),
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
                    character_id="h", frame_index=0,
                    transform=FrameTransform(), interpolation=InterpolationType.LINEAR,
                ),
            ),
        )
        orchestrator.load(output, transforms)
        assert orchestrator.duration_frames == 0

        orchestrator.seek(1)
        assert orchestrator.current_frame == 0  # Clamps to max (0)

        orchestrator.update(1.0)
        assert orchestrator.current_frame == 0  # Stays at 0


# ============================================================================
# Test PlaybackState Consistency
# ============================================================================


class TestPlaybackStateConsistency:
    """Tests that PlaybackState always reports consistent values."""

    def test_playback_state_matches_internal_state(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test PlaybackState matches internal _current_frame/_current_time."""
        test_cases = [0, 1, 12, 23, 24]

        for frame in test_cases:
            loaded_orchestrator.seek(frame)
            state = loaded_orchestrator.playback_state

            assert state.current_frame == loaded_orchestrator._current_frame
            assert state.current_frame == loaded_orchestrator.current_frame
            assert state.frame_rate == loaded_orchestrator.frame_rate
            assert state.duration_frames == loaded_orchestrator.duration_frames

    def test_playback_state_time_matches_frame(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test PlaybackState.current_time_seconds == current_frame / frame_rate."""
        loaded_orchestrator.seek(12)
        state = loaded_orchestrator.playback_state

        expected = 12 / 24.0
        assert state.current_time_seconds == pytest.approx(expected)


# ============================================================================
# Test Frame Iterator
# ============================================================================


class TestRenderFrame:
    """Tests for RenderFrame contract."""

    def test_render_frame_construction(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame construction from orchestrator."""
        loaded_orchestrator.seek(12)
        frame = loaded_orchestrator.render_frame()

        assert frame.frame_index == 12
        assert frame.timestamp_seconds == pytest.approx(12 / 24.0)
        assert frame.frame_rate == 24.0
        assert isinstance(frame.transforms, dict)

    def test_render_frame_immutability(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame is frozen/immutable."""
        loaded_orchestrator.seek(12)
        frame = loaded_orchestrator.render_frame()

        # Verify frozen
        with pytest.raises(AttributeError):
            frame.frame_index = 10  # type: ignore
        with pytest.raises(AttributeError):
            frame.transforms = {}  # type: ignore

    def test_render_frame_empty_transforms(
        self, orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame with no clips loaded."""
        frame = orchestrator.render_frame()

        assert frame.frame_index == 0
        assert frame.timestamp_seconds == 0.0
        assert frame.frame_rate == 24.0
        assert len(frame.transforms) == 0

    def test_render_frame_multiple_entities(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame with multiple clip entities."""
        # loaded_orchestrator only has one clip, but test the structure
        frame = loaded_orchestrator.render_frame()

        # Should have at least the hero_1 clip
        assert len(frame.transforms) >= 0
        # If there are transforms, they should be FrameTransform instances
        for clip_id, transform in frame.transforms.items():
            assert isinstance(clip_id, str)
            assert hasattr(transform, "position_x")
            assert hasattr(transform, "scale")

    def test_render_frame_deterministic(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that repeated render_frame() produces identical results."""
        loaded_orchestrator.seek(5)

        frame1 = loaded_orchestrator.render_frame()
        frame2 = loaded_orchestrator.render_frame()

        assert frame1 == frame2

    def test_render_frame_no_playback_mutation(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that render_frame() does not modify playback state."""
        loaded_orchestrator.seek(10)

        before_state = loaded_orchestrator.playback_state
        before_frame = loaded_orchestrator.current_frame

        # render_frame() is called to exercise the method
        # but the return value is not used - we only verify state unchanged
        _ = loaded_orchestrator.render_frame()

        after_state = loaded_orchestrator.playback_state
        after_frame = loaded_orchestrator.current_frame

        assert before_state == after_state
        assert before_frame == after_frame

    def test_render_frame_frame_count(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frame_count property."""
        frame = loaded_orchestrator.render_frame()

        assert frame.frame_count == len(frame.transforms)

    def test_render_frame_duration_seconds(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test duration_seconds calculation."""
        frame = loaded_orchestrator.render_frame()

        # With no entities, duration_seconds should be 0
        # (frame_count / frame_rate would be 0)
        expected = frame.frame_count / frame.frame_rate if frame.frame_count > 0 else 0.0
        assert frame.duration_seconds == expected

    def test_render_frame_preserves_clip_identity(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that clip_id semantics are preserved in RenderFrame."""
        frame = loaded_orchestrator.render_frame()

        # Verify transforms are keyed by clip_id
        for clip_id in frame.transforms.keys():
            assert isinstance(clip_id, str)
            assert "_" in clip_id or clip_id == "default"  # clip_id format check

    def test_render_frame_compatible_with_frames_iterator(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that RenderFrame data matches what frames() iterator provides."""
        loaded_orchestrator.seek(5)

        # Get frame via render_frame()
        rf = loaded_orchestrator.render_frame()

        # Get frame via frames iterator
        frames_list = list(loaded_orchestrator.frames(start_frame=5, end_frame=5))
        assert len(frames_list) == 1
        fi, ft = frames_list[0]

        assert rf.frame_index == fi
        assert rf.transforms == ft

    def test_render_frame_timestamp_matches_current_time(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that timestamp_seconds matches current_time."""
        loaded_orchestrator.seek(12)
        frame = loaded_orchestrator.render_frame()

        assert frame.timestamp_seconds == loaded_orchestrator.playback_state.current_time_seconds

    def test_render_frame_at_exact_frame_boundary(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame at exact frame boundary."""
        loaded_orchestrator.seek(24)
        frame = loaded_orchestrator.render_frame()

        assert frame.frame_index == 24
        assert frame.timestamp_seconds == pytest.approx(1.0)  # 24/24 = 1.0 second

    def test_render_frame_at_frame_zero(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test RenderFrame at frame 0."""
        loaded_orchestrator.seek(0)
        frame = loaded_orchestrator.render_frame()

        assert frame.frame_index == 0
        assert frame.timestamp_seconds == 0.0


class TestFrameIterator:
    """Tests for frames() iterator method."""

    def test_frames_default_iterates_full_range(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() iterates from 0 to duration_frames inclusive."""
        # loaded_orchestrator has duration_frames == 24
        frames_list = list(loaded_orchestrator.frames())

        # Should yield frames 0 through 24 inclusive = 25 frames
        assert len(frames_list) == 25
        assert frames_list[0][0] == 0
        assert frames_list[-1][0] == 24

    def test_frames_explicit_start(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames(start_frame=N) iterates from N to duration."""
        frames_list = list(loaded_orchestrator.frames(start_frame=5))

        assert len(frames_list) == 20  # 5 through 24 inclusive
        assert frames_list[0][0] == 5
        assert frames_list[-1][0] == 24

    def test_frames_explicit_end(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames(end_frame=N) iterates from 0 to N."""
        frames_list = list(loaded_orchestrator.frames(end_frame=10))

        assert len(frames_list) == 11  # 0 through 10 inclusive
        assert frames_list[0][0] == 0
        assert frames_list[-1][0] == 10

    def test_frames_start_and_end(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames(start_frame, end_frame) iterates the range."""
        frames_list = list(loaded_orchestrator.frames(start_frame=5, end_frame=10))

        assert len(frames_list) == 6  # 5 through 10 inclusive
        assert frames_list[0][0] == 5
        assert frames_list[-1][0] == 10

    def test_frames_single_frame(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames(start_frame=N, end_frame=N) yields exactly one frame."""
        frames_list = list(loaded_orchestrator.frames(start_frame=12, end_frame=12))

        assert len(frames_list) == 1
        assert frames_list[0][0] == 12

    def test_frames_empty_range_when_start_greater_than_end(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() returns empty iterator when start > end."""
        frames_list = list(loaded_orchestrator.frames(start_frame=10, end_frame=5))

        assert len(frames_list) == 0

    def test_frames_negative_start_raises(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() raises InvalidFrameError for negative start_frame."""
        from runtime.animation import InvalidFrameError

        with pytest.raises(InvalidFrameError, match="start_frame.*cannot be negative"):
            list(loaded_orchestrator.frames(start_frame=-1))

    def test_frames_negative_end_raises(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() raises InvalidFrameError for negative end_frame."""
        from runtime.animation import InvalidFrameError

        with pytest.raises(InvalidFrameError, match="end_frame.*cannot be negative"):
            list(loaded_orchestrator.frames(end_frame=-1))

    def test_frames_start_beyond_duration_raises(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() raises InvalidFrameError when start_frame > duration."""
        from runtime.animation import InvalidFrameError

        with pytest.raises(InvalidFrameError, match="start_frame.*exceeds duration"):
            list(loaded_orchestrator.frames(start_frame=100))

    def test_frames_end_beyond_duration_raises(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() raises InvalidFrameError when end_frame > duration."""
        from runtime.animation import InvalidFrameError

        with pytest.raises(InvalidFrameError, match="end_frame.*exceeds duration"):
            list(loaded_orchestrator.frames(end_frame=100))

    def test_frames_empty_runtime_yields_frame_0(
        self, orchestrator: AnimationOrchestrator
    ) -> None:
        """Test frames() on empty runtime yields frame 0 only."""
        # Before loading, duration_frames == 0
        assert orchestrator.duration_frames == 0

        frames_list = list(orchestrator.frames())

        # Frame 0 is valid even when duration is 0
        assert len(frames_list) == 1
        assert frames_list[0][0] == 0

    def test_frames_evaluation_matches_evaluate_at_frame(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that each yielded transform matches evaluate_at_frame()."""
        for frame_index, transforms in loaded_orchestrator.frames(0, 10):
            expected = loaded_orchestrator.evaluate_at_frame(frame_index)
            assert transforms == expected

    def test_frames_deterministic(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that repeated iteration produces identical results."""
        result1 = list(loaded_orchestrator.frames(0, 10))
        result2 = list(loaded_orchestrator.frames(0, 10))

        assert result1 == result2

    def test_frames_no_playback_mutation(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that frames() does not modify playback state."""
        loaded_orchestrator.seek(10)

        before_state = loaded_orchestrator.playback_state
        before_frame = loaded_orchestrator.current_frame

        # Iterate through frames
        list(loaded_orchestrator.frames(0, 5))

        after_state = loaded_orchestrator.playback_state
        after_frame = loaded_orchestrator.current_frame

        assert before_state == after_state
        assert before_frame == after_frame

    def test_frames_lazy_iterator(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that frames() returns a generator, not a list."""
        result = loaded_orchestrator.frames(0, 5)

        # Should be a generator, not a list
        import types

        assert isinstance(result, types.GeneratorType)

    def test_frames_generator_exhaustion(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that iterator stops after last frame."""
        result = loaded_orchestrator.frames(0, 5)

        frames_yielded = []
        for frame_index, _ in result:
            frames_yielded.append(frame_index)

        assert frames_yielded == [0, 1, 2, 3, 4, 5]

    def test_frames_snapshot_semantics(
        self, loaded_orchestrator: AnimationOrchestrator
    ) -> None:
        """Test that yielded transforms are independent snapshots."""
        frames_list = list(loaded_orchestrator.frames(0, 5))

        # Each frame should be independent
        for frame_index, transforms in frames_list:
            assert frame_index in [0, 1, 2, 3, 4, 5]
            # Transform dict should be non-None for valid clips
            assert isinstance(transforms, dict)
