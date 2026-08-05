"""Tests for manga to frame integration contract."""

from pathlib import Path

import pytest

from tools.manga.models import MangaMetadata, MangaPage, MangaParseResult
from tools.frame.models import Frame, FrameSequence, LayerType
from tools.frame.palette import CharacterColorPalette
from tools.manga_frame import (
    MangaFrameInput,
    MangaFrameOutput,
    convert_manga_to_frames,
    create_frame_sequence_from_manga,
)


class TestMangaFrameInput:
    """Tests for MangaFrameInput contract."""

    def test_valid_input(self) -> None:
        """Test creating valid input contract."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0, file_path=Path("page1.png"))],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
        )
        assert input_contract.sequence_id == "test_seq"
        assert input_contract.total_frames == 1

    def test_input_with_all_options(self) -> None:
        """Test input with all optional parameters."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(title="Test Manga", chapter=1),
            pages=[
                MangaPage(page_number=0, file_path=Path("page1.png")),
                MangaPage(page_number=1, file_path=Path("page2.png")),
            ],
            total_pages=2,
        )
        palette = CharacterColorPalette(
            character_id="hero",
            hair="#FF0000",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
            name="Chapter 1",
            frame_rate=30.0,
            character_palettes={"hero": palette},
        )
        assert input_contract.name == "Chapter 1"
        assert input_contract.frame_rate == 30.0
        assert input_contract.character_palettes is not None
        assert "hero" in input_contract.character_palettes

    def test_get_palette_for_existing_character(self) -> None:
        """Test getting palette for existing character."""
        palette = CharacterColorPalette(
            character_id="hero",
            hair="#FF0000",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        input_contract = MangaFrameInput(
            parse_result=MangaParseResult(metadata=MangaMetadata()),
            sequence_id="test",
            character_palettes={"hero": palette},
        )
        result = input_contract.get_palette_for_character("hero")
        assert result is palette

    def test_get_palette_for_missing_character(self) -> None:
        """Test getting palette for non-existing character returns None."""
        input_contract = MangaFrameInput(
            parse_result=MangaParseResult(metadata=MangaMetadata()),
            sequence_id="test",
            character_palettes={},
        )
        result = input_contract.get_palette_for_character("villain")
        assert result is None


class TestConvertMangaToFrames:
    """Tests for convert_manga_to_frames function."""

    def test_single_page_to_frame(self) -> None:
        """Test converting single manga page to frame."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0, file_path=Path("page1.png"))],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
        )

        output = convert_manga_to_frames(input_contract)

        assert isinstance(output, MangaFrameOutput)
        assert output.pages_converted == 1
        assert isinstance(output.sequence, FrameSequence)

        # Verify frame
        frame = output.sequence.frames[0]
        assert frame.frame_index == 0
        assert frame.source_path == Path("page1.png")
        assert len(frame.layers) == 1
        assert frame.layers[0].layer_type == LayerType.BACKGROUND
        assert frame.layers[0].source_path == Path("page1.png")

    def test_multiple_pages_to_frames(self) -> None:
        """Test converting multiple manga pages to frames."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[
                MangaPage(page_number=0, file_path=Path("page1.png")),
                MangaPage(page_number=1, file_path=Path("page2.png")),
                MangaPage(page_number=2, file_path=Path("page3.png")),
            ],
            total_pages=3,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
        )

        output = convert_manga_to_frames(input_contract)

        assert output.pages_converted == 3
        assert len(output.sequence.frames) == 3

        for i, frame in enumerate(output.sequence.frames):
            assert frame.frame_index == i

    def test_metadata_preserved(self) -> None:
        """Test that manga metadata is preserved."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(title="My Manga", chapter=5),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
        )

        output = convert_manga_to_frames(input_contract)

        assert output.metadata_preserved is True
        assert output.sequence.name == "My Manga - Chapter 5"

    def test_custom_name_overrides_metadata(self) -> None:
        """Test that custom name overrides metadata title."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(title="Original Title", chapter=1),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
            name="Custom Name",
        )

        output = convert_manga_to_frames(input_contract)

        assert output.sequence.name == "Custom Name"

    def test_frame_rate_passed_through(self) -> None:
        """Test that frame rate is passed to sequence."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
            frame_rate=30.0,
        )

        output = convert_manga_to_frames(input_contract)

        assert output.sequence.frame_rate == 30.0

    def test_empty_pages_raises_error(self) -> None:
        """Test that empty pages raise ValueError."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[],
            total_pages=0,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test_seq",
        )

        with pytest.raises(ValueError, match="no pages"):
            convert_manga_to_frames(input_contract)

    def test_palettes_provided_flag(self) -> None:
        """Test that palettes_provided flag is set correctly."""
        # Without palettes
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        output = convert_manga_to_frames(MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test",
        ))
        assert output.palettes_provided is False

        # With palettes
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test",
            character_palettes={"hero": CharacterColorPalette(
                character_id="hero",
                hair="#FF0000",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )},
        )
        output = convert_manga_to_frames(input_contract)
        assert output.palettes_provided is True


class TestCreateFrameSequenceFromManga:
    """Tests for create_frame_sequence_from_manga factory function."""

    def test_basic_conversion(self) -> None:
        """Test basic factory function usage."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[
                MangaPage(page_number=0, file_path=Path("p1.png")),
                MangaPage(page_number=1, file_path=Path("p2.png")),
            ],
            total_pages=2,
        )

        sequence = create_frame_sequence_from_manga(
            parse_result=parse_result,
            sequence_id="factory_test",
            name="Test Sequence",
        )

        assert isinstance(sequence, FrameSequence)
        assert sequence.sequence_id == "factory_test"
        assert sequence.name == "Test Sequence"
        assert len(sequence.frames) == 2


class TestImmutability:
    """Tests for immutability guarantees."""

    def test_output_sequence_is_frozen(self) -> None:
        """Test that output FrameSequence is frozen."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test",
        )

        output = convert_manga_to_frames(input_contract)

        with pytest.raises(Exception):
            output.sequence.sequence_id = "new_id"

    def test_frames_tuple_is_immutable(self) -> None:
        """Test that frames collection is tuple."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[MangaPage(page_number=0)],
            total_pages=1,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="test",
        )

        output = convert_manga_to_frames(input_contract)

        assert isinstance(output.sequence.frames, tuple)


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(title="Deterministic Test"),
            pages=[
                MangaPage(page_number=0, file_path=Path("a.png")),
                MangaPage(page_number=1, file_path=Path("b.png")),
            ],
            total_pages=2,
        )
        input_contract = MangaFrameInput(
            parse_result=parse_result,
            sequence_id="deterministic",
        )

        output1 = convert_manga_to_frames(input_contract)
        output2 = convert_manga_to_frames(input_contract)

        assert output1.sequence == output2.sequence
        assert output1.sequence.model_dump() == output2.sequence.model_dump()


class TestBoundaryViolations:
    """Tests for architecture boundary verification."""

    def test_manga_frame_imports_manga(self) -> None:
        """Verify manga_frame imports from tools.manga."""
        import tools.manga_frame
        source = tools.manga_frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from tools.manga" in content

    def test_manga_frame_imports_frame(self) -> None:
        """Verify manga_frame imports from tools.frame."""
        import tools.manga_frame
        source = tools.manga_frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from tools.frame" in content

    def test_no_forbidden_imports(self) -> None:
        """Verify manga_frame has no forbidden imports."""
        import tools.manga_frame
        source = tools.manga_frame.__file__
        with open(source) as f:
            content = f.read()

        forbidden = [
            "runtime",
            "agents",
            "apps",
            "core",
            "torch", "tensorflow",
            "cv2", "PIL", "opencv",
            "diffusers", "transformers",
            "requests", "httpx",
            "ffmpeg", "moviepy",
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"

    def test_manga_module_does_not_import_frame(self) -> None:
        """Verify tools.manga does NOT import tools.frame."""
        import tools.manga
        source = tools.manga.__file__
        with open(source) as f:
            content = f.read()
        assert "from tools.frame" not in content
        assert "import tools.frame" not in content

    def test_frame_module_does_not_import_manga(self) -> None:
        """Verify tools.frame does NOT import tools.manga."""
        import tools.frame
        source = tools.frame.__file__
        with open(source) as f:
            content = f.read()
        assert "from tools.manga" not in content
        assert "import tools.manga" not in content
