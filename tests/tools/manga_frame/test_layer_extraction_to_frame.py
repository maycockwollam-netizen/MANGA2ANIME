"""Tests for layer extraction to frame integration."""

from pathlib import Path

import pytest

from tools.frame.models import FrameSequence, LayerType
from tools.manga_frame.layer_extraction import (
    LayerCategory,
    LayerDescriptor,
    LayerExtractionResult,
)
from tools.manga_frame.layer_extraction_to_frame import (
    LayerExtractionToFrameInput,
    LayerExtractionToFrameMetadata,
    LayerExtractionToFrameOutput,
    UnknownLayerCategoryError,
    convert_layer_extraction_to_frames,
    create_frame_sequence_from_layer_extraction,
)


class TestBasicConversion:
    """Tests for basic conversion functionality."""

    def test_single_layer_conversion(self) -> None:
        """Test converting a single layer."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert isinstance(output, LayerExtractionToFrameOutput)
        assert isinstance(output.sequence, FrameSequence)
        assert output.sequence.sequence_id == "test_seq"
        assert len(output.sequence.frames) == 1
        assert len(output.sequence.frames[0].layers) == 1

    def test_multiple_layers_conversion(self) -> None:
        """Test converting multiple layers."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
                LayerDescriptor(
                    layer_id="char",
                    category=LayerCategory.CHARACTER,
                    layer_index=1,
                ),
                LayerDescriptor(
                    layer_id="fg",
                    category=LayerCategory.FOREGROUND,
                    layer_index=2,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert len(output.sequence.frames) == 1
        assert len(output.sequence.frames[0].layers) == 3


class TestIdentityPreservation:
    """Tests for identity field preservation."""

    def test_layer_id_preserved(self) -> None:
        """Test that layer_id is preserved."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="my_layer",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_id == "my_layer"

    def test_layer_index_preserved(self) -> None:
        """Test that layer_index is preserved."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="layer_1",
                    category=LayerCategory.BACKGROUND,
                    layer_index=5,
                ),
                LayerDescriptor(
                    layer_id="layer_2",
                    category=LayerCategory.CHARACTER,
                    layer_index=10,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_index == 5
        assert output.sequence.frames[0].layers[1].layer_index == 10

    def test_source_path_preserved(self) -> None:
        """Test that source_path is preserved."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="layer",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                    source_path=Path("/layers/layer1.png"),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].source_path == Path("/manga/page1.png")
        assert output.sequence.frames[0].layers[0].source_path == Path("/layers/layer1.png")

    def test_page_number_to_frame_index_mapping(self) -> None:
        """Test that page_number maps to frame_index."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=5,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=10,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # Frames should be sorted by frame_index
        frame_indices = [f.frame_index for f in output.sequence.frames]
        assert frame_indices == [5, 10]


class TestCategoryMapping:
    """Tests for LayerCategory to LayerType mapping."""

    def test_background_mapping(self) -> None:
        """Test BACKGROUND category maps to BACKGROUND type."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_type == LayerType.BACKGROUND

    def test_character_mapping(self) -> None:
        """Test CHARACTER category maps to CHARACTER type."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="char",
                    category=LayerCategory.CHARACTER,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_type == LayerType.CHARACTER

    def test_foreground_mapping(self) -> None:
        """Test FOREGROUND category maps to FOREGROUND type."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="fg",
                    category=LayerCategory.FOREGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_type == LayerType.FOREGROUND

    def test_effect_mapping(self) -> None:
        """Test EFFECT category maps to EFFECT type."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="effect",
                    category=LayerCategory.EFFECT,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.sequence.frames[0].layers[0].layer_type == LayerType.EFFECT


class TestUnknownCategory:
    """Tests for UNKNOWN category handling."""

    def test_unknown_raises_error_by_default(self) -> None:
        """Test that UNKNOWN category raises error by default."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="unknown_layer",
                    category=LayerCategory.UNKNOWN,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
            skip_unknown_categories=False,  # Default
        )

        with pytest.raises(UnknownLayerCategoryError) as exc_info:
            convert_layer_extraction_to_frames(input_contract)

        assert "unknown_layer" in str(exc_info.value)
        assert exc_info.value.layer_id == "unknown_layer"

    def test_unknown_skipped_when_enabled(self) -> None:
        """Test that UNKNOWN category is skipped when skip_unknown_categories=True."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="unknown_layer",
                    category=LayerCategory.UNKNOWN,
                    layer_index=0,
                ),
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=1,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
            skip_unknown_categories=True,
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # Should have only the BACKGROUND layer
        assert len(output.sequence.frames[0].layers) == 1
        assert output.sequence.frames[0].layers[0].layer_id == "bg"

        # Metadata should reflect the skip
        assert output.metadata.layers_filtered == 1
        assert output.skipped_layers == ("unknown_layer",)

    def test_multiple_unknown_layers(self) -> None:
        """Test skipping multiple UNKNOWN layers."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="u1", category=LayerCategory.UNKNOWN, layer_index=0),
                LayerDescriptor(layer_id="bg", category=LayerCategory.BACKGROUND, layer_index=1),
                LayerDescriptor(layer_id="u2", category=LayerCategory.UNKNOWN, layer_index=2),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
            skip_unknown_categories=True,
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert len(output.sequence.frames[0].layers) == 1
        assert output.metadata.layers_filtered == 2
        assert "u1" in output.skipped_layers
        assert "u2" in output.skipped_layers

    def test_all_unknown_layers_produces_empty_frame(self) -> None:
        """Test that skipping all UNKNOWN layers produces an empty frame.

        Empty frames are valid according to the Frame model contract.
        This documents the expected behavior when all layers in a result are UNKNOWN.
        """
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="u1", category=LayerCategory.UNKNOWN, layer_index=0),
                LayerDescriptor(layer_id="u2", category=LayerCategory.UNKNOWN, layer_index=1),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
            skip_unknown_categories=True,
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # Frame should exist with empty layers
        assert len(output.sequence.frames) == 1
        assert len(output.sequence.frames[0].layers) == 0

        # Metadata should accurately reflect the situation
        assert output.metadata.layers_converted == 0
        assert output.metadata.layers_filtered == 2
        assert output.skipped_layers == ("u1", "u2")

        # Source path should still be preserved
        assert output.sequence.frames[0].source_path == Path("/manga/page1.png")


class TestOrdering:
    """Tests for layer ordering."""

    def test_deterministic_layer_ordering(self) -> None:
        """Test that layer ordering is deterministic."""
        # Layers must be provided in order (LayerExtractionResult validates this)
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="b", category=LayerCategory.BACKGROUND, layer_index=0),
                LayerDescriptor(layer_id="a", category=LayerCategory.EFFECT, layer_index=1),
                LayerDescriptor(layer_id="c", category=LayerCategory.CHARACTER, layer_index=2),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        # Convert twice
        output1 = convert_layer_extraction_to_frames(input_contract)
        output2 = convert_layer_extraction_to_frames(input_contract)

        # Results should be equal
        assert output1 == output2
        assert output1.sequence == output2.sequence

    def test_non_sequential_layer_index(self) -> None:
        """Test that non-sequential layer indices are preserved."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="bg", category=LayerCategory.BACKGROUND, layer_index=0),
                LayerDescriptor(layer_id="char", category=LayerCategory.CHARACTER, layer_index=5),
                LayerDescriptor(layer_id="fg", category=LayerCategory.FOREGROUND, layer_index=10),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        indices = [layer.layer_index for layer in output.sequence.frames[0].layers]
        assert indices == [0, 5, 10]


class TestValidation:
    """Tests for input validation."""

    def test_empty_extraction_results_rejected(self) -> None:
        """Test that empty extraction_results is rejected."""
        input_contract = LayerExtractionToFrameInput(
            extraction_results=(),
            sequence_id="test_seq",
        )

        with pytest.raises(ValueError, match="empty extraction_results"):
            convert_layer_extraction_to_frames(input_contract)

    def test_empty_sequence_id_rejected(self) -> None:
        """Test that empty sequence_id is rejected."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(),
        )

        # Whitespace-only sequence_id should fail during input validation
        with pytest.raises(Exception, match="sequence_id cannot be empty"):
            LayerExtractionToFrameInput(
                extraction_results=(result,),
                sequence_id="   ",  # Whitespace only
            )

    def test_negative_layer_index_in_input(self) -> None:
        """Test that negative layer_index in input is rejected."""
        # This tests that LayerDescriptor validation works
        with pytest.raises(ValueError, match="layer_index cannot be negative"):
            LayerDescriptor(
                layer_id="layer",
                category=LayerCategory.BACKGROUND,
                layer_index=-1,
            )

    def test_duplicate_layer_index_in_input(self) -> None:
        """Test that duplicate layer_index in input is rejected."""
        # This tests that LayerExtractionResult validation works
        with pytest.raises(ValueError, match="duplicate layer_index"):
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(layer_id="l1", category=LayerCategory.BACKGROUND, layer_index=1),
                    LayerDescriptor(layer_id="l2", category=LayerCategory.CHARACTER, layer_index=1),
                ),
            )

    def test_duplicate_page_number_rejected(self) -> None:
        """Test that duplicate page_number values are rejected."""
        from tools.manga_frame.layer_extraction_to_frame import DuplicatePageNumberError

        # Two results with same page_number
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=5,
                layers=(
                    LayerDescriptor(
                        layer_id="layer",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=5,  # Same as first!
                layers=(
                    LayerDescriptor(
                        layer_id="layer",
                        category=LayerCategory.CHARACTER,
                        layer_index=0,
                    ),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        with pytest.raises(DuplicatePageNumberError, match=r"\[5\]"):
            convert_layer_extraction_to_frames(input_contract)

    def test_multiple_duplicate_page_numbers_rejected(self) -> None:
        """Test that multiple duplicate page_numbers are all detected."""
        from tools.manga_frame.layer_extraction_to_frame import DuplicatePageNumberError

        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=1,
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=2,
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page3.png"),
                page_number=1,  # Duplicate of first
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page4.png"),
                page_number=2,  # Duplicate of second
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        with pytest.raises(DuplicatePageNumberError) as exc_info:
            convert_layer_extraction_to_frames(input_contract)

        # Both duplicates should be reported
        error = exc_info.value
        assert 1 in error.duplicated_pages
        assert 2 in error.duplicated_pages

    def test_unique_page_numbers_succeed(self) -> None:
        """Test that unique page_numbers still convert successfully."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(
                        layer_id="layer",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=1,
                layers=(
                    LayerDescriptor(
                        layer_id="layer",
                        category=LayerCategory.CHARACTER,
                        layer_index=0,
                    ),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)
        assert len(output.sequence.frames) == 2
        assert output.sequence.frames[0].frame_index == 0
        assert output.sequence.frames[1].frame_index == 1


class TestImmutability:
    """Tests for immutability guarantees."""

    def test_input_not_mutated(self) -> None:
        """Test that input LayerExtractionResult is not mutated."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        # Store original state
        original_layer_id = result.layers[0].layer_id

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        # Convert
        convert_layer_extraction_to_frames(input_contract)

        # Verify input unchanged
        assert result.layers[0].layer_id == original_layer_id

    def test_output_is_frozen(self) -> None:
        """Test that output FrameSequence is frozen."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # FrameSequence should be frozen
        with pytest.raises((TypeError, ValueError)):
            output.sequence.sequence_id = "new_id"  # type: ignore[misc]

    def test_input_unchanged_after_failed_validation(self) -> None:
        """Test that inputs are not modified when validation fails."""
        from tools.manga_frame.layer_extraction_to_frame import DuplicatePageNumberError

        # Create a list of results that will fail validation
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=5,
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=5,  # Duplicate!
                layers=(
                    LayerDescriptor(
                        layer_id="l",
                        category=LayerCategory.CHARACTER,
                        layer_index=0,
                    ),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        # Attempt conversion - should fail
        with pytest.raises(DuplicatePageNumberError):
            convert_layer_extraction_to_frames(input_contract)

        # Verify original results are unchanged
        assert input_contract.extraction_results[0].page_number == 5
        assert input_contract.extraction_results[1].page_number == 5
        assert len(input_contract.extraction_results) == 2


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(
                        layer_id="bg",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=1,
                layers=(
                    LayerDescriptor(
                        layer_id="char",
                        category=LayerCategory.CHARACTER,
                        layer_index=0,
                    ),
                ),
            ),
        )

        input_contract1 = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        input_contract2 = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        output1 = convert_layer_extraction_to_frames(input_contract1)
        output2 = convert_layer_extraction_to_frames(input_contract2)

        assert output1 == output2
        assert output1.sequence == output2.sequence
        assert output1.metadata == output2.metadata


class TestSerialization:
    """Tests for serialization."""

    def test_frame_sequence_serialization(self) -> None:
        """Test that output FrameSequence can be serialized."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # Serialize
        data = output.sequence.model_dump()

        # Deserialize
        reconstructed = FrameSequence(**data)

        assert reconstructed == output.sequence

    def test_metadata_serialization(self) -> None:
        """Test that output metadata can be serialized."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(
                    layer_id="bg",
                    category=LayerCategory.BACKGROUND,
                    layer_index=0,
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        # Serialize
        data = output.metadata.model_dump()

        # Deserialize
        reconstructed = LayerExtractionToFrameMetadata(**data)

        assert reconstructed == output.metadata


class TestFactoryFunction:
    """Tests for factory function."""

    def test_factory_with_list_input(self) -> None:
        """Test factory function accepts list input."""
        results = [
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(
                        layer_id="bg",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
        ]

        sequence = create_frame_sequence_from_layer_extraction(
            extraction_results=results,
            sequence_id="test_seq",
        )

        assert isinstance(sequence, FrameSequence)
        assert sequence.sequence_id == "test_seq"

    def test_factory_with_tuple_input(self) -> None:
        """Test factory function accepts tuple input."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(
                        layer_id="bg",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
        )

        sequence = create_frame_sequence_from_layer_extraction(
            extraction_results=results,
            sequence_id="test_seq",
        )

        assert isinstance(sequence, FrameSequence)
        assert sequence.sequence_id == "test_seq"

    def test_factory_all_options(self) -> None:
        """Test factory function with all optional parameters."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(
                        layer_id="bg",
                        category=LayerCategory.BACKGROUND,
                        layer_index=0,
                    ),
                ),
            ),
        )

        sequence = create_frame_sequence_from_layer_extraction(
            extraction_results=results,
            sequence_id="test_seq",
            name="Test Sequence",
            frame_rate=30.0,
        )

        assert sequence.sequence_id == "test_seq"
        assert sequence.name == "Test Sequence"
        assert sequence.frame_rate == 30.0


class TestOutputMetadata:
    """Tests for output metadata."""

    def test_metadata_pages_converted(self) -> None:
        """Test that metadata correctly counts converted pages."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=1,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.metadata.pages_converted == 2

    def test_metadata_layers_converted(self) -> None:
        """Test that metadata correctly counts converted layers."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="l1", category=LayerCategory.BACKGROUND, layer_index=0),
                LayerDescriptor(layer_id="l2", category=LayerCategory.CHARACTER, layer_index=1),
                LayerDescriptor(layer_id="l3", category=LayerCategory.FOREGROUND, layer_index=2),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.metadata.layers_converted == 3

    def test_metadata_layers_filtered(self) -> None:
        """Test that metadata correctly counts filtered layers."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="u1", category=LayerCategory.UNKNOWN, layer_index=0),
                LayerDescriptor(layer_id="bg", category=LayerCategory.BACKGROUND, layer_index=1),
                LayerDescriptor(layer_id="u2", category=LayerCategory.UNKNOWN, layer_index=2),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
            skip_unknown_categories=True,
        )

        output = convert_layer_extraction_to_frames(input_contract)

        assert output.metadata.layers_filtered == 2
        assert output.metadata.layers_converted == 1


class TestFrameOrdering:
    """Tests for frame ordering."""

    def test_frames_sorted_by_index(self) -> None:
        """Test that frames are sorted by frame_index."""
        results = (
            LayerExtractionResult(
                source_path=Path("/manga/page3.png"),
                page_number=2,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page1.png"),
                page_number=0,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
            LayerExtractionResult(
                source_path=Path("/manga/page2.png"),
                page_number=1,
                layers=(
                    LayerDescriptor(layer_id="l", category=LayerCategory.BACKGROUND, layer_index=0),
                ),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=results,
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        frame_indices = [f.frame_index for f in output.sequence.frames]
        assert frame_indices == [0, 1, 2]


class TestVisibleLayer:
    """Tests for layer visibility."""

    def test_all_layers_visible(self) -> None:
        """Test that all converted layers are visible by default."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=(
                LayerDescriptor(layer_id="bg", category=LayerCategory.BACKGROUND, layer_index=0),
                LayerDescriptor(layer_id="char", category=LayerCategory.CHARACTER, layer_index=1),
            ),
        )

        input_contract = LayerExtractionToFrameInput(
            extraction_results=(result,),
            sequence_id="test_seq",
        )

        output = convert_layer_extraction_to_frames(input_contract)

        for layer in output.sequence.frames[0].layers:
            assert layer.visible is True
