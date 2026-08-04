"""Tests for manga extractor."""

from pathlib import Path

import pytest

from tools.manga import MangaExtractionError, MangaMetadata, MangaPage, MangaParseResult
from tools.manga.extractor import (
    ExtractionResult,
    MangaExtractor,
    PageExtraction,
    extract,
)


class TestBasicExtraction:
    """Tests for basic extraction functionality."""

    def test_extract_single_page(self) -> None:
        """Test extraction of a single page."""
        page = MangaPage(page_number=0, file_path=Path("1.jpg"))
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[page],
            total_pages=1,
        )

        result = extract(parse_result)

        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert result.pages[0].page_number == 0
        assert result.pages[0].file_path == "1.jpg"

    def test_extract_multiple_pages(self) -> None:
        """Test extraction of multiple pages."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
            MangaPage(page_number=2, file_path=Path("3.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=3,
        )

        result = extract(parse_result)

        assert result.total_pages == 3
        assert len(result.pages) == 3
        assert result.valid is True
        assert len(result.validation_errors) == 0


class TestDimensionHandling:
    """Tests for dimension statistics."""

    def test_all_dimensions_known(self) -> None:
        """Test when all pages have dimensions."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920, height=1080),
            MangaPage(page_number=1, file_path=Path("2.jpg"), width=1920, height=1080),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        result = extract(parse_result)

        assert result.known_dimensions == 2
        assert result.missing_dimensions == 0
        assert all(p.has_dimensions for p in result.pages)

    def test_some_dimensions_missing(self) -> None:
        """Test when some pages are missing dimensions."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920, height=1080),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        result = extract(parse_result)

        assert result.known_dimensions == 1
        assert result.missing_dimensions == 1
        assert result.pages[0].has_dimensions is True
        assert result.pages[1].has_dimensions is False

    def test_all_dimensions_missing(self) -> None:
        """Test when all pages are missing dimensions."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        result = extract(parse_result)

        assert result.known_dimensions == 0
        assert result.missing_dimensions == 2
        assert all(not p.has_dimensions for p in result.pages)

    def test_partial_dimensions(self) -> None:
        """Test pages with only width or only height."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920),
            MangaPage(page_number=1, file_path=Path("2.jpg"), height=1080),
            MangaPage(page_number=2, file_path=Path("3.jpg"), width=1920, height=1080),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=3,
        )

        result = extract(parse_result)

        assert result.known_dimensions == 1
        assert result.missing_dimensions == 2


class TestPageValidation:
    """Tests for page number validation."""

    def test_empty_pages(self) -> None:
        """Test validation of empty pages list."""
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[],
            total_pages=0,
        )

        result = extract(parse_result)

        assert result.valid is False
        assert "No pages to validate" in result.validation_errors

    def test_duplicate_page_numbers(self) -> None:
        """Test detection of duplicate page numbers."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
            MangaPage(page_number=1, file_path=Path("3.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=3,
        )

        result = extract(parse_result)

        assert result.valid is False
        assert any("Duplicate page numbers" in e for e in result.validation_errors)

    def test_missing_page_numbers(self) -> None:
        """Test detection of missing page numbers."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
            MangaPage(page_number=3, file_path=Path("4.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=3,
        )

        result = extract(parse_result)

        assert result.valid is False
        assert any("Missing page numbers" in e for e in result.validation_errors)

    def test_wrong_starting_page(self) -> None:
        """Test detection of wrong starting page number."""
        pages = [
            MangaPage(page_number=1, file_path=Path("1.jpg")),
            MangaPage(page_number=2, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        result = extract(parse_result)

        assert result.valid is False
        assert any("first page number" in e for e in result.validation_errors)


class TestTotalPagesValidation:
    """Tests for total_pages consistency."""

    def test_total_pages_mismatch(self) -> None:
        """Test detection of total_pages mismatch."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=5,
        )

        with pytest.raises(MangaExtractionError, match="total_pages mismatch"):
            extract(parse_result)


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920, height=1080),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        result1 = extract(parse_result)
        result2 = extract(parse_result)

        assert result1.total_pages == result2.total_pages
        assert len(result1.pages) == len(result2.pages)
        for p1, p2 in zip(result1.pages, result2.pages, strict=True):
            assert p1.page_number == p2.page_number
            assert p1.file_path == p2.file_path
            assert p1.has_dimensions == p2.has_dimensions
        assert result1.known_dimensions == result2.known_dimensions


class TestMutationSafety:
    """Tests for mutation safety."""

    def test_original_not_modified(self) -> None:
        """Test that original MangaParseResult is not modified."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920, height=1080),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )
        original_pages_len = len(parse_result.pages)
        original_total = parse_result.total_pages
        original_width = parse_result.pages[0].width

        extract(parse_result)

        assert len(parse_result.pages) == original_pages_len
        assert parse_result.total_pages == original_total
        assert parse_result.pages[0].width == original_width

    def test_page_objects_unchanged(self) -> None:
        """Test that page objects are not modified."""
        page = MangaPage(page_number=0, file_path=Path("1.jpg"), width=1920, height=1080)
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=[page],
            total_pages=1,
        )
        original_file_path = page.file_path
        original_width = page.width
        original_height = page.height

        extract(parse_result)

        assert page.file_path == original_file_path
        assert page.width == original_width
        assert page.height == original_height


class TestExceptionHandling:
    """Tests for exception handling."""

    def test_manga_extraction_error_raised(self) -> None:
        """Test that MangaExtractionError is raised on critical errors."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=5,
        )

        with pytest.raises(MangaExtractionError):
            extract(parse_result)


class TestExtractorClass:
    """Tests for MangaExtractor class."""

    def test_extractor_extract_method(self) -> None:
        """Test MangaExtractor.extract method."""
        pages = [
            MangaPage(page_number=0, file_path=Path("1.jpg")),
            MangaPage(page_number=1, file_path=Path("2.jpg")),
        ]
        parse_result = MangaParseResult(
            metadata=MangaMetadata(),
            pages=pages,
            total_pages=2,
        )

        extractor = MangaExtractor()
        result = extractor.extract(parse_result)

        assert result.total_pages == 2
        assert len(result.pages) == 2


class TestImports:
    """Tests for public API imports."""

    def test_import_extractor(self) -> None:
        """Test extractor module can be imported."""
        from tools.manga import extractor
        assert extractor is not None

    def test_import_manga_extractor(self) -> None:
        """Test MangaExtractor can be imported."""
        from tools.manga.extractor import MangaExtractor
        assert MangaExtractor is not None

    def test_import_extraction_result(self) -> None:
        """Test ExtractionResult can be imported."""
        assert ExtractionResult is not None

    def test_import_page_extraction(self) -> None:
        """Test PageExtraction can be imported."""
        assert PageExtraction is not None

    def test_import_extract_function(self) -> None:
        """Test extract function can be imported."""
        from tools.manga.extractor import extract
        assert callable(extract)
