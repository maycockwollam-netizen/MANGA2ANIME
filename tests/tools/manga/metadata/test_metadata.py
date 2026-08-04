"""Tests for manga metadata."""


from tools.manga import MangaMetadata
from tools.manga.metadata import (
    MangaMetadataProcessor,
    MetadataResult,
    process,
)


class TestBasicProcessing:
    """Tests for basic metadata processing."""

    def test_valid_metadata(self) -> None:
        """Test processing valid metadata."""
        metadata = MangaMetadata(
            title="One Piece",
            author="Eiichiro Oda",
            chapter=1,
            chapter_title="Romance Dawn",
            source="local",
        )

        result = process(metadata)

        assert result.valid is True
        assert len(result.validation_errors) == 0
        assert result.metadata.title == "One Piece"
        assert result.metadata.author == "Eiichiro Oda"
        assert result.metadata.chapter == 1
        assert result.metadata.chapter_title == "Romance Dawn"
        assert result.metadata.source == "local"

    def test_missing_optional_metadata(self) -> None:
        """Test processing with missing optional fields."""
        metadata = MangaMetadata()

        result = process(metadata)

        assert result.valid is True
        assert len(result.validation_errors) == 0
        assert result.metadata.title is None
        assert result.metadata.author is None
        assert result.metadata.chapter is None
        assert result.metadata.chapter_title is None
        assert result.metadata.source is None


class TestNormalization:
    """Tests for metadata normalization."""

    def test_whitespace_trimming(self) -> None:
        """Test whitespace trimming for string fields."""
        metadata = MangaMetadata(
            title="  One Piece  ",
            author="  Eiichiro Oda  ",
        )

        result = process(metadata)

        assert result.metadata.title == "One Piece"
        assert result.metadata.author == "Eiichiro Oda"

    def test_empty_string_normalization(self) -> None:
        """Test empty string normalization to None."""
        metadata = MangaMetadata(
            title="",
            author="Eiichiro Oda",
        )

        result = process(metadata)

        assert result.metadata.title is None
        assert result.metadata.author == "Eiichiro Oda"

    def test_whitespace_only_normalization(self) -> None:
        """Test whitespace-only string normalization to None."""
        metadata = MangaMetadata(
            title="   ",
            author="   ",
        )

        result = process(metadata)

        assert result.metadata.title is None
        assert result.metadata.author is None

    def test_chapter_title_normalization(self) -> None:
        """Test chapter title whitespace normalization."""
        metadata = MangaMetadata(
            chapter_title="  Romance   Dawn   v2  ",
        )

        result = process(metadata)

        assert result.metadata.chapter_title == "Romance Dawn v2"

    def test_source_normalization(self) -> None:
        """Test source identifier trimming."""
        metadata = MangaMetadata(
            source="  local  ",
        )

        result = process(metadata)

        assert result.metadata.source == "local"


class TestValidation:
    """Tests for metadata validation."""

    def test_invalid_chapter_zero(self) -> None:
        """Test validation of chapter number zero."""
        metadata = MangaMetadata(chapter=0)

        result = process(metadata)

        assert result.valid is False
        assert any("Chapter number must be >= 1" in e for e in result.validation_errors)

    def test_invalid_chapter_negative(self) -> None:
        """Test validation of negative chapter number."""
        metadata = MangaMetadata(chapter=-1)

        result = process(metadata)

        assert result.valid is False
        assert any("Chapter number must be >= 1" in e for e in result.validation_errors)

    def test_valid_chapter_one(self) -> None:
        """Test validation of chapter number 1."""
        metadata = MangaMetadata(chapter=1)

        result = process(metadata)

        assert result.valid is True
        assert len(result.validation_errors) == 0

    def test_none_chapter_valid(self) -> None:
        """Test that None chapter is valid."""
        metadata = MangaMetadata(chapter=None)

        result = process(metadata)

        assert result.valid is True
        assert result.metadata.chapter is None


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        metadata = MangaMetadata(
            title="  One Piece  ",
            author="Eiichiro Oda",
            chapter=10,
            chapter_title="  Chapter  10  ",
        )

        result1 = process(metadata)
        result2 = process(metadata)

        assert result1.valid == result2.valid
        assert result1.metadata.title == result2.metadata.title
        assert result1.metadata.author == result2.metadata.author
        assert result1.metadata.chapter == result2.metadata.chapter
        assert result1.metadata.chapter_title == result2.metadata.chapter_title


class TestMutationSafety:
    """Tests for mutation safety."""

    def test_original_not_modified(self) -> None:
        """Test that original MangaMetadata is not modified."""
        metadata = MangaMetadata(
            title="  One Piece  ",
            author="  Eiichiro Oda  ",
            chapter=1,
        )
        original_title = metadata.title
        original_author = metadata.author

        process(metadata)

        assert metadata.title == original_title
        assert metadata.author == original_author

    def test_new_metadata_created(self) -> None:
        """Test that a new normalized metadata object is created."""
        metadata = MangaMetadata(title="  One Piece  ")

        result = process(metadata)

        assert result.metadata is not metadata
        assert metadata.title == "  One Piece  "
        assert result.metadata.title == "One Piece"


class TestMetadataProcessorClass:
    """Tests for MangaMetadataProcessor class."""

    def test_processor_process_method(self) -> None:
        """Test MangaMetadataProcessor.process method."""
        metadata = MangaMetadata(
            title="One Piece",
            chapter=1,
        )

        processor = MangaMetadataProcessor()
        result = processor.process(metadata)

        assert result.valid is True
        assert result.metadata.title == "One Piece"
        assert result.metadata.chapter == 1


class TestImports:
    """Tests for public API imports."""

    def test_import_metadata_processor(self) -> None:
        """Test MangaMetadataProcessor can be imported."""
        from tools.manga.metadata import MangaMetadataProcessor
        assert MangaMetadataProcessor is not None

    def test_import_metadata_result(self) -> None:
        """Test MetadataResult can be imported."""
        assert MetadataResult is not None

    def test_import_process_function(self) -> None:
        """Test process function can be imported."""
        from tools.manga.metadata import process
        assert callable(process)

    def test_import_metadata_module(self) -> None:
        """Test metadata module can be imported."""
        from tools.manga import metadata
        assert metadata is not None
