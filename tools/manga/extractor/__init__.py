"""Manga extractor module.

V1 provides metadata-level extraction validation and statistics from MangaParseResult.
Does NOT perform image processing, OCR, or visual extraction.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from tools.manga.exceptions import MangaExtractionError
from tools.manga.models import MangaPage, MangaParseResult


class PageExtraction(BaseModel):
    """Extracted page information.

    Preserves existing MangaPage metadata without modification.
    """

    page_number: int
    file_path: str | None
    width: int | None
    height: int | None
    has_dimensions: bool


class ExtractionResult(BaseModel):
    """Result of manga extraction operation.

    Contains validated page metadata and dimension statistics.
    """

    total_pages: int
    pages: list[PageExtraction] = Field(default_factory=list)
    known_dimensions: int = 0
    missing_dimensions: int = 0
    valid: bool = True
    validation_errors: list[str] = Field(default_factory=list)


def _extract_page(page: MangaPage) -> PageExtraction:
    """Extract page information from MangaPage without mutation."""
    has_dims = page.width is not None and page.height is not None
    file_path_str = str(page.file_path) if page.file_path else None
    return PageExtraction(
        page_number=page.page_number,
        file_path=file_path_str,
        width=page.width,
        height=page.height,
        has_dimensions=has_dims,
    )


def _validate_page_numbers(pages: list[MangaPage]) -> list[str]:
    """Validate page numbering and return list of validation errors."""
    errors = []

    if not pages:
        errors.append("No pages to validate")
        return errors

    page_numbers = [p.page_number for p in pages]

    expected_start = 0
    if page_numbers[0] != expected_start:
        errors.append(f"Expected first page number to be {expected_start}, got {page_numbers[0]}")

    seen = set()
    duplicates = []
    for num in page_numbers:
        if num in seen:
            duplicates.append(num)
        seen.add(num)

    if duplicates:
        errors.append(f"Duplicate page numbers found: {sorted(set(duplicates))}")

    expected = set(range(len(pages)))
    actual = set(page_numbers)
    missing = expected - actual
    if missing:
        errors.append(f"Missing page numbers: {sorted(missing)}")

    for i, page in enumerate(pages):
        if page.page_number < 0:
            errors.append(f"Invalid page number {page.page_number} at index {i} (must be >= 0)")

    return errors


def extract(parse_result: MangaParseResult) -> ExtractionResult:
    """Extract and validate page metadata from MangaParseResult.

    Performs validation on the parse result without modifying it.
    Produces an ExtractionResult with dimension statistics.

    Args:
        parse_result: Result from MangaParser containing pages and metadata

    Returns:
        ExtractionResult with validated page info and statistics

    Raises:
        MangaExtractionError: If validation fails critically
    """
    if parse_result.total_pages != len(parse_result.pages):
        raise MangaExtractionError(
            f"total_pages mismatch: expected {len(parse_result.pages)}, got {parse_result.total_pages}"
        )

    validation_errors = _validate_page_numbers(parse_result.pages)

    extractions = [_extract_page(page) for page in parse_result.pages]

    known_dims = sum(1 for e in extractions if e.has_dimensions)
    missing_dims = len(extractions) - known_dims

    result = ExtractionResult(
        total_pages=parse_result.total_pages,
        pages=extractions,
        known_dimensions=known_dims,
        missing_dimensions=missing_dims,
        valid=len(validation_errors) == 0,
        validation_errors=validation_errors,
    )

    return result


class MangaExtractor:
    """Extractor for manga page metadata.

    Validates MangaParseResult and produces ExtractionResult with
    dimension statistics. V1 does not perform image processing.

    Example:
        extractor = MangaExtractor()
        result = extractor.extract(parse_result)
    """

    def extract(self, parse_result: MangaParseResult) -> ExtractionResult:
        """Extract and validate page metadata.

        Args:
            parse_result: MangaParseResult from parser

        Returns:
            ExtractionResult with validated pages and statistics
        """
        return extract(parse_result)


__all__ = ["MangaExtractor", "ExtractionResult", "PageExtraction", "extract"]
