"""Manga parser module.

Parses manga input sources (directories, archives) into structured page metadata.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from tools.manga.exceptions import MangaInputError, MangaParseError
from tools.manga.models import (
    MangaInput,
    MangaMetadata,
    MangaPage,
    MangaParseResult,
)

SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def _natural_sort_key(filename: str) -> tuple[tuple[int | str, ...], str]:
    """Generate a sort key that handles mixed numbers and text naturally.

    Example: 'page10.jpg' -> ((0, 'page'), 10, '.jpg')
    """
    parts = re.split(r"(\d+)", filename)
    key = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            key.append((0, int(part)))
        elif part:
            key.append((1, part.lower()))
    return tuple(key)


def _is_supported_image(filename: str) -> bool:
    """Check if filename has a supported image extension (case-insensitive)."""
    suffix = Path(filename).suffix.lower()
    return suffix in SUPPORTED_EXTENSIONS


def _scan_directory(directory: Path) -> list[Path]:
    """Scan directory for supported image files with natural sorting."""
    if not directory.is_dir():
        raise MangaInputError(f"Path is not a directory: {directory}")

    image_files = []
    for item in directory.iterdir():
        if item.is_file() and _is_supported_image(item.name):
            image_files.append(item)

    if not image_files:
        raise MangaParseError(f"No supported image files found in: {directory}")

    image_files.sort(key=lambda p: _natural_sort_key(p.name))
    return image_files


def _scan_archive(archive_path: Path) -> list[str]:
    """Scan ZIP archive for supported image files with natural sorting."""
    if not archive_path.is_file():
        raise MangaInputError(f"Path is not a file: {archive_path}")

    if not archive_path.suffix.lower() == ".zip":
        raise MangaInputError(f"Unsupported archive type: {archive_path.suffix}")

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            image_files = []
            for name in zf.namelist():
                if _is_supported_image(name) and not name.endswith("/"):
                    image_files.append(name)

            if not image_files:
                raise MangaParseError(f"No supported image files found in archive: {archive_path}")

            image_files.sort(key=_natural_sort_key)
            return image_files
    except zipfile.BadZipFile as e:
        raise MangaParseError(f"Invalid or corrupted ZIP archive: {archive_path}") from e


def _extract_chapter_from_path(path: Path) -> int | None:
    """Try to extract chapter number from path name.

    Matches patterns like: chapter_12, chapter-12, Chapter 12, etc.
    Returns None if no chapter number can be determined.
    """
    name = path.name
    match = re.search(r"chapter[_\-\s]*(\d+)", name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


class MangaParser:
    """Parser for manga input sources.

    Parses directory or ZIP archive inputs containing manga pages and produces
    structured MangaParseResult with page metadata.

    Example:
        parser = MangaParser()
        result = parser.parse(MangaInput(path=Path("/path/to/chapter")))
    """

    def parse(self, manga_input: MangaInput) -> MangaParseResult:
        """Parse manga input and return structured result.

        Args:
            manga_input: MangaInput containing path or URL

        Returns:
            MangaParseResult with page metadata

        Raises:
            MangaInputError: If input is invalid or missing
            MangaParseError: If parsing fails
        """
        if manga_input.url is not None:
            raise MangaInputError(
                "URL input is not supported in Parser V1. "
                "Please provide a local directory or ZIP archive."
            )

        if manga_input.path is None:
            raise MangaInputError("No path provided in MangaInput")

        path = manga_input.path

        if not path.exists():
            raise MangaInputError(f"Path does not exist: {path}")

        metadata = MangaMetadata()

        if path.is_file():
            if path.suffix.lower() == ".zip":
                image_names = _scan_archive(path)
                pages = [
                    MangaPage(page_number=i, file_path=Path(name))
                    for i, name in enumerate(image_names)
                ]
                chapter = _extract_chapter_from_path(path)
                if chapter is not None:
                    metadata.chapter = chapter
            else:
                raise MangaInputError(
                    f"Unsupported file type: {path.suffix}. "
                    f"Supported types: .zip, {', '.join(SUPPORTED_EXTENSIONS)}"
                )
        else:
            image_files = _scan_directory(path)
            pages = [
                MangaPage(page_number=i, file_path=rel_path)
                for i, rel_path in enumerate(image_files)
            ]
            chapter = _extract_chapter_from_path(path)
            if chapter is not None:
                metadata.chapter = chapter

        result = MangaParseResult(
            metadata=metadata,
            pages=pages,
            total_pages=len(pages),
        )
        return result


__all__ = ["MangaParser"]
