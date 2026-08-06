"""Tests for runtime animation module."""

import pytest

from runtime.animation import (
    AnimationRuntime,
    ClipNotFoundError,
    DuplicateClipError,
    InvalidFrameError,
    RuntimeAnimationState,
    UnsupportedInterpolationError,
)
from tools.frame.animation import AnimationClip, AnimationKeyframe
from tools.frame.models import FrameTransform, InterpolationType

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def empty_runtime() -> AnimationRuntime:
    """Create an empty runtime."""
    return AnimationRuntime(sequence_id="test_sequence")


@pytest.fixture
def clip_with_keyframes() -> AnimationClip:
    """Create a clip with keyframes for testing."""
    return AnimationClip(
        clip_id="hero_1",
        start_frame=0,
        end_frame=24,
        keyframes=[
            AnimationKeyframe(
                frame_index=0,
                transform=FrameTransform(position_x=0, scale=1.0),
                interpolation=InterpolationType.LINEAR,
            ),
            AnimationKeyframe(
                frame_index=24,
                transform=FrameTransform(position_x=100, scale=2.0),
                interpolation=InterpolationType.LINEAR,
            ),
        ],
    )


@pytest.fixture
def clip_without_keyframes() -> AnimationClip:
    """Create a clip without keyframes (uses default transform)."""
    return AnimationClip(
        clip_id="villain_default",
        start_frame=10,
        end_frame=20,
        keyframes=[],
    )


@pytest.fixture
def populated_runtime(
    empty_runtime: AnimationRuntime,
    clip_with_keyframes: AnimationClip,
    clip_without_keyframes: AnimationClip,
) -> AnimationRuntime:
    """Create a runtime with clips registered."""
    empty_runtime.register(clip_with_keyframes)
    empty_runtime.register(clip_without_keyframes)
    return empty_runtime


# ============================================================================
# Test Runtime Lifecycle
# ============================================================================


class TestRuntimeLifecycle:
    """Tests for runtime lifecycle management."""

    def test_create_empty_runtime(self) -> None:
        """Test creating an empty runtime."""
        runtime = AnimationRuntime(sequence_id="intro")
        assert runtime.sequence_id == "intro"
        assert runtime.frame_rate == 24.0
        assert runtime.count() == 0

    def test_create_runtime_custom_frame_rate(self) -> None:
        """Test creating runtime with custom frame rate."""
        runtime = AnimationRuntime(sequence_id="test", frame_rate=30.0)
        assert runtime.frame_rate == 30.0

    def test_empty_sequence_id_rejected(self) -> None:
        """Test that empty sequence_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AnimationRuntime(sequence_id="")

    def test_whitespace_sequence_id_rejected(self) -> None:
        """Test that whitespace-only sequence_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AnimationRuntime(sequence_id="   ")

    def test_state_property(self) -> None:
        """Test runtime state is immutable."""
        runtime = AnimationRuntime(sequence_id="test")
        state = runtime.state
        assert isinstance(state, RuntimeAnimationState)
        assert state.sequence_id == "test"
        assert state.registered_clips == 0
        assert state.frame_rate == 24.0


# ============================================================================
# Test Clip Registration
# ============================================================================


class TestClipRegistration:
    """Tests for clip registration."""

    def test_register_single_clip(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test registering a single clip."""
        result = empty_runtime.register(clip_with_keyframes)
        assert result is clip_with_keyframes
        assert empty_runtime.count() == 1
        assert "hero_1" in empty_runtime

    def test_register_many(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
        clip_without_keyframes: AnimationClip,
    ) -> None:
        """Test registering multiple clips."""
        clips = [clip_with_keyframes, clip_without_keyframes]
        result = empty_runtime.register_many(clips)
        assert len(result) == 2
        assert empty_runtime.count() == 2

    def test_register_duplicate_rejected(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test that duplicate clip_id is rejected."""
        empty_runtime.register(clip_with_keyframes)
        with pytest.raises(DuplicateClipError, match="already exists"):
            empty_runtime.register(clip_with_keyframes)

    def test_register_many_duplicate_rejected(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
        clip_without_keyframes: AnimationClip,
    ) -> None:
        """Test that register_many fails if any duplicate exists."""
        empty_runtime.register(clip_with_keyframes)
        with pytest.raises(DuplicateClipError):
            empty_runtime.register_many([clip_without_keyframes, clip_with_keyframes])

    def test_get_clip(
        self,
        populated_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test retrieving a registered clip."""
        clip = populated_runtime.get_clip("hero_1")
        assert clip is clip_with_keyframes

    def test_get_unknown_clip(self, empty_runtime: AnimationRuntime) -> None:
        """Test that getting unknown clip raises error."""
        with pytest.raises(ClipNotFoundError):
            empty_runtime.get_clip("unknown")

    def test_has_clip(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test checking clip existence."""
        assert populated_runtime.has_clip("hero_1") is True
        assert populated_runtime.has_clip("unknown") is False

    def test_list_clips_sorted(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that list_clips returns sorted clips."""
        clips = [
            AnimationClip(clip_id="z_clip", start_frame=0, end_frame=10),
            AnimationClip(clip_id="a_clip", start_frame=0, end_frame=10),
            AnimationClip(clip_id="m_clip", start_frame=0, end_frame=10),
        ]
        empty_runtime.register_many(clips)
        listed = empty_runtime.list_clips()
        assert [c.clip_id for c in listed] == ["a_clip", "m_clip", "z_clip"]

    def test_unregister(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test unregistering a clip."""
        clip = populated_runtime.unregister("hero_1")
        assert clip.clip_id == "hero_1"
        assert populated_runtime.count() == 1
        assert "hero_1" not in populated_runtime

    def test_unregister_unknown(self, empty_runtime: AnimationRuntime) -> None:
        """Test that unregistering unknown clip raises error."""
        with pytest.raises(ClipNotFoundError):
            empty_runtime.unregister("unknown")

    def test_clear(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test clearing all clips."""
        populated_runtime.clear()
        assert populated_runtime.count() == 0


# ============================================================================
# Test Clip Replacement
# ============================================================================


class TestClipReplacement:
    """Tests for clip replacement functionality."""

    def test_replace_existing_clip(
        self,
        populated_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test replacing an existing clip."""
        # Create replacement clip with different keyframes
        replacement_clip = AnimationClip(
            clip_id="hero_1",  # Same clip_id
            start_frame=0,
            end_frame=48,  # Different end frame
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0, scale=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=48,
                    transform=FrameTransform(position_x=200, scale=3.0),
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )

        result = populated_runtime.replace(replacement_clip)

        assert result is replacement_clip
        assert populated_runtime.count() == 2  # Still 2 clips
        retrieved = populated_runtime.get_clip("hero_1")
        assert retrieved is replacement_clip
        assert retrieved.end_frame == 48

    def test_replace_updates_evaluation(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that replacement updates evaluation results."""
        # Register initial clip
        initial_clip = AnimationClip(
            clip_id="hero_1",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(position_x=100),
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )
        empty_runtime.register(initial_clip)

        # Evaluate before replacement
        result_before = empty_runtime.evaluate("hero_1", 12)
        assert result_before.position_x == 50

        # Replace with different clip
        replacement_clip = AnimationClip(
            clip_id="hero_1",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(position_x=200),  # Different end
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )
        empty_runtime.replace(replacement_clip)

        # Evaluate after replacement
        result_after = empty_runtime.evaluate("hero_1", 12)
        assert result_after.position_x == 100  # Now different

    def test_replace_nonexistent_clip(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that replacing non-existent clip raises error."""
        clip = AnimationClip(
            clip_id="unknown",
            start_frame=0,
            end_frame=10,
        )

        with pytest.raises(ClipNotFoundError, match="not found"):
            empty_runtime.replace(clip)

    def test_replace_many(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test replacing multiple clips atomically."""
        # Register initial clips
        clip_a = AnimationClip(clip_id="a", start_frame=0, end_frame=10)
        clip_b = AnimationClip(clip_id="b", start_frame=0, end_frame=10)
        empty_runtime.register_many([clip_a, clip_b])

        # Create replacements
        replacement_a = AnimationClip(
            clip_id="a",
            start_frame=0,
            end_frame=20,  # Different end
        )
        replacement_b = AnimationClip(
            clip_id="b",
            start_frame=0,
            end_frame=30,  # Different end
        )

        result = empty_runtime.replace_many([replacement_a, replacement_b])

        assert len(result) == 2
        assert empty_runtime.get_clip("a") is replacement_a
        assert empty_runtime.get_clip("b") is replacement_b

    def test_replace_many_nonexistent_rejected(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that replace_many fails if any clip doesn't exist."""
        # Register only one clip
        empty_runtime.register(AnimationClip(clip_id="a", start_frame=0, end_frame=10))

        # Try to replace both (b doesn't exist)
        replacement_a = AnimationClip(clip_id="a", start_frame=0, end_frame=20)
        replacement_b = AnimationClip(clip_id="b", start_frame=0, end_frame=20)

        with pytest.raises(ClipNotFoundError, match="'b'"):
            empty_runtime.replace_many([replacement_a, replacement_b])

        # Verify no changes were made
        assert empty_runtime.get_clip("a").end_frame == 10

    def test_replace_many_duplicate_in_request_rejected(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that replace_many rejects duplicate clip_ids in the request."""
        empty_runtime.register(AnimationClip(clip_id="a", start_frame=0, end_frame=10))

        replacement_a = AnimationClip(clip_id="a", start_frame=0, end_frame=20)
        replacement_duplicate = AnimationClip(clip_id="a", start_frame=0, end_frame=30)

        with pytest.raises(ValueError, match="duplicate"):
            empty_runtime.replace_many([replacement_a, replacement_duplicate])

    def test_replace_preserves_count(
        self,
        populated_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test that replacement preserves clip count."""
        initial_count = populated_runtime.count()

        replacement = AnimationClip(
            clip_id="hero_1",
            start_frame=0,
            end_frame=10,
        )
        populated_runtime.replace(replacement)

        assert populated_runtime.count() == initial_count

    def test_replace_deterministic(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that replacement is deterministic."""
        # Register initial clip
        empty_runtime.register(
            AnimationClip(
                clip_id="hero_1",
                start_frame=0,
                end_frame=24,
                keyframes=[
                    AnimationKeyframe(
                        frame_index=0,
                        transform=FrameTransform(position_x=0),
                        interpolation=InterpolationType.LINEAR,
                    ),
                    AnimationKeyframe(
                        frame_index=24,
                        transform=FrameTransform(position_x=100),
                        interpolation=InterpolationType.LINEAR,
                    ),
                ],
            )
        )

        # Replace multiple times
        for _ in range(10):
            replacement = AnimationClip(
                clip_id="hero_1",
                start_frame=0,
                end_frame=24,
                keyframes=[
                    AnimationKeyframe(
                        frame_index=0,
                        transform=FrameTransform(position_x=0),
                        interpolation=InterpolationType.LINEAR,
                    ),
                    AnimationKeyframe(
                        frame_index=24,
                        transform=FrameTransform(position_x=100),
                        interpolation=InterpolationType.LINEAR,
                    ),
                ],
            )
            empty_runtime.replace(replacement)
            result = empty_runtime.evaluate("hero_1", 12)
            assert result.position_x == 50


# ============================================================================
# Test Animation Evaluation
# ============================================================================


class TestAnimationEvaluation:
    """Tests for animation frame evaluation."""

    def test_evaluate_exact_keyframe(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating at exact keyframe returns keyframe transform."""
        transform = populated_runtime.evaluate("hero_1", 0)
        assert transform.position_x == 0.0
        assert transform.scale == 1.0

    def test_evaluate_between_keyframes(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating between keyframes returns interpolated transform."""
        transform = populated_runtime.evaluate("hero_1", 12)
        # At t=0.5, position_x should be 50.0
        assert transform.position_x == 50.0
        # Scale should be 1.5 (interpolated between 1.0 and 2.0)
        assert transform.scale == 1.5

    def test_evaluate_empty_keyframes(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating clip with no keyframes returns default transform."""
        transform = populated_runtime.evaluate("villain_default", 15)
        assert transform.position_x is None
        assert transform.scale == 1.0  # default
        assert transform.opacity == 1.0  # default

    def test_evaluate_before_first_keyframe(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating before first keyframe raises error."""
        # villain_default starts at frame 10
        with pytest.raises(InvalidFrameError, match="out of clip range"):
            populated_runtime.evaluate("villain_default", 5)

    def test_evaluate_after_last_keyframe(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating after last keyframe returns last keyframe."""
        transform = populated_runtime.evaluate("hero_1", 24)
        assert transform.position_x == 100.0
        assert transform.scale == 2.0

    def test_evaluate_at_clip_boundary(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating at clip boundary."""
        # villain_default is 10-20
        transform = populated_runtime.evaluate("villain_default", 20)
        assert transform.position_x is None  # no keyframes

    def test_evaluate_outside_clip_range(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating outside clip range raises error."""
        with pytest.raises(InvalidFrameError, match="out of clip range"):
            populated_runtime.evaluate("hero_1", 100)

    def test_evaluate_negative_frame(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating at negative frame raises error."""
        with pytest.raises(InvalidFrameError, match="cannot be negative"):
            populated_runtime.evaluate("hero_1", -1)

    def test_evaluate_unknown_clip(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating unknown clip raises error."""
        with pytest.raises(ClipNotFoundError):
            empty_runtime.evaluate("unknown", 0)

    def test_evaluate_unsupported_interpolation(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that unsupported interpolation raises error."""
        clip = AnimationClip(
            clip_id="bad_clip",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.BOUNCE,  # unsupported
                ),
            ],
        )
        empty_runtime.register(clip)
        with pytest.raises(UnsupportedInterpolationError, match="LINEAR"):
            empty_runtime.evaluate("bad_clip", 12)


# ============================================================================
# Test Multi-Clip Evaluation
# ============================================================================


class TestMultiClipEvaluation:
    """Tests for evaluating multiple clips at once."""

    def test_evaluate_at_frame(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test evaluating all clips at a specific frame."""
        # hero_1 is 0-24, villain_default is 10-20
        results = populated_runtime.evaluate_at_frame(15)
        assert "hero_1" in results
        assert "villain_default" in results

    def test_evaluate_at_frame_excludes_inactive(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test that evaluate_at_frame excludes clips outside frame range."""
        # villain_default is 10-20, hero_1 is 0-24
        results = populated_runtime.evaluate_at_frame(5)
        assert "hero_1" in results
        assert "villain_default" not in results

    def test_evaluate_at_frame_handles_unsupported(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that evaluate_at_frame skips unsupported interpolation."""
        good_clip = AnimationClip(
            clip_id="good",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(position_x=100),
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )
        bad_clip = AnimationClip(
            clip_id="bad",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.ELASTIC,  # unsupported
                ),
            ],
        )
        empty_runtime.register_many([good_clip, bad_clip])
        results = empty_runtime.evaluate_at_frame(12)
        assert "good" in results
        assert "bad" not in results  # skipped due to error

    def test_evaluate_at_frame_negative(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test that evaluate_at_frame rejects negative frame."""
        with pytest.raises(InvalidFrameError, match="cannot be negative"):
            populated_runtime.evaluate_at_frame(-1)


# ============================================================================
# Test Determinism
# ============================================================================


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test that same input produces same output."""
        empty_runtime.register(clip_with_keyframes)

        result1 = empty_runtime.evaluate("hero_1", 12)
        result2 = empty_runtime.evaluate("hero_1", 12)

        assert result1.position_x == result2.position_x
        assert result1.scale == result2.scale

    def test_different_registration_order_same_output(
        self,
        clip_with_keyframes: AnimationClip,
        clip_without_keyframes: AnimationClip,
    ) -> None:
        """Test that registration order doesn't affect evaluation."""
        runtime1 = AnimationRuntime(sequence_id="test1")
        runtime1.register(clip_with_keyframes)
        runtime1.register(clip_without_keyframes)

        runtime2 = AnimationRuntime(sequence_id="test2")
        runtime2.register(clip_without_keyframes)
        runtime2.register(clip_with_keyframes)

        result1 = runtime1.evaluate("hero_1", 12)
        result2 = runtime2.evaluate("hero_1", 12)

        assert result1.position_x == result2.position_x

    def test_multiple_evaluations_same_result(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test that repeated evaluations produce same result."""
        results = [populated_runtime.evaluate("hero_1", 12) for _ in range(10)]
        for result in results:
            assert result.position_x == 50.0


# ============================================================================
# Test Serialization Compatibility
# ============================================================================


class TestSerializationCompatibility:
    """Tests for serialization compatibility."""

    def test_registered_clip_serialization(
        self,
        empty_runtime: AnimationRuntime,
        clip_with_keyframes: AnimationClip,
    ) -> None:
        """Test that registered clips can still be serialized."""
        empty_runtime.register(clip_with_keyframes)
        retrieved = empty_runtime.get_clip("hero_1")

        # Should be the exact same object
        assert retrieved is clip_with_keyframes

        # Should be serializable
        data = retrieved.model_dump()
        assert data["clip_id"] == "hero_1"
        assert data["start_frame"] == 0
        assert data["end_frame"] == 24
        assert len(data["keyframes"]) == 2

    def test_evaluated_transform_serialization(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test that evaluated transforms are serializable."""
        transform = populated_runtime.evaluate("hero_1", 12)
        data = transform.model_dump()
        assert "position_x" in data
        assert "scale" in data


# ============================================================================
# Test Clip Frame Range
# ============================================================================


class TestClipFrameRange:
    """Tests for clip frame range queries."""

    def test_get_clip_frame_range(
        self,
        populated_runtime: AnimationRuntime,
    ) -> None:
        """Test getting clip frame range."""
        start, end = populated_runtime.get_clip_frame_range("hero_1")
        assert start == 0
        assert end == 24

    def test_get_frame_range_unknown_clip(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that getting range for unknown clip raises error."""
        with pytest.raises(ClipNotFoundError):
            empty_runtime.get_clip_frame_range("unknown")


# ============================================================================
# Test Runtime Integration (End-to-End)
# ============================================================================


class TestRuntimeIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test full pipeline from bindings to runtime evaluation."""
        # Step 1: Create AnimationClip objects (simulating create_animation_clips output)
        hero_body_clip = AnimationClip(
            clip_id="hero_1",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0, opacity=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=12,
                    transform=FrameTransform(position_x=50, opacity=0.8),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(position_x=100, opacity=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )

        hero_face_clip = AnimationClip(
            clip_id="hero_2",
            start_frame=0,
            end_frame=24,
            keyframes=[
                AnimationKeyframe(
                    frame_index=0,
                    transform=FrameTransform(position_x=0, scale=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
                AnimationKeyframe(
                    frame_index=24,
                    transform=FrameTransform(position_x=0, scale=1.5),
                    interpolation=InterpolationType.LINEAR,
                ),
            ],
        )

        # Step 2: Register clips in runtime
        empty_runtime.register_many([hero_body_clip, hero_face_clip])

        # Step 3: Verify registration
        assert empty_runtime.count() == 2
        assert "hero_1" in empty_runtime
        assert "hero_2" in empty_runtime

        # Step 4: Evaluate at various frames
        results_frame_0 = empty_runtime.evaluate_at_frame(0)
        assert len(results_frame_0) == 2
        assert results_frame_0["hero_1"].position_x == 0
        assert results_frame_0["hero_2"].position_x == 0

        results_frame_12 = empty_runtime.evaluate_at_frame(12)
        assert len(results_frame_12) == 2
        assert results_frame_12["hero_1"].position_x == 50
        assert results_frame_12["hero_1"].opacity == 0.8
        assert results_frame_12["hero_2"].position_x == 0  # face doesn't move x
        assert results_frame_12["hero_2"].scale == 1.25  # interpolated

        results_frame_24 = empty_runtime.evaluate_at_frame(24)
        assert len(results_frame_24) == 2
        assert results_frame_24["hero_1"].position_x == 100
        assert results_frame_24["hero_1"].opacity == 1.0
        assert results_frame_24["hero_2"].scale == 1.5

    def test_clip_id_collision_handling(
        self,
        empty_runtime: AnimationRuntime,
    ) -> None:
        """Test that collision-safe clip_ids work correctly."""
        # These would have collided with the old f-string approach
        clip_a = AnimationClip(
            clip_id="hero_1__2",  # escaped: hero + "1_2"
            start_frame=0,
            end_frame=10,
        )
        clip_b = AnimationClip(
            clip_id="hero__1_2",  # escaped: hero_1 + "2"
            start_frame=0,
            end_frame=10,
        )

        empty_runtime.register_many([clip_a, clip_b])

        # Both should be registered (no collision)
        assert empty_runtime.count() == 2
        assert empty_runtime.has_clip("hero_1__2")
        assert empty_runtime.has_clip("hero__1_2")

        # Both should evaluate correctly
        assert empty_runtime.evaluate("hero_1__2", 5) is not None
        assert empty_runtime.evaluate("hero__1_2", 5) is not None
