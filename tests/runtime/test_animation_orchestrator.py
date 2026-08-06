"""Tests for animation orchestrator module."""

import pytest

from runtime.animation.consumer import (
    AnimationOrchestrator,
    ClipCreationError,
    OrchestratorState,
)
from tools.frame.models import FrameTransform, InterpolationType
from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    CharacterTransformInput,
    CharacterTransformInputSet,
    _build_clip_id,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def orchestrator() -> AnimationOrchestrator:
    """Create an empty orchestrator."""
    return AnimationOrchestrator()


@pytest.fixture
def single_binding_output() -> CharacterAnimationOutput:
    """Create output with single character binding."""
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
    return CharacterAnimationOutput(
        sequence_id="intro",
        bindings=(binding,),
        metadata=CharacterAnimationMetadata(
            bindings_created=1,
            characters_bound=1,
            palettes_available=0,
            palettes_missing=1,
        ),
    )


@pytest.fixture
def multi_binding_output() -> CharacterAnimationOutput:
    """Create output with multiple character bindings."""
    hero_target = CharacterAnimationTarget(
        character_id="hero",
        layer_id=None,
        sequence_id="intro",
    )
    villain_target = CharacterAnimationTarget(
        character_id="villain",
        layer_id="body",
        sequence_id="intro",
    )
    bindings = (
        CharacterAnimationBinding(target=hero_target, frame_index=0, palette_id=None),
        CharacterAnimationBinding(target=hero_target, frame_index=24, palette_id=None),
        CharacterAnimationBinding(target=villain_target, frame_index=0, palette_id=None),
        CharacterAnimationBinding(target=villain_target, frame_index=24, palette_id=None),
    )
    return CharacterAnimationOutput(
        sequence_id="intro",
        bindings=bindings,
        metadata=CharacterAnimationMetadata(
            bindings_created=4,
            characters_bound=2,
            palettes_available=0,
            palettes_missing=2,
        ),
    )


@pytest.fixture
def transforms_at_keyframes() -> CharacterTransformInputSet:
    """Create transforms matching keyframe positions."""
    transforms = (
        CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(position_x=0, scale=1.0),
            interpolation=InterpolationType.LINEAR,
        ),
        CharacterTransformInput(
            character_id="hero",
            frame_index=24,
            transform=FrameTransform(position_x=100, scale=2.0),
            interpolation=InterpolationType.LINEAR,
        ),
        CharacterTransformInput(
            character_id="villain",
            frame_index=0,
            transform=FrameTransform(position_x=50, scale=1.5),
            interpolation=InterpolationType.LINEAR,
        ),
        CharacterTransformInput(
            character_id="villain",
            frame_index=24,
            transform=FrameTransform(position_x=150, scale=1.0),
            interpolation=InterpolationType.LINEAR,
        ),
    )
    return CharacterTransformInputSet(transforms=transforms)


@pytest.fixture
def sparse_transforms() -> CharacterTransformInputSet:
    """Create sparse transforms (not all frames have transforms)."""
    transforms = (
        CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(position_x=0),
            interpolation=InterpolationType.LINEAR,
        ),
        # Frame 12 has no transform
        CharacterTransformInput(
            character_id="hero",
            frame_index=24,
            transform=FrameTransform(position_x=100),
            interpolation=InterpolationType.LINEAR,
        ),
    )
    return CharacterTransformInputSet(transforms=transforms)


@pytest.fixture
def empty_output() -> CharacterAnimationOutput:
    """Create empty animation output."""
    return CharacterAnimationOutput(
        sequence_id="empty",
        bindings=(),
        metadata=CharacterAnimationMetadata(
            bindings_created=0,
            characters_bound=0,
            palettes_available=0,
            palettes_missing=0,
        ),
    )


@pytest.fixture
def empty_transforms() -> CharacterTransformInputSet:
    """Create empty transforms."""
    return CharacterTransformInputSet(transforms=())


# ============================================================================
# Test Orchestrator Lifecycle
# ============================================================================


class TestOrchestratorLifecycle:
    """Tests for orchestrator lifecycle."""

    def test_create_orchestrator(self) -> None:
        """Test creating an empty orchestrator."""
        orchestrator = AnimationOrchestrator()
        assert orchestrator.sequence_id is None
        assert orchestrator.frame_rate == 24.0
        assert orchestrator.count() == 0

    def test_create_orchestrator_custom_frame_rate(self) -> None:
        """Test creating orchestrator with custom frame rate."""
        orchestrator = AnimationOrchestrator(frame_rate=30.0)
        assert orchestrator.frame_rate == 30.0

    def test_state_property(self) -> None:
        """Test orchestrator state is immutable."""
        orchestrator = AnimationOrchestrator()
        state = orchestrator.state
        assert isinstance(state, OrchestratorState)
        assert state.sequence_id == ""
        assert state.clip_count == 0
        assert state.runtime_frame_rate == 24.0


# ============================================================================
# Test Load Operation
# ============================================================================


class TestLoadOperation:
    """Tests for load operation."""

    def test_load_single_character(
        self,
        orchestrator: AnimationOrchestrator,
        single_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test loading single character animation."""
        clips = orchestrator.load(single_binding_output, transforms_at_keyframes)

        assert len(clips) == 1
        assert orchestrator.sequence_id == "intro"
        assert orchestrator.count() == 1

    def test_load_multiple_characters(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test loading multiple character animations."""
        clips = orchestrator.load(multi_binding_output, transforms_at_keyframes)

        assert len(clips) == 2  # hero + villain
        assert orchestrator.count() == 2

    def test_load_empty_output(
        self,
        orchestrator: AnimationOrchestrator,
        empty_output: CharacterAnimationOutput,
        empty_transforms: CharacterTransformInputSet,
    ) -> None:
        """Test loading empty animation."""
        clips = orchestrator.load(empty_output, empty_transforms)

        assert len(clips) == 0
        assert orchestrator.count() == 0
        assert orchestrator.sequence_id == "empty"

    def test_load_sparse_transforms(
        self,
        orchestrator: AnimationOrchestrator,
        single_binding_output: CharacterAnimationOutput,
        sparse_transforms: CharacterTransformInputSet,
    ) -> None:
        """Test loading with sparse transforms (missing frames)."""
        # Add bindings for frames 0, 12, 24
        target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="1",
            sequence_id="intro",
        )
        output = CharacterAnimationOutput(
            sequence_id="intro",
            bindings=(
                CharacterAnimationBinding(target=target, frame_index=0, palette_id=None),
                CharacterAnimationBinding(target=target, frame_index=12, palette_id=None),
                CharacterAnimationBinding(target=target, frame_index=24, palette_id=None),
            ),
            metadata=CharacterAnimationMetadata(
                bindings_created=3,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )

        clips = orchestrator.load(output, sparse_transforms)

        assert len(clips) == 1
        clip = clips[0]
        # Should have keyframes at 0 and 24 (not 12)
        assert len(clip.keyframes) == 2

    def test_load_updates_sequence_id(
        self,
        orchestrator: AnimationOrchestrator,
    ) -> None:
        """Test that load updates the sequence ID."""
        assert orchestrator.sequence_id is None

        output = CharacterAnimationOutput(
            sequence_id="scene_1",
            bindings=(),
            metadata=CharacterAnimationMetadata(
                bindings_created=0,
                characters_bound=0,
                palettes_available=0,
                palettes_missing=0,
            ),
        )
        transforms = CharacterTransformInputSet(transforms=())

        orchestrator.load(output, transforms)
        assert orchestrator.sequence_id == "scene_1"


# ============================================================================
# Test Reload Operation
# ============================================================================


class TestReloadOperation:
    """Tests for reload operation."""

    def test_reload_replaces_clips(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test that reload replaces existing clips."""
        # Load initial
        orchestrator.load(multi_binding_output, transforms_at_keyframes)
        assert orchestrator.count() == 2

        # Create new output with different sequence
        new_output = CharacterAnimationOutput(
            sequence_id="scene_2",
            bindings=multi_binding_output.bindings,
            metadata=multi_binding_output.metadata,
        )

        # Reload
        orchestrator.reload(new_output, transforms_at_keyframes)
        assert orchestrator.count() == 2
        assert orchestrator.sequence_id == "scene_2"


# ============================================================================
# Test Evaluation
# ============================================================================


class TestEvaluation:
    """Tests for evaluation through orchestrator."""

    def test_evaluate_after_load(
        self,
        orchestrator: AnimationOrchestrator,
        single_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating after loading."""
        orchestrator.load(single_binding_output, transforms_at_keyframes)

        # Get the clip_id
        clips = orchestrator.list_clips()
        clip_id = clips[0].clip_id

        # Evaluate
        transform = orchestrator.evaluate(clip_id, 0)
        assert transform.position_x == 0.0
        assert transform.scale == 1.0

    def test_evaluate_between_keyframes(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating between keyframes."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        hero_clip = next(c for c in clips if "hero" in c.clip_id)

        # Evaluate at frame 12 (between 0 and 24)
        transform = orchestrator.evaluate(hero_clip.clip_id, 12)
        assert transform.position_x == 50.0  # Linear interpolation
        assert transform.scale == 1.5  # Linear interpolation

    def test_evaluate_at_frame_all_clips(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating all clips at a frame."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        results = orchestrator.evaluate_at_frame(12)

        assert len(results) == 2
        # Hero: interpolated from 0 to 100 -> 50
        # Villain: interpolated from 50 to 150 -> 100
        for clip_id, transform in results.items():
            if "hero" in clip_id:
                assert transform.position_x == 50.0
            else:
                assert transform.position_x == 100.0

    def test_evaluate_exact_keyframe(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating at exact keyframe."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        hero_clip = next(c for c in clips if "hero" in c.clip_id)

        transform = orchestrator.evaluate(hero_clip.clip_id, 0)
        assert transform.position_x == 0.0
        assert transform.scale == 1.0

    def test_evaluate_unknown_clip(
        self,
        orchestrator: AnimationOrchestrator,
        empty_output: CharacterAnimationOutput,
        empty_transforms: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating unknown clip raises error."""
        from runtime.animation import ClipNotFoundError

        orchestrator.load(empty_output, empty_transforms)

        with pytest.raises(ClipNotFoundError):
            orchestrator.evaluate("unknown", 0)

    def test_evaluate_outside_range(
        self,
        orchestrator: AnimationOrchestrator,
        single_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating outside clip range raises error."""
        from runtime.animation import InvalidFrameError

        orchestrator.load(single_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        clip_id = clips[0].clip_id

        with pytest.raises(InvalidFrameError):
            orchestrator.evaluate(clip_id, 100)

    def test_evaluate_negative_frame(
        self,
        orchestrator: AnimationOrchestrator,
        single_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test evaluating negative frame raises error."""
        from runtime.animation import InvalidFrameError

        orchestrator.load(single_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        clip_id = clips[0].clip_id

        with pytest.raises(InvalidFrameError):
            orchestrator.evaluate(clip_id, -1)


# ============================================================================
# Test Unsupported Interpolation
# ============================================================================


class TestUnsupportedInterpolation:
    """Tests for V1 interpolation limitation."""

    def test_unsupported_interpolation_raises_error(
        self,
        orchestrator: AnimationOrchestrator,
    ) -> None:
        """Test that non-LINEAR interpolation raises error at evaluation."""
        from runtime.animation import UnsupportedInterpolationError

        # Create output
        target = CharacterAnimationTarget(
            character_id="hero",
            layer_id=None,
            sequence_id="intro",
        )
        output = CharacterAnimationOutput(
            sequence_id="intro",
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

        # Create transforms with non-LINEAR interpolation
        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=24,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.BOUNCE,  # Unsupported in V1
                ),
            )
        )

        # Load succeeds
        clips = orchestrator.load(output, transforms)
        assert len(clips) == 1

        # Evaluation between keyframes fails
        with pytest.raises(UnsupportedInterpolationError):
            orchestrator.evaluate(clips[0].clip_id, 12)


# ============================================================================
# Test Atomicity
# ============================================================================


class TestAtomicity:
    """Tests for atomicity guarantees."""

    def test_failed_load_preserves_state(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test that failed load preserves previous state."""
        # Load initial valid data
        orchestrator.load(multi_binding_output, transforms_at_keyframes)
        assert orchestrator.count() == 2
        initial_sequence = orchestrator.sequence_id

        # Create output with duplicate bindings (will fail)
        target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="1",
            sequence_id="intro",
        )
        bad_output = CharacterAnimationOutput(
            sequence_id="bad",
            bindings=(
                CharacterAnimationBinding(target=target, frame_index=0, palette_id=None),
                CharacterAnimationBinding(target=target, frame_index=0, palette_id=None),  # Duplicate!
            ),
            metadata=CharacterAnimationMetadata(
                bindings_created=2,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )

        # Load should fail
        with pytest.raises(ClipCreationError):
            orchestrator.load(bad_output, transforms_at_keyframes)

        # State should be unchanged
        assert orchestrator.count() == 2
        assert orchestrator.sequence_id == initial_sequence


# ============================================================================
# Test Determinism
# ============================================================================


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(
        self,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test that same inputs produce same outputs."""
        results = []

        for _ in range(5):
            orchestrator = AnimationOrchestrator()
            orchestrator.load(multi_binding_output, transforms_at_keyframes)

            clip_id = next(c.clip_id for c in orchestrator.list_clips() if "hero" in c.clip_id)
            transform = orchestrator.evaluate(clip_id, 12)
            results.append(transform.position_x)

        assert all(x == results[0] for x in results)

    def test_registration_order_does_not_affect(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test that evaluation is independent of internal ordering."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        hero_clip_id = next(c.clip_id for c in orchestrator.list_clips() if "hero" in c.clip_id)

        results = [orchestrator.evaluate(hero_clip_id, 12) for _ in range(10)]
        assert all(r.position_x == results[0].position_x for r in results)


# ============================================================================
# Test End-to-End Pipeline
# ============================================================================


class TestEndToEndPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline_from_domain_to_evaluation(
        self,
        orchestrator: AnimationOrchestrator,
    ) -> None:
        """Test complete pipeline: domain → clips → runtime → evaluation."""
        # Step 1: Create domain data (simulating upstream pipeline)
        hero_target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="body",
            sequence_id="scene_1",
        )
        hero_face_target = CharacterAnimationTarget(
            character_id="hero",
            layer_id="face",
            sequence_id="scene_1",
        )

        bindings = (
            # Hero body bindings
            CharacterAnimationBinding(target=hero_target, frame_index=0, palette_id=None),
            CharacterAnimationBinding(target=hero_target, frame_index=48, palette_id=None),
            # Hero face bindings
            CharacterAnimationBinding(target=hero_face_target, frame_index=0, palette_id=None),
            CharacterAnimationBinding(target=hero_face_target, frame_index=48, palette_id=None),
        )

        animation_output = CharacterAnimationOutput(
            sequence_id="scene_1",
            bindings=bindings,
            metadata=CharacterAnimationMetadata(
                bindings_created=4,
                characters_bound=1,
                palettes_available=0,
                palettes_missing=1,
            ),
        )

        # Step 2: Create transform inputs
        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=0,
                    transform=FrameTransform(position_x=0, scale=1.0, opacity=1.0),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=48,
                    transform=FrameTransform(position_x=200, scale=2.0, opacity=0.8),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        # Step 3: Load into orchestrator
        clips = orchestrator.load(animation_output, transforms)

        # Step 4: Verify clip creation
        assert len(clips) == 2  # body + face
        clip_ids = {c.clip_id for c in clips}

        # Verify collision-safe clip_ids (underscores only escaped if present)
        assert "hero_body" in clip_ids
        assert "hero_face" in clip_ids

        # Step 5: Evaluate at various frames
        body_clip_id = "hero_body"
        face_clip_id = "hero_face"

        # At frame 0
        results_0 = orchestrator.evaluate_at_frame(0)
        assert results_0[body_clip_id].position_x == 0
        assert results_0[body_clip_id].opacity == 1.0
        assert results_0[face_clip_id].position_x == 0

        # At frame 24 (midpoint)
        results_24 = orchestrator.evaluate_at_frame(24)
        assert results_24[body_clip_id].position_x == 100  # Interpolated
        assert results_24[body_clip_id].opacity == 0.9  # Interpolated
        assert results_24[body_clip_id].scale == 1.5  # Interpolated

        # At frame 48
        results_48 = orchestrator.evaluate_at_frame(48)
        assert results_48[body_clip_id].position_x == 200
        assert results_48[body_clip_id].opacity == 0.8
        assert results_48[body_clip_id].scale == 2.0

        # Step 6: Verify state
        state = orchestrator.state
        assert state.sequence_id == "scene_1"
        assert state.clip_count == 2

    def test_clip_id_collision_prevention_in_orchestrator(
        self,
        orchestrator: AnimationOrchestrator,
    ) -> None:
        """Test that collision-safe clip_ids work correctly in orchestrator."""
        # These would have collided with simple f-string approach
        target_a = CharacterAnimationTarget(
            character_id="hero",
            layer_id="1_2",  # Contains underscore
            sequence_id="scene",
        )
        target_b = CharacterAnimationTarget(
            character_id="hero_1",  # Contains underscore
            layer_id="2",
            sequence_id="scene",
        )

        output = CharacterAnimationOutput(
            sequence_id="scene",
            bindings=(
                CharacterAnimationBinding(target=target_a, frame_index=0, palette_id=None),
                CharacterAnimationBinding(target=target_b, frame_index=0, palette_id=None),
            ),
            metadata=CharacterAnimationMetadata(
                bindings_created=2,
                characters_bound=2,
                palettes_available=0,
                palettes_missing=2,
            ),
        )

        transforms = CharacterTransformInputSet(
            transforms=(
                CharacterTransformInput(
                    character_id="hero",
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
                CharacterTransformInput(
                    character_id="hero_1",
                    frame_index=0,
                    transform=FrameTransform(),
                    interpolation=InterpolationType.LINEAR,
                ),
            )
        )

        clips = orchestrator.load(output, transforms)

        # Both clips should be registered with different IDs
        assert len(clips) == 2
        clip_ids = {c.clip_id for c in clips}

        # Verify collision-safe encoding
        expected_a = _build_clip_id("hero", "1_2")  # "hero_1__2"
        expected_b = _build_clip_id("hero_1", "2")  # "hero__1_2"
        assert expected_a in clip_ids
        assert expected_b in clip_ids
        assert expected_a != expected_b


# ============================================================================
# Test API Surface
# ============================================================================


class TestAPISurface:
    """Tests for orchestrator API surface."""

    def test_get_runtime(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test get_runtime returns underlying AnimationRuntime."""
        from runtime.animation import AnimationRuntime

        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        runtime = orchestrator.get_runtime()
        assert isinstance(runtime, AnimationRuntime)
        assert runtime.count() == orchestrator.count()

    def test_list_clips(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test list_clips returns sorted clips."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        assert len(clips) == 2
        # Should be sorted by clip_id
        assert clips[0].clip_id < clips[1].clip_id

    def test_has_clip(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test has_clip works correctly."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        assert orchestrator.has_clip(clips[0].clip_id) is True
        assert orchestrator.has_clip("nonexistent") is False

    def test_contains_dunder(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test __contains__ works correctly."""
        orchestrator.load(multi_binding_output, transforms_at_keyframes)

        clips = orchestrator.list_clips()
        assert clips[0].clip_id in orchestrator
        assert "nonexistent" not in orchestrator

    def test_len(
        self,
        orchestrator: AnimationOrchestrator,
        multi_binding_output: CharacterAnimationOutput,
        transforms_at_keyframes: CharacterTransformInputSet,
    ) -> None:
        """Test __len__ works correctly."""
        assert len(orchestrator) == 0

        orchestrator.load(multi_binding_output, transforms_at_keyframes)
        assert len(orchestrator) == 2
