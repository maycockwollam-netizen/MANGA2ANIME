"""Tests for character animation integration contracts."""

import pytest

from tools.frame.models import FrameTransform, InterpolationType
from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationInput,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    CharacterTransformInput,
    CharacterTransformInputSet,
    _build_clip_id,
    build_character_animation_bindings,
    create_animation_clips,
)

# ============================================================================
# Fixtures
# ============================================================================


class MockReference:
    """Mock CharacterFrameReference for testing."""

    def __init__(
        self,
        character_id: str,
        frame_index: int,
        layer_index: int | None = None,
        palette_id: str | None = None,
    ):
        self.character_id = character_id
        self.frame_index = frame_index
        self.layer_index = layer_index
        self.palette_id = palette_id


@pytest.fixture
def basic_references() -> tuple:
    """Create basic references for testing."""
    return (
        MockReference(character_id="char_a", frame_index=0, layer_index=1),
        MockReference(character_id="char_a", frame_index=1, layer_index=1),
        MockReference(character_id="char_b", frame_index=0, layer_index=2),
    )


@pytest.fixture
def basic_input() -> CharacterAnimationInput:
    """Create basic input for testing."""
    return CharacterAnimationInput(
        sequence_id="seq_001",
        frame_count=10,
        palette_associations=(
            ("char_a", "palette_a"),
            ("char_b", "palette_b"),
        ),
    )


# ============================================================================
# Test CharacterAnimationTarget
# ============================================================================


class TestCharacterAnimationTarget:
    """Tests for CharacterAnimationTarget."""

    def test_construction(self) -> None:
        """Test basic construction."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        assert target.character_id == "char_1"
        assert target.layer_id == "layer_1"
        assert target.sequence_id == "seq_001"

    def test_without_layer(self) -> None:
        """Test construction without layer."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id=None,
            sequence_id="seq_001",
        )
        assert target.layer_id is None

    def test_target_is_frozen(self) -> None:
        """Test that target is frozen."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        with pytest.raises((TypeError, AttributeError)):
            target.character_id = "new"  # type: ignore[misc]

    def test_model_dump(self) -> None:
        """Test serialization."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        data = target.model_dump()
        assert data["character_id"] == "char_1"
        assert data["layer_id"] == "layer_1"
        assert data["sequence_id"] == "seq_001"


# ============================================================================
# Test CharacterAnimationBinding
# ============================================================================


class TestCharacterAnimationBinding:
    """Tests for CharacterAnimationBinding."""

    def test_construction(self) -> None:
        """Test basic construction."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=5,
            palette_id="palette_1",
        )
        assert binding.target is target
        assert binding.frame_index == 5
        assert binding.palette_id == "palette_1"

    def test_binding_is_frozen(self) -> None:
        """Test that binding is frozen."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=5,
            palette_id=None,
        )
        with pytest.raises((TypeError, AttributeError)):
            binding.frame_index = 10  # type: ignore[misc]

    def test_model_dump(self) -> None:
        """Test serialization."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=5,
            palette_id=None,
        )
        data = binding.model_dump()
        assert data["frame_index"] == 5
        assert data["target"]["character_id"] == "char_1"


# ============================================================================
# Test CharacterAnimationMetadata
# ============================================================================


class TestCharacterAnimationMetadata:
    """Tests for CharacterAnimationMetadata."""

    def test_construction(self) -> None:
        """Test basic construction."""
        metadata = CharacterAnimationMetadata(
            bindings_created=10,
            characters_bound=3,
            palettes_available=2,
            palettes_missing=1,
        )
        assert metadata.bindings_created == 10
        assert metadata.characters_bound == 3

    def test_metadata_is_frozen(self) -> None:
        """Test that metadata is frozen."""
        metadata = CharacterAnimationMetadata(
            bindings_created=1,
            characters_bound=1,
            palettes_available=0,
            palettes_missing=1,
        )
        with pytest.raises((TypeError, ValueError)):
            metadata.bindings_created = 10  # type: ignore[misc]


# ============================================================================
# Test CharacterAnimationInput
# ============================================================================


class TestCharacterAnimationInput:
    """Tests for CharacterAnimationInput."""

    def test_construction(self) -> None:
        """Test basic construction."""
        inp = CharacterAnimationInput(
            sequence_id="seq_001",
            frame_count=10,
        )
        assert inp.sequence_id == "seq_001"
        assert inp.frame_count == 10
        assert inp.palette_associations == ()

    def test_with_palettes(self) -> None:
        """Test construction with palette associations."""
        inp = CharacterAnimationInput(
            sequence_id="seq_001",
            frame_count=10,
            palette_associations=(
                ("char_1", "palette_1"),
                ("char_2", "palette_2"),
            ),
        )
        assert len(inp.palette_associations) == 2

    def test_empty_sequence_id_rejected(self) -> None:
        """Test that empty sequence_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            CharacterAnimationInput(
                sequence_id="",
                frame_count=10,
            )

    def test_negative_frame_count_rejected(self) -> None:
        """Test that negative frame_count is rejected."""
        with pytest.raises(ValueError):
            CharacterAnimationInput(
                sequence_id="seq_001",
                frame_count=-1,
            )

    def test_input_is_mutable(self) -> None:
        """Test that input is mutable (not frozen)."""
        inp = CharacterAnimationInput(
            sequence_id="seq_001",
            frame_count=10,
        )
        inp.frame_count = 20  # Should not raise
        assert inp.frame_count == 20


# ============================================================================
# Test build_character_animation_bindings
# ============================================================================


class TestBuildCharacterAnimationBindings:
    """Tests for the main binding function."""

    def test_basic_binding(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test basic binding creation."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        assert output.sequence_id == "seq_001"
        assert len(output.bindings) == 3
        assert output.metadata.bindings_created == 3
        assert output.metadata.characters_bound == 2

    def test_bindings_sorted(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that bindings are deterministically sorted."""
        references = (
            MockReference(character_id="char_c", frame_index=2),
            MockReference(character_id="char_a", frame_index=0),
            MockReference(character_id="char_b", frame_index=1),
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        # Should be sorted by (character_id, frame_index)
        assert output.bindings[0].target.character_id == "char_a"
        assert output.bindings[1].target.character_id == "char_b"
        assert output.bindings[2].target.character_id == "char_c"

    def test_invalid_frame_index_rejected(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that invalid frame index is rejected."""
        references = (
            MockReference(character_id="char_1", frame_index=999),
        )

        with pytest.raises(ValueError, match="exceeds frame_count"):
            build_character_animation_bindings(
                input_contract=basic_input,
                references=references,
            )

    def test_negative_frame_index_rejected(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that negative frame index is rejected."""
        references = (
            MockReference(character_id="char_1", frame_index=-1),
        )

        with pytest.raises(ValueError, match="cannot be negative"):
            build_character_animation_bindings(
                input_contract=basic_input,
                references=references,
            )

    def test_palette_association(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that palette associations are preserved."""
        references = (
            MockReference(character_id="char_a", frame_index=0),
            MockReference(character_id="char_b", frame_index=0),
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        # Find char_a binding
        char_a_binding = next(
            b for b in output.bindings
            if b.target.character_id == "char_a"
        )
        assert char_a_binding.palette_id == "palette_a"

        # Find char_b binding
        char_b_binding = next(
            b for b in output.bindings
            if b.target.character_id == "char_b"
        )
        assert char_b_binding.palette_id == "palette_b"

    def test_missing_palette_reported(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that missing palettes are reported."""
        # Only char_a has palette in fixture
        references = (
            MockReference(character_id="char_a", frame_index=0),
            MockReference(character_id="char_c", frame_index=0),  # No palette
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        assert output.metadata.palettes_available == 1
        assert output.metadata.palettes_missing == 1

    def test_target_identity(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test that target identity is correctly created."""
        references = (
            MockReference(
                character_id="char_1",
                frame_index=0,
                layer_index=5,
            ),
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        binding = output.bindings[0]
        assert binding.target.character_id == "char_1"
        assert binding.target.layer_id == "5"  # Converted to string
        assert binding.target.sequence_id == "seq_001"


# ============================================================================
# Test Deep Immutability
# ============================================================================


class TestDeepImmutability:
    """Tests for deep immutability guarantees."""

    def test_output_is_frozen(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test that output is frozen."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        with pytest.raises((TypeError, AttributeError)):
            output.sequence_id = "new"  # type: ignore[misc]

    def test_bindings_tuple_immutable(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test that bindings tuple is immutable."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        with pytest.raises((TypeError, AttributeError)):
            output.bindings.append(  # type: ignore[attr-defined]
                CharacterAnimationBinding(
                    target=CharacterAnimationTarget(
                        character_id="new",
                        layer_id=None,
                        sequence_id="seq_001",
                    ),
                    frame_index=0,
                    palette_id=None,
                )
            )

    def test_metadata_immutable(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test that metadata is immutable."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        with pytest.raises((TypeError, ValueError)):
            output.metadata.bindings_created = 99  # type: ignore[misc]

    def test_target_immutable(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test that targets are immutable."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        target = output.bindings[0].target
        with pytest.raises((TypeError, AttributeError)):
            target.character_id = "new"  # type: ignore[misc]


# ============================================================================
# Test Serialization
# ============================================================================


class TestSerialization:
    """Tests for serialization behavior."""

    def test_target_serialization(self) -> None:
        """Test target serialization."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        data = target.model_dump()
        assert isinstance(data, dict)
        assert data["character_id"] == "char_1"

    def test_binding_serialization(self) -> None:
        """Test binding serialization."""
        target = CharacterAnimationTarget(
            character_id="char_1",
            layer_id="layer_1",
            sequence_id="seq_001",
        )
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=5,
            palette_id=None,
        )
        data = binding.model_dump()
        assert isinstance(data, dict)
        assert data["frame_index"] == 5

    def test_metadata_serialization(self) -> None:
        """Test metadata serialization."""
        metadata = CharacterAnimationMetadata(
            bindings_created=10,
            characters_bound=3,
            palettes_available=2,
            palettes_missing=1,
        )
        data = metadata.model_dump()
        assert data["bindings_created"] == 10


# ============================================================================
# Test Determinism
# ============================================================================


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Test that same input produces same output."""
        output1 = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )
        output2 = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        assert output1.bindings == output2.bindings
        assert output1.metadata == output2.metadata

    def test_deterministic_sorting(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Test deterministic sorting of bindings."""
        references = (
            MockReference(character_id="char_b", frame_index=1),
            MockReference(character_id="char_a", frame_index=0),
            MockReference(character_id="char_b", frame_index=0),
            MockReference(character_id="char_a", frame_index=1),
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        # Should be sorted by (character_id, frame_index)
        expected_order = [
            ("char_a", 0),
            ("char_a", 1),
            ("char_b", 0),
            ("char_b", 1),
        ]
        actual_order = [
            (b.target.character_id, b.frame_index)
            for b in output.bindings
        ]
        assert actual_order == expected_order


# ============================================================================
# Test Dependency Boundary
# ============================================================================


class TestDependencyBoundary:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify no forbidden imports."""
        import tools.manga_frame.character_animation as module
        source_file = module.__file__
        assert source_file is not None

        with open(source_file) as f:
            content = f.read()

        forbidden = [
            "from PIL", "import PIL",
            "from cv2", "import cv2",
            "from numpy", "import numpy",
            "from torch", "import torch",
            "from tensorflow", "import tensorflow",
            "from diffusers", "import diffusers",
            "from transformers", "import transformers",
            "from requests", "import requests",
            "from ffmpeg", "import ffmpeg",
            "from moviepy", "import moviepy",
            "import gpu", "import cuda",
            "from runtime", "import runtime",
            "from agents", "import agents",
            "from apps", "import apps",
            "from core.", "import core.",
            "from render", "import render",
            "from audio", "import audio",
            "from vfx", "import vfx",
        ]

        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"

    def test_module_importable(self) -> None:
        """Verify module can be imported."""
        from tools.manga_frame.character_animation import (
            CharacterAnimationInput,
            build_character_animation_bindings,
        )
        assert CharacterAnimationInput is not None
        assert CharacterAnimationOutput is not None
        assert build_character_animation_bindings is not None


# ============================================================================
# Test No Animation Generation
# ============================================================================


class TestNoAnimationGeneration:
    """Tests to verify no animation generation occurs."""

    def test_no_keyframes_created(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Verify no AnimationKeyframe objects are created."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        # Bindings should only contain structural info, not AnimationKeyframe
        for binding in output.bindings:
            # Binding should not have keyframes attribute
            assert not hasattr(binding, "keyframes")
            # Binding should not have transforms
            assert not hasattr(binding, "transform")

    def test_no_interpolation(
        self,
        basic_input: CharacterAnimationInput,
    ) -> None:
        """Verify no interpolation logic is present."""
        references = (
            MockReference(character_id="char_1", frame_index=0),
            MockReference(character_id="char_1", frame_index=1),
            MockReference(character_id="char_1", frame_index=2),
        )

        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=references,
        )

        # Each binding should be independent - no interpolation metadata
        for binding in output.bindings:
            # No interpolation type should be set
            assert not hasattr(binding, "interpolation")

    def test_targets_not_clips(
        self,
        basic_input: CharacterAnimationInput,
        basic_references: tuple,
    ) -> None:
        """Verify targets are identity only, not AnimationClip."""
        output = build_character_animation_bindings(
            input_contract=basic_input,
            references=basic_references,
        )

        for binding in output.bindings:
            target = binding.target
            # Target should not have clip attributes
            assert not hasattr(target, "keyframes")
            assert not hasattr(target, "start_frame")
            assert not hasattr(target, "end_frame")


# ============================================================================
# Test CharacterTransformInput
# ============================================================================


class TestCharacterTransformInput:
    """Tests for CharacterTransformInput."""

    def test_construction(self) -> None:
        """Test basic construction."""
        transform = FrameTransform(position_x=100)
        input_data = CharacterTransformInput(
            character_id="hero",
            frame_index=5,
            transform=transform,
        )
        assert input_data.character_id == "hero"
        assert input_data.frame_index == 5
        assert input_data.transform.position_x == 100
        assert input_data.interpolation == InterpolationType.LINEAR

    def test_character_id_trimming(self) -> None:
        """Test character_id is trimmed."""
        input_data = CharacterTransformInput(
            character_id="  hero  ",
            frame_index=0,
            transform=FrameTransform(),
        )
        assert input_data.character_id == "hero"

    def test_empty_character_id_rejected(self) -> None:
        """Test empty character_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            CharacterTransformInput(
                character_id="",
                frame_index=0,
                transform=FrameTransform(),
            )

    def test_whitespace_only_character_id_rejected(self) -> None:
        """Test whitespace-only character_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            CharacterTransformInput(
                character_id="   ",
                frame_index=0,
                transform=FrameTransform(),
            )

    def test_negative_frame_index_rejected(self) -> None:
        """Test negative frame_index is rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            CharacterTransformInput(
                character_id="hero",
                frame_index=-1,
                transform=FrameTransform(),
            )

    def test_explicit_interpolation(self) -> None:
        """Test explicit interpolation type."""
        input_data = CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(),
            interpolation=InterpolationType.EASE_IN_OUT,
        )
        assert input_data.interpolation == InterpolationType.EASE_IN_OUT

    def test_input_is_frozen(self) -> None:
        """Test that input is frozen."""
        input_data = CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(),
        )
        with pytest.raises((TypeError, AttributeError)):
            input_data.character_id = "new"  # type: ignore[misc]

    def test_model_dump(self) -> None:
        """Test serialization."""
        input_data = CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(position_x=100),
            interpolation=InterpolationType.LINEAR,
        )
        data = input_data.model_dump()
        assert data["character_id"] == "hero"
        assert data["frame_index"] == 0
        assert data["transform"]["position_x"] == 100
        assert data["interpolation"] == "linear"


class TestCharacterTransformInputSet:
    """Tests for CharacterTransformInputSet."""

    def test_single_transform(self) -> None:
        """Test creating set with single transform."""
        transform = CharacterTransformInput(
            character_id="hero",
            frame_index=0,
            transform=FrameTransform(),
        )
        input_set = CharacterTransformInputSet(transforms=(transform,))
        assert len(input_set.transforms) == 1

    def test_multiple_transforms_sorted(self) -> None:
        """Test multiple transforms are sorted."""
        transforms = [
            CharacterTransformInput("hero", 10, FrameTransform()),
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("hero", 5, FrameTransform()),
        ]
        input_set = CharacterTransformInputSet(transforms=transforms)
        frame_indices = [t.frame_index for t in input_set.transforms]
        assert frame_indices == [0, 5, 10]

    def test_duplicate_identity_rejected(self) -> None:
        """Test duplicate (character_id, frame_index) is rejected."""
        transforms = [
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("hero", 0, FrameTransform()),
        ]
        with pytest.raises(ValueError, match="duplicate"):
            CharacterTransformInputSet(transforms=transforms)

    def test_different_characters_same_frame_allowed(self) -> None:
        """Test same frame index for different characters is allowed."""
        transforms = [
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("villain", 0, FrameTransform()),
        ]
        input_set = CharacterTransformInputSet(transforms=transforms)
        assert len(input_set.transforms) == 2

    def test_transforms_stored_as_tuple(self) -> None:
        """Test transforms are stored as tuple."""
        transforms = [
            CharacterTransformInput("hero", 0, FrameTransform()),
        ]
        input_set = CharacterTransformInputSet(transforms=transforms)
        assert isinstance(input_set.transforms, tuple)


# ============================================================================
# Test _build_clip_id (collision-safe)
# ============================================================================


class TestBuildClipId:
    """Tests for _build_clip_id collision-safe clip_id generation."""

    def test_basic_ids(self) -> None:
        """Test basic character_id and layer_id."""
        assert _build_clip_id("hero", "1") == "hero_1"

    def test_none_layer_id(self) -> None:
        """Test None layer_id produces 'default' suffix."""
        assert _build_clip_id("hero", None) == "hero_default"

    def test_underscore_in_character_id(self) -> None:
        """Test underscore in character_id is escaped."""
        assert _build_clip_id("hero_1", "2") == "hero__1_2"

    def test_underscore_in_layer_id(self) -> None:
        """Test underscore in layer_id is escaped."""
        assert _build_clip_id("hero", "1_2") == "hero_1__2"

    def test_underscores_in_both(self) -> None:
        """Test underscores in both character_id and layer_id."""
        assert _build_clip_id("hero_1", "2_3") == "hero__1_2__3"

    def test_no_collision_hero_1_2_vs_hero_1(self) -> None:
        """Test no collision between (hero, 1_2) and (hero_1, 2)."""
        clip_a = _build_clip_id("hero", "1_2")  # hero_1__2
        clip_b = _build_clip_id("hero_1", "2")  # hero__1_2
        assert clip_a != clip_b

    def test_no_collision_hero_2_vs_hero_1(self) -> None:
        """Test distinct IDs produce distinct clip_ids."""
        clip_a = _build_clip_id("hero", "1")
        clip_b = _build_clip_id("hero", "2")
        assert clip_a != clip_b

    def test_different_characters_same_layer(self) -> None:
        """Test different characters produce different clip_ids."""
        clip_a = _build_clip_id("hero", "1")
        clip_b = _build_clip_id("villain", "1")
        assert clip_a != clip_b

    def test_deterministic(self) -> None:
        """Test clip_id is deterministic."""
        clip_a = _build_clip_id("hero_1", "2_3")
        clip_b = _build_clip_id("hero_1", "2_3")
        assert clip_a == clip_b


# ============================================================================
# Test create_animation_clips
# ============================================================================


class TestCreateAnimationClips:
    """Tests for create_animation_clips function."""

    def _make_output(self, bindings: list) -> CharacterAnimationOutput:
        """Create a CharacterAnimationOutput from bindings."""
        return CharacterAnimationOutput(
            sequence_id="seq",
            bindings=tuple(bindings),
            metadata=CharacterAnimationMetadata(
                bindings_created=len(bindings),
                characters_bound=len({b.target.character_id for b in bindings}),
                palettes_available=0,
                palettes_missing=len(bindings),
            ),
        )

    def _make_transforms(self, transforms: list) -> CharacterTransformInputSet:
        """Create a CharacterTransformInputSet from transforms."""
        return CharacterTransformInputSet(transforms=tuple(transforms))

    def test_empty_bindings_returns_empty_tuple(self) -> None:
        """Test empty bindings produce empty tuple."""
        output = self._make_output([])
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)
        assert clips == ()

    def test_one_character_one_frame_one_clip(self) -> None:
        """Test one character with one frame produces one clip."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", "1", "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert clips[0].clip_id == "hero_1"
        assert clips[0].start_frame == 0
        assert clips[0].end_frame == 0

    def test_one_character_multiple_frames_one_clip(self) -> None:
        """Test one character with multiple frames produces one clip."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=5,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=10,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert clips[0].start_frame == 0
        assert clips[0].end_frame == 10

    def test_multiple_characters_produce_multiple_clips(self) -> None:
        """Test multiple characters produce multiple clips."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("villain", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 2
        clip_ids = {c.clip_id for c in clips}
        assert "hero_1" in clip_ids
        assert "villain_1" in clip_ids

    def test_same_character_different_layers_separate_clips(self) -> None:
        """Test same character on different layers produces separate clips."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "2", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 2
        clip_ids = {c.clip_id for c in clips}
        assert "hero_1" in clip_ids
        assert "hero_2" in clip_ids

    def test_none_layer_id_handling(self) -> None:
        """Test that None layer_id produces default suffix."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", None, "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert clips[0].clip_id == "hero_default"

    def test_clip_id_no_collision(self) -> None:
        """Test that clip_ids don't collide with underscores."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1_2", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero_1", "2", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("hero_1", 0, FrameTransform()),
        ])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 2
        clip_ids = {c.clip_id for c in clips}
        # These should be distinct due to escaping
        assert "hero_1__2" in clip_ids
        assert "hero__1_2" in clip_ids
        assert len(clip_ids) == 2  # No collision

    def test_transform_correctly_mapped(self) -> None:
        """Test transform data is correctly mapped to keyframes."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", "1", "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([
            CharacterTransformInput("hero", 0, FrameTransform(position_x=100)),
        ])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert len(clips[0].keyframes) == 1
        assert clips[0].keyframes[0].transform.position_x == 100

    def test_interpolation_correctly_mapped(self) -> None:
        """Test interpolation is correctly mapped."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", "1", "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([
            CharacterTransformInput(
                "hero",
                0,
                FrameTransform(),
                interpolation=InterpolationType.EASE_IN_OUT,
            ),
        ])
        clips = create_animation_clips(output, transforms)

        assert len(clips[0].keyframes) == 1
        assert clips[0].keyframes[0].interpolation == InterpolationType.EASE_IN_OUT

    def test_missing_transform_no_keyframe(self) -> None:
        """Test that missing transform results in no keyframe."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", "1", "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([])  # No transforms
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert len(clips[0].keyframes) == 0
        assert clips[0].default_transform == FrameTransform()

    def test_default_transform_is_identity(self) -> None:
        """Test that default_transform is FrameTransform() (identity)."""
        binding = CharacterAnimationBinding(
            target=CharacterAnimationTarget("hero", "1", "seq"),
            frame_index=0,
            palette_id=None,
        )
        output = self._make_output([binding])
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        default = clips[0].default_transform
        assert default.position_x is None
        assert default.scale == 1.0
        assert default.opacity == 1.0

    def test_duplicate_binding_rejected(self) -> None:
        """Test duplicate (character, layer, frame) binding is rejected."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])

        with pytest.raises(ValueError, match="duplicate binding"):
            create_animation_clips(output, transforms)

    def test_determinism_across_calls(self) -> None:
        """Test same input produces same output across calls."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=10,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("hero", 10, FrameTransform()),
        ])

        clips1 = create_animation_clips(output, transforms)
        clips2 = create_animation_clips(output, transforms)

        assert len(clips1) == len(clips2)
        assert clips1[0].clip_id == clips2[0].clip_id
        assert clips1[0].start_frame == clips2[0].start_frame
        assert clips1[0].end_frame == clips2[0].end_frame

    def test_keyframes_sorted(self) -> None:
        """Test keyframes are sorted by frame_index."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=10,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=5,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([
            CharacterTransformInput("hero", 0, FrameTransform()),
            CharacterTransformInput("hero", 5, FrameTransform()),
            CharacterTransformInput("hero", 10, FrameTransform()),
        ])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        keyframes = clips[0].keyframes
        assert keyframes[0].frame_index == 0
        assert keyframes[1].frame_index == 5
        assert keyframes[2].frame_index == 10

    def test_clips_sorted_by_clip_id(self) -> None:
        """Test clips are sorted by clip_id."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("z", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("a", "1", "seq"),
                frame_index=0,
                palette_id=None,
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert clips[0].clip_id == "a_1"
        assert clips[1].clip_id == "z_1"

    def test_palette_id_does_not_affect_clip(self) -> None:
        """Test palette_id does not affect clip_id or clip grouping."""
        bindings = [
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=0,
                palette_id="palette_red",
            ),
            CharacterAnimationBinding(
                target=CharacterAnimationTarget("hero", "1", "seq"),
                frame_index=5,
                palette_id="palette_blue",
            ),
        ]
        output = self._make_output(bindings)
        transforms = self._make_transforms([])
        clips = create_animation_clips(output, transforms)

        assert len(clips) == 1
        assert clips[0].clip_id == "hero_1"  # No palette in clip_id
