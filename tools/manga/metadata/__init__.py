"""Manga metadata module.

V1 provides metadata normalization and validation for MangaMetadata.
Does NOT fetch metadata from external sources.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from tools.manga.models import MangaMetadata


class MetadataResult(BaseModel):
    """Result of metadata processing operation.

    Contains normalized metadata and validation information.
    """

    metadata: MangaMetadata
    valid: bool = True
    validation_errors: list[str] = Field(default_factory=list)


def _normalize_string(value: str | None) -> str | None:
    """Normalize a string by trimming whitespace and converting empty to None."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _normalize_chapter_title(value: str | None) -> str | None:
    """Normalize chapter title by trimming whitespace and collapsing internal spaces."""
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized if normalized else None


def _normalize_source(value: str | None) -> str | None:
    """Normalize source identifier by trimming whitespace."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _normalize_metadata(metadata: MangaMetadata) -> MangaMetadata:
    """Create a normalized copy of MangaMetadata without mutation."""
    return MangaMetadata(
        title=_normalize_string(metadata.title),
        author=_normalize_string(metadata.author),
        chapter=metadata.chapter,
        chapter_title=_normalize_chapter_title(metadata.chapter_title),
        source=_normalize_source(metadata.source),
    )


def _validate_chapter(chapter: int | None) -> list[str]:
    """Validate chapter number."""
    errors = []
    if chapter is not None and chapter < 1:
        errors.append(f"Chapter number must be >= 1, got {chapter}")
    return errors


def _validate_metadata(metadata: MangaMetadata) -> list[str]:
    """Validate metadata and return list of validation errors."""
    errors = []

    errors.extend(_validate_chapter(metadata.chapter))

    return errors


def process(metadata: MangaMetadata) -> MetadataResult:
    """Normalize and validate manga metadata.

    Creates a normalized copy without mutating the original.
    Performs deterministic validation.

    Args:
        metadata: MangaMetadata to process

    Returns:
        MetadataResult with normalized metadata and validation status
    """
    errors = _validate_metadata(metadata)

    normalized = _normalize_metadata(metadata)

    result = MetadataResult(
        metadata=normalized,
        valid=len(errors) == 0,
        validation_errors=errors,
    )

    return result


class MangaMetadataProcessor:
    """Processor for manga metadata normalization and validation.

    Provides deterministic metadata processing without mutation.
    V1 does not fetch metadata from external sources.

    Example:
        processor = MangaMetadataProcessor()
        result = processor.process(metadata)
    """

    def process(self, metadata: MangaMetadata) -> MetadataResult:
        """Normalize and validate metadata.

        Args:
            metadata: MangaMetadata to process

        Returns:
            MetadataResult with normalized metadata and validation status
        """
        return process(metadata)


__all__ = ["MangaMetadataProcessor", "MetadataResult", "process"]
