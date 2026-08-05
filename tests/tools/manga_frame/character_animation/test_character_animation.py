"""Tests for character animation integration contracts."""

import pytest

from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationInput,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    build_character_animation_bindings,
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
