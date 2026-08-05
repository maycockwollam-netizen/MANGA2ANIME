"""Tests for character frame integration contracts."""

import pytest

from tools.frame.models import Frame, FrameLayer, FrameSequence, LayerType
from tools.frame.palette import CharacterColorPalette
from tools.manga_frame.character_frame import (
    CharacterFrameInput,
    CharacterFrameMappingMetadata,
    CharacterFrameOutput,
    CharacterFrameReference,
    convert_character_tracking_to_frames,
)
from tools.manga_frame.character_tracking import (
    CharacterAppearance,
    CharacterTrack,
    CharacterTrackingResult,
    TrackingStatus,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def basic_sequence() -> FrameSequence:
    """Create a basic frame sequence for testing."""
    frames = [
        Frame(
            frame_index=0,
            layers=[
                FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0),
                FrameLayer(layer_id="layer_0", layer_type=LayerType.CHARACTER, layer_index=1),
            ],
        ),
        Frame(
            frame_index=1,
            layers=[
                FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0),
                FrameLayer(layer_id="layer_1", layer_type=LayerType.CHARACTER, layer_index=1),
            ],
        ),
        Frame(
            frame_index=2,
            layers=[
                FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0),
            ],
        ),
    ]
    return FrameSequence(sequence_id="seq_001", frames=tuple(frames))


@pytest.fixture
def basic_tracking() -> CharacterTrackingResult:
    """Create a basic tracking result for testing."""
    tracks = [
        CharacterTrack(
            character_id="naruto",
            appearances=[
                CharacterAppearance(page_number=0, frame_index=0, layer_id="layer_0"),
                CharacterAppearance(page_number=1, frame_index=1, layer_id="layer_1"),
            ],
        ),
        CharacterTrack(
            character_id="sasuke",
            appearances=[
                CharacterAppearance(page_number=0, frame_index=0, layer_id=None),
            ],
        ),
    ]
    return CharacterTrackingResult(
        sequence_id="seq_001",
        tracks=tuple(tracks),
        status=TrackingStatus.SUCCESS,
    )


@pytest.fixture
def basic_palettes() -> dict[str, CharacterColorPalette]:
    """Create basic palettes for testing."""
    return {
        "naruto": CharacterColorPalette(
            character_id="naruto",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        ),
        "sasuke": CharacterColorPalette(
            character_id="sasuke",
            hair="#000000",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#000080",
        ),
    }


# ============================================================================
# Test CharacterFrameMappingMetadata
# ============================================================================


class TestCharacterFrameMappingMetadata:
    """Tests for CharacterFrameMappingMetadata."""

    def test_construction(self) -> None:
        """Test basic construction."""
        metadata = CharacterFrameMappingMetadata(
            characters_mapped=5,
            appearances_mapped=20,
            characters_unmapped=0,
            appearances_unmapped=0,
            palettes_applied=5,
            palettes_missing=0,
        )
        assert metadata.characters_mapped == 5
        assert metadata.appearances_mapped == 20

    def test_metadata_is_frozen(self) -> None:
        """Test that metadata is frozen."""
        metadata = CharacterFrameMappingMetadata(
            characters_mapped=1,
            appearances_mapped=1,
            characters_unmapped=0,
            appearances_unmapped=0,
            palettes_applied=0,
            palettes_missing=0,
        )
        with pytest.raises((TypeError, ValueError)):
            metadata.characters_mapped = 10  # type: ignore[misc]


# ============================================================================
# Test CharacterFrameReference
# ============================================================================


class TestCharacterFrameReference:
    """Tests for CharacterFrameReference."""

    def test_construction(self) -> None:
        """Test basic construction."""
        ref = CharacterFrameReference(
            character_id="char_1",
            frame_index=0,
            layer_index=1,
            palette_id="palette_1",
        )
        assert ref.character_id == "char_1"
        assert ref.frame_index == 0
        assert ref.layer_index == 1
        assert ref.palette_id == "palette_1"

    def test_without_layer(self) -> None:
        """Test construction without layer."""
        ref = CharacterFrameReference(
            character_id="char_1",
            frame_index=0,
            layer_index=None,
            palette_id=None,
        )
        assert ref.layer_index is None
        assert ref.palette_id is None


# ============================================================================
# Test CharacterFrameInput
# ============================================================================


class TestCharacterFrameInput:
    """Tests for CharacterFrameInput."""

    def test_construction(self, basic_sequence: FrameSequence, basic_tracking: CharacterTrackingResult) -> None:
        """Test basic input construction."""
        inp = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )
        assert inp.tracking_result is basic_tracking
        assert inp.frame_sequence is basic_sequence
        assert inp.character_palettes is None

    def test_with_palettes(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
        basic_palettes: dict[str, CharacterColorPalette],
    ) -> None:
        """Test input with palettes."""
        inp = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
            character_palettes=basic_palettes,
        )
        assert inp.character_palettes is not None
        assert "naruto" in inp.character_palettes

    def test_palette_key_normalization(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
        basic_palettes: dict[str, CharacterColorPalette],
    ) -> None:
        """Test that palette keys are normalized."""
        raw_palettes = {"  naruto  ": basic_palettes["naruto"]}
        inp = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
            character_palettes=raw_palettes,
        )
        assert "naruto" in inp.character_palettes
        assert "  naruto  " not in inp.character_palettes


# ============================================================================
# Test convert_character_tracking_to_frames
# ============================================================================


class TestConvertCharacterTrackingToFrames:
    """Tests for the main conversion function."""

    def test_basic_mapping(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
    ) -> None:
        """Test basic character to frame mapping."""
        input_contract = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )
        output = convert_character_tracking_to_frames(input_contract)

        assert output.sequence is basic_sequence
        assert output.tracking_result is basic_tracking
        assert output.metadata.characters_mapped == 2
        assert output.metadata.appearances_mapped == 3

    def test_references_created(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
    ) -> None:
        """Test that correct references are created."""
        input_contract = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )
        output = convert_character_tracking_to_frames(input_contract)

        # Should have 3 references
        assert len(output.references) == 3

        # References should be sorted
        ref_ids = [r.character_id for r in output.references]
        assert ref_ids == sorted(ref_ids)

    def test_layer_index_mapping(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
    ) -> None:
        """Test that layer indices are correctly mapped."""
        input_contract = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )
        output = convert_character_tracking_to_frames(input_contract)

        # Find naruto's reference for frame 0
        naruto_ref = next(
            r for r in output.references
            if r.character_id == "naruto" and r.frame_index == 0
        )
        assert naruto_ref.layer_index == 1  # layer_0 has index 1

    def test_invalid_frame_reference_rejected(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that invalid frame references are rejected."""
        tracks = [
            CharacterTrack(
                character_id="char_1",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=999),  # Invalid!
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
        )

        with pytest.raises(ValueError, match="frame_index 999 not in sequence"):
            convert_character_tracking_to_frames(input_contract)

    def test_invalid_layer_reference_rejected(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that invalid layer references are rejected."""
        tracks = [
            CharacterTrack(
                character_id="char_1",
                appearances=[
                    CharacterAppearance(
                        page_number=0,
                        frame_index=0,
                        layer_id="nonexistent_layer",
                    ),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
        )

        with pytest.raises(ValueError, match="nonexistent_layer"):
            convert_character_tracking_to_frames(input_contract)

    def test_skip_invalid_references(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that invalid references are skipped when configured."""
        tracks = [
            CharacterTrack(
                character_id="char_a",  # Ordered: a before b
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
            CharacterTrack(
                character_id="char_b",  # Ordered: b after a
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=999),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
            skip_invalid_references=True,
        )

        output = convert_character_tracking_to_frames(input_contract)

        assert output.metadata.characters_mapped == 1
        assert output.metadata.characters_unmapped == 1
        assert len(output.references) == 1

    def test_palette_associations(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
        basic_palettes: dict[str, CharacterColorPalette],
    ) -> None:
        """Test that palettes are correctly associated."""
        # Add palette_id to tracks
        tracks = [
            CharacterTrack(
                character_id="naruto",
                palette_id="naruto",  # Reference to palette
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
            character_palettes=basic_palettes,
        )

        output = convert_character_tracking_to_frames(input_contract)

        assert output.metadata.palettes_applied == 1
        assert ("naruto", basic_palettes["naruto"]) in output.palette_associations

    def test_missing_palette_reported(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that missing palettes are reported."""
        tracks = [
            CharacterTrack(
                character_id="orphan",
                palette_id="nonexistent_palette",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
        )

        output = convert_character_tracking_to_frames(input_contract)

        assert output.metadata.palettes_missing == 1
        assert output.metadata.palettes_applied == 0

    def test_deterministic_ordering(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that references are deterministically ordered."""
        tracks = [
            CharacterTrack(
                character_id="char_a",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
            CharacterTrack(
                character_id="char_b",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=1),
                ],
            ),
            CharacterTrack(
                character_id="char_c",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=2),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
        )

        output = convert_character_tracking_to_frames(input_contract)

        # Should be sorted by character_id then frame_index
        assert output.references[0].character_id == "char_a"
        assert output.references[1].character_id == "char_b"
        assert output.references[2].character_id == "char_c"


# ============================================================================
# Test Deep Immutability
# ============================================================================


class TestDeepImmutability:
    """Tests for deep immutability guarantees."""

    def test_references_tuple_immutable(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
    ) -> None:
        """Test that references tuple is immutable."""
        input_contract = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )
        output = convert_character_tracking_to_frames(input_contract)

        with pytest.raises((TypeError, AttributeError)):
            output.references.append(
                CharacterFrameReference(
                    character_id="new",
                    frame_index=0,
                    layer_index=None,
                    palette_id=None,
                )
            )

    def test_palette_associations_immutable(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that palette associations tuple is immutable."""
        tracks = [
            CharacterTrack(
                character_id="char_1",
                palette_id="palette_1",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )
        palettes = {
            "palette_1": CharacterColorPalette(
                character_id="char_1",
                hair="#FF0000",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#000000",
            ),
        }
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
            character_palettes=palettes,
        )
        output = convert_character_tracking_to_frames(input_contract)

        with pytest.raises((TypeError, AttributeError)):
            output.palette_associations = tuple()  # type: ignore[misc]

    def test_metadata_immutable(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that metadata is immutable."""
        from tools.manga_frame.character_frame import CharacterFrameMappingMetadata

        metadata = CharacterFrameMappingMetadata(
            characters_mapped=5,
            appearances_mapped=10,
            characters_unmapped=0,
            appearances_unmapped=0,
            palettes_applied=5,
            palettes_missing=0,
        )

        with pytest.raises((TypeError, ValueError)):
            metadata.characters_mapped = 10  # type: ignore[misc]

    def test_caller_dict_modification_protected(
        self,
        basic_sequence: FrameSequence,
    ) -> None:
        """Test that modifying caller-owned dict doesn't affect result."""
        # Create tracking with palette_id references
        tracks = [
            CharacterTrack(
                character_id="char_1",
                palette_id="palette_1",
                appearances=[
                    CharacterAppearance(page_number=0, frame_index=0),
                ],
            ),
        ]
        tracking = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tuple(tracks),
        )

        palettes = {
            "palette_1": CharacterColorPalette(
                character_id="char_1",
                hair="#FF0000",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#000000",
            ),
        }

        original_dict = dict(palettes)
        input_contract = CharacterFrameInput(
            tracking_result=tracking,
            frame_sequence=basic_sequence,
            character_palettes=original_dict,
        )

        # Modify original
        original_dict["new_palette"] = CharacterColorPalette(
            character_id="new_char",
            hair="#FF0000",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#000000",
        )

        output = convert_character_tracking_to_frames(input_contract)

        # Should not contain new_palette
        palette_ids = [pid for _, p in output.palette_associations for pid in [p.character_id]]
        assert "new_char" not in palette_ids


# ============================================================================
# Test Serialization
# ============================================================================


class TestSerialization:
    """Tests for serialization behavior."""

    def test_metadata_serialization(self) -> None:
        """Test metadata serialization."""
        metadata = CharacterFrameMappingMetadata(
            characters_mapped=5,
            appearances_mapped=20,
            characters_unmapped=0,
            appearances_unmapped=0,
            palettes_applied=5,
            palettes_missing=0,
        )
        data = metadata.model_dump()
        assert data["characters_mapped"] == 5

    def test_reference_dataclass(self) -> None:
        """Test reference dataclass."""
        ref = CharacterFrameReference(
            character_id="char_1",
            frame_index=0,
            layer_index=1,
            palette_id=None,
        )
        # Dataclass should be hashable and comparable
        ref2 = CharacterFrameReference(
            character_id="char_1",
            frame_index=0,
            layer_index=1,
            palette_id=None,
        )
        assert ref == ref2


# ============================================================================
# Test Determinism
# ============================================================================


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(
        self,
        basic_sequence: FrameSequence,
        basic_tracking: CharacterTrackingResult,
    ) -> None:
        """Test that same input produces same output."""
        input_contract = CharacterFrameInput(
            tracking_result=basic_tracking,
            frame_sequence=basic_sequence,
        )

        output1 = convert_character_tracking_to_frames(input_contract)
        output2 = convert_character_tracking_to_frames(input_contract)

        assert output1.references == output2.references
        assert output1.metadata == output2.metadata


# ============================================================================
# Test Dependency Boundary
# ============================================================================


class TestDependencyBoundary:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify no forbidden imports in character_frame."""
        import tools.manga_frame.character_frame as module
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

    def test_allowed_imports(self) -> None:
        """Verify expected allowed imports."""
        import tools.manga_frame.character_frame as module
        source_file = module.__file__

        with open(source_file) as f:
            content = f.read()

        # Should import from character_tracking and frame
        assert "from tools.manga_frame.character_tracking import" in content
        assert "from tools.frame.models import" in content

    def test_module_importable(self) -> None:
        """Verify character_frame can be imported."""
        from tools.manga_frame.character_frame import (
            CharacterFrameInput,
            convert_character_tracking_to_frames,
        )
        assert CharacterFrameInput is not None
        assert CharacterFrameOutput is not None
        assert convert_character_tracking_to_frames is not None
