"""Tests for character tracking contracts."""

import pytest

from tools.manga_frame.character_tracking import (
    CharacterAppearance,
    CharacterTrack,
    CharacterTrackingInput,
    CharacterTrackingResult,
    CharacterTrackMetadata,
    TrackingConfig,
    TrackingStatus,
)


class TestTrackingStatus:
    """Tests for TrackingStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all expected statuses are defined."""
        assert TrackingStatus.NOT_PROCESSED == "not_processed"
        assert TrackingStatus.SUCCESS == "success"
        assert TrackingStatus.PARTIAL == "partial"
        assert TrackingStatus.FAILED == "failed"

    def test_is_str_enum(self) -> None:
        """Test that TrackingStatus is a string enum."""
        assert isinstance(TrackingStatus.SUCCESS, str)
        assert TrackingStatus.SUCCESS == "success"


class TestCharacterTrackMetadata:
    """Tests for CharacterTrackMetadata model."""

    def test_basic_construction(self) -> None:
        """Test basic metadata construction."""
        metadata = CharacterTrackMetadata()
        assert metadata.total_characters is None
        assert metadata.total_appearances is None
        assert metadata.extra == ()

    def test_with_values(self) -> None:
        """Test metadata with values."""
        metadata = CharacterTrackMetadata(
            total_characters=5,
            total_appearances=20,
        )
        assert metadata.total_characters == 5
        assert metadata.total_appearances == 20

    def test_metadata_is_frozen(self) -> None:
        """Test that metadata is frozen."""
        metadata = CharacterTrackMetadata()
        with pytest.raises((TypeError, ValueError)):
            metadata.total_characters = 10  # type: ignore[misc]


class TestCharacterAppearance:
    """Tests for CharacterAppearance model."""

    def test_basic_construction(self) -> None:
        """Test basic appearance construction."""
        appearance = CharacterAppearance(
            page_number=0,
            frame_index=0,
        )
        assert appearance.page_number == 0
        assert appearance.frame_index == 0
        assert appearance.layer_id is None
        assert appearance.region_bounds is None

    def test_full_construction(self) -> None:
        """Test appearance with all fields."""
        appearance = CharacterAppearance(
            page_number=1,
            frame_index=2,
            layer_id="layer_1",
            region_bounds=(10, 20, 100, 150),
            confidence=0.95,
        )
        assert appearance.page_number == 1
        assert appearance.frame_index == 2
        assert appearance.layer_id == "layer_1"
        assert appearance.region_bounds == (10, 20, 100, 150)
        assert appearance.confidence == 0.95

    def test_negative_page_number_rejected(self) -> None:
        """Test that negative page_number is rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            CharacterAppearance(page_number=-1, frame_index=0)

    def test_negative_frame_index_rejected(self) -> None:
        """Test that negative frame_index is rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            CharacterAppearance(page_number=0, frame_index=-1)

    def test_empty_layer_id_rejected(self) -> None:
        """Test that empty layer_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
            CharacterAppearance(page_number=0, frame_index=0, layer_id="")

    def test_whitespace_layer_id_rejected(self) -> None:
        """Test that whitespace layer_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
            CharacterAppearance(page_number=0, frame_index=0, layer_id="   ")

    def test_layer_id_normalized(self) -> None:
        """Test that layer_id is normalized."""
        appearance = CharacterAppearance(
            page_number=0,
            frame_index=0,
            layer_id="  layer_1  ",
        )
        assert appearance.layer_id == "layer_1"

    def test_invalid_confidence_rejected(self) -> None:
        """Test that invalid confidence is rejected."""
        with pytest.raises(ValueError):
            CharacterAppearance(page_number=0, frame_index=0, confidence=1.5)

        with pytest.raises(ValueError):
            CharacterAppearance(page_number=0, frame_index=0, confidence=-0.1)

    def test_invalid_region_bounds_rejected(self) -> None:
        """Test that invalid region bounds are rejected."""
        # Wrong number of values
        with pytest.raises(ValueError, match="exactly 4 values"):
            CharacterAppearance(page_number=0, frame_index=0, region_bounds=(1, 2, 3))

        # Negative width/height
        with pytest.raises(ValueError, match="non-negative"):
            CharacterAppearance(
                page_number=0,
                frame_index=0,
                region_bounds=(0, 0, -1, 100),
            )


class TestCharacterTrack:
    """Tests for CharacterTrack model."""

    def test_basic_construction(self) -> None:
        """Test basic track construction."""
        track = CharacterTrack(character_id="char_1")
        assert track.character_id == "char_1"
        assert track.display_name is None
        assert track.appearances == ()
        assert track.palette_id is None

    def test_with_appearances(self) -> None:
        """Test track with appearances."""
        appearances = (
            CharacterAppearance(page_number=0, frame_index=0),
            CharacterAppearance(page_number=1, frame_index=1),
        )
        track = CharacterTrack(
            character_id="naruto",
            display_name="Naruto Uzumaki",
            appearances=appearances,
        )
        assert track.character_id == "naruto"
        assert track.display_name == "Naruto Uzumaki"
        assert len(track.appearances) == 2

    def test_appearances_is_tuple(self) -> None:
        """Test that appearances is stored as tuple."""
        appearances = [CharacterAppearance(page_number=0, frame_index=0)]
        track = CharacterTrack(
            character_id="char_1",
            appearances=appearances,
        )
        assert isinstance(track.appearances, tuple)

    def test_empty_character_id_rejected(self) -> None:
        """Test that empty character_id is rejected."""
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            CharacterTrack(character_id="")

    def test_whitespace_character_id_rejected(self) -> None:
        """Test that whitespace character_id is rejected."""
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            CharacterTrack(character_id="   ")

    def test_appearance_ordering_validated(self) -> None:
        """Test that appearances are ordered by page_number."""
        appearances = (
            CharacterAppearance(page_number=2, frame_index=0),
            CharacterAppearance(page_number=1, frame_index=0),
        )
        with pytest.raises(ValueError, match="ordered by page_number"):
            CharacterTrack(character_id="char_1", appearances=appearances)

    def test_duplicate_appearance_rejected(self) -> None:
        """Test that duplicate (page, frame) pairs are rejected."""
        appearances = (
            CharacterAppearance(page_number=1, frame_index=1),
            CharacterAppearance(page_number=1, frame_index=1),
        )
        with pytest.raises(ValueError, match="duplicate.*pairs"):
            CharacterTrack(character_id="char_1", appearances=appearances)

    def test_track_is_mutable(self) -> None:
        """Test that CharacterTrack is mutable (by design)."""
        track = CharacterTrack(character_id="char_1")
        track.display_name = "Character One"  # Should not raise
        assert track.display_name == "Character One"

    def test_appearance_count_property(self) -> None:
        """Test appearance_count property."""
        appearances = (
            CharacterAppearance(page_number=0, frame_index=0),
            CharacterAppearance(page_number=1, frame_index=1),
            CharacterAppearance(page_number=2, frame_index=2),
        )
        track = CharacterTrack(
            character_id="char_1",
            appearances=appearances,
        )
        assert track.appearance_count == 3

    def test_get_appearances_on_page(self) -> None:
        """Test get_appearances_on_page method."""
        appearances = (
            CharacterAppearance(page_number=0, frame_index=0),
            CharacterAppearance(page_number=1, frame_index=1),
            CharacterAppearance(page_number=1, frame_index=2),
        )
        track = CharacterTrack(
            character_id="char_1",
            appearances=appearances,
        )
        page_1_apps = track.get_appearances_on_page(1)
        assert len(page_1_apps) == 2


class TestTrackingConfig:
    """Tests for TrackingConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TrackingConfig()
        assert config.min_confidence == 0.5
        assert config.track_across_pages is True
        assert config.merge_threshold is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = TrackingConfig(
            min_confidence=0.8,
            track_across_pages=False,
            merge_threshold=0.9,
        )
        assert config.min_confidence == 0.8
        assert config.track_across_pages is False
        assert config.merge_threshold == 0.9

    def test_config_is_mutable(self) -> None:
        """Test that config is mutable."""
        config = TrackingConfig()
        config.min_confidence = 0.9
        assert config.min_confidence == 0.9


class TestCharacterTrackingInput:
    """Tests for CharacterTrackingInput model."""

    def test_basic_construction(self) -> None:
        """Test basic input construction."""
        inp = CharacterTrackingInput(
            sequence_id="seq_001",
            frame_count=10,
            page_count=10,
        )
        assert inp.sequence_id == "seq_001"
        assert inp.frame_count == 10
        assert inp.page_count == 10
        assert inp.config is None

    def test_with_config(self) -> None:
        """Test input with tracking config."""
        config = TrackingConfig(min_confidence=0.7)
        inp = CharacterTrackingInput(
            sequence_id="seq_002",
            frame_count=20,
            page_count=20,
            config=config,
        )
        assert inp.config is not None
        assert inp.config.min_confidence == 0.7

    def test_empty_sequence_id_rejected(self) -> None:
        """Test that empty sequence_id is rejected."""
        with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
            CharacterTrackingInput(
                sequence_id="",
                frame_count=10,
                page_count=10,
            )

    def test_negative_frame_count_rejected(self) -> None:
        """Test that negative frame_count is rejected."""
        with pytest.raises(ValueError):
            CharacterTrackingInput(
                sequence_id="seq_001",
                frame_count=-1,
                page_count=10,
            )

    def test_input_is_mutable(self) -> None:
        """Test that input is mutable."""
        inp = CharacterTrackingInput(
            sequence_id="seq_001",
            frame_count=10,
            page_count=10,
        )
        inp.frame_count = 20
        assert inp.frame_count == 20


class TestCharacterTrackingResult:
    """Tests for CharacterTrackingResult model."""

    def test_basic_construction(self) -> None:
        """Test basic result construction."""
        result = CharacterTrackingResult(sequence_id="seq_001")
        assert result.sequence_id == "seq_001"
        assert result.tracks == ()
        assert result.status == TrackingStatus.NOT_PROCESSED

    def test_with_tracks(self) -> None:
        """Test result with tracks."""
        tracks = (
            CharacterTrack(character_id="char_1"),
            CharacterTrack(character_id="char_2"),
        )
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tracks,
            status=TrackingStatus.SUCCESS,
        )
        assert len(result.tracks) == 2
        assert result.status == TrackingStatus.SUCCESS

    def test_tracks_is_tuple(self) -> None:
        """Test that tracks is stored as tuple."""
        tracks = [CharacterTrack(character_id="char_1")]
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tracks,
        )
        assert isinstance(result.tracks, tuple)

    def test_track_ordering_validated(self) -> None:
        """Test that tracks are ordered by character_id."""
        tracks = (
            CharacterTrack(character_id="char_2"),
            CharacterTrack(character_id="char_1"),
        )
        with pytest.raises(ValueError, match="ordered by character_id"):
            CharacterTrackingResult(
                sequence_id="seq_001",
                tracks=tracks,
            )

    def test_duplicate_character_id_rejected(self) -> None:
        """Test that duplicate character_id values are rejected."""
        tracks = (
            CharacterTrack(character_id="char_1"),
            CharacterTrack(character_id="char_1"),
        )
        with pytest.raises(ValueError, match="duplicate character_id"):
            CharacterTrackingResult(
                sequence_id="seq_001",
                tracks=tracks,
            )

    def test_result_is_frozen(self) -> None:
        """Test that result is frozen."""
        result = CharacterTrackingResult(sequence_id="seq_001")
        with pytest.raises((TypeError, ValueError)):
            result.sequence_id = "new_id"  # type: ignore[misc]

    def test_track_count_property(self) -> None:
        """Test track_count property."""
        tracks = (
            CharacterTrack(character_id="char_1"),
            CharacterTrack(character_id="char_2"),
        )
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tracks,
        )
        assert result.track_count == 2

    def test_get_track(self) -> None:
        """Test get_track method."""
        tracks = (
            CharacterTrack(character_id="char_1"),
            CharacterTrack(character_id="char_2"),
        )
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tracks,
        )
        track = result.get_track("char_1")
        assert track is not None
        assert track.character_id == "char_1"

        missing = result.get_track("char_99")
        assert missing is None

    def test_get_tracks_with_palette(self) -> None:
        """Test get_tracks_with_palette method."""
        tracks = (
            CharacterTrack(character_id="char_1", palette_id="palette_a"),
            CharacterTrack(character_id="char_2", palette_id="palette_b"),
            CharacterTrack(character_id="char_3", palette_id="palette_a"),
        )
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=tracks,
        )
        palette_a_tracks = result.get_tracks_with_palette("palette_a")
        assert len(palette_a_tracks) == 2


class TestDeepImmutability:
    """Tests for deep immutability guarantees."""

    def test_tracks_tuple_cannot_append(self) -> None:
        """Test that tracks tuple cannot be appended to."""
        result = CharacterTrackingResult(sequence_id="seq_001")
        with pytest.raises(AttributeError):
            result.tracks.append(CharacterTrack(character_id="new"))

    def test_caller_list_modification_protected(self) -> None:
        """Test that modifying caller-owned list doesn't affect result."""
        original_tracks = [CharacterTrack(character_id="char_1")]
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=original_tracks,
        )

        # Modify original list
        original_tracks.append(CharacterTrack(character_id="char_2"))

        # Result should be unaffected
        assert len(result.tracks) == 1

    def test_appearances_tuple_cannot_append(self) -> None:
        """Test that appearances tuple cannot be appended to."""
        track = CharacterTrack(character_id="char_1")
        with pytest.raises(AttributeError):
            track.appearances.append(
                CharacterAppearance(page_number=0, frame_index=0)
            )

    def test_metadata_is_frozen(self) -> None:
        """Test that nested metadata is frozen."""
        metadata = CharacterTrackMetadata(total_characters=5)
        with pytest.raises((TypeError, ValueError)):
            metadata.total_characters = 10  # type: ignore[misc]


class TestSerialization:
    """Tests for serialization behavior."""

    def test_track_serialization(self) -> None:
        """Test CharacterTrack serialization."""
        track = CharacterTrack(character_id="test_char")
        data = track.model_dump()
        assert data["character_id"] == "test_char"

    def test_result_serialization(self) -> None:
        """Test CharacterTrackingResult serialization."""
        result = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=[CharacterTrack(character_id="char_1")],
        )
        data = result.model_dump()
        assert data["sequence_id"] == "seq_001"
        assert isinstance(data["tracks"], (list, tuple))

    def test_serialization_roundtrip(self) -> None:
        """Test that serialization roundtrip preserves equality."""
        original = CharacterTrackingResult(
            sequence_id="seq_001",
            tracks=[
                CharacterTrack(character_id="char_1"),
                CharacterTrack(character_id="char_2"),
            ],
            status=TrackingStatus.SUCCESS,
        )

        # Roundtrip
        data = original.model_dump()
        reconstructed = CharacterTrackingResult(**data)

        assert reconstructed == original


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        input1 = CharacterTrackingInput(
            sequence_id="seq_001",
            frame_count=10,
            page_count=10,
        )
        input2 = CharacterTrackingInput(
            sequence_id="seq_001",
            frame_count=10,
            page_count=10,
        )

        # Create equivalent results
        result1 = CharacterTrackingResult(sequence_id=input1.sequence_id)
        result2 = CharacterTrackingResult(sequence_id=input2.sequence_id)

        assert result1 == result2
        assert result1.model_dump() == result2.model_dump()


class TestDependencyBoundary:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify no forbidden imports in character_tracking."""
        import tools.manga_frame.character_tracking as module
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
        import tools.manga_frame.character_tracking as module
        source_file = module.__file__

        with open(source_file) as f:
            content = f.read()

        # Should have pydantic
        assert "from pydantic" in content

    def test_character_tracking_module_importable(self) -> None:
        """Verify character_tracking can be imported."""
        from tools.manga_frame.character_tracking import (
            CharacterTrack,
            CharacterTrackingResult,
            TrackingStatus,
        )
        assert TrackingStatus is not None
        assert CharacterTrack is not None
        assert CharacterTrackingResult is not None
