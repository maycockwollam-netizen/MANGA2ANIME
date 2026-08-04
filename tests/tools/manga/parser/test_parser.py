"""Tests for manga parser."""

import zipfile
from pathlib import Path

import pytest

from tools.manga import (
    MangaInput,
    MangaInputError,
    MangaParseError,
)
from tools.manga.parser import SUPPORTED_EXTENSIONS, MangaParser


class TestNaturalSorting:
    """Tests for natural sorting behavior."""

    def test_natural_sort_single_digits(self, tmp_path: Path) -> None:
        """Test sorting with single digit numbers."""
        for name in ["3.jpg", "1.jpg", "2.jpg"]:
            (tmp_path / name).touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        page_numbers = [p.page_number for p in result.pages]
        assert page_numbers == [0, 1, 2]
        filenames = [p.file_path.name for p in result.pages]
        assert filenames == ["1.jpg", "2.jpg", "3.jpg"]

    def test_natural_sort_double_digits(self, tmp_path: Path) -> None:
        """Test natural sorting with double digits."""
        for name in ["10.jpg", "2.jpg", "1.jpg"]:
            (tmp_path / name).touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        filenames = [p.file_path.name for p in result.pages]
        assert filenames == ["1.jpg", "2.jpg", "10.jpg"]

    def test_natural_sort_mixed_names(self, tmp_path: Path) -> None:
        """Test natural sorting with mixed text and numbers."""
        for name in ["page10.jpg", "page2.jpg", "page1.jpg"]:
            (tmp_path / name).touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        filenames = [p.file_path.name for p in result.pages]
        assert filenames == ["page1.jpg", "page2.jpg", "page10.jpg"]

    def test_natural_sort_case_insensitive(self, tmp_path: Path) -> None:
        """Test sorting is case-insensitive for extensions."""
        for name in ["PAGE1.JPG", "page2.jpg", "Page3.JpG"]:
            (tmp_path / name).touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 3
        assert all(p.page_number == i for i, p in enumerate(result.pages))


class TestSupportedExtensions:
    """Tests for supported image extensions."""

    @pytest.mark.parametrize("ext", [".jpg", ".jpeg", ".png", ".webp"])
    def test_supported_extensions(self, ext: str, tmp_path: Path) -> None:
        """Test all supported extensions are recognized."""
        (tmp_path / f"1{ext}").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 1

    @pytest.mark.parametrize("ext", [".gif", ".bmp", ".tiff", ".pdf", ".txt"])
    def test_unsupported_extensions_ignored(self, ext: str, tmp_path: Path) -> None:
        """Test unsupported extensions are ignored."""
        (tmp_path / f"1{ext}").touch()

        parser = MangaParser()
        with pytest.raises(MangaParseError, match="No supported image files"):
            parser.parse(MangaInput(path=tmp_path))

    def test_uppercase_extension(self, tmp_path: Path) -> None:
        """Test uppercase extensions are recognized."""
        (tmp_path / "1.JPG").touch()
        (tmp_path / "2.PNG").touch()
        (tmp_path / "3.WEBP").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 3


class TestDirectoryParsing:
    """Tests for directory parsing."""

    def test_single_page(self, tmp_path: Path) -> None:
        """Test parsing a directory with a single page."""
        (tmp_path / "cover.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 1
        assert result.pages[0].file_path.name == "cover.jpg"
        assert result.pages[0].page_number == 0

    def test_multiple_pages(self, tmp_path: Path) -> None:
        """Test parsing a directory with multiple pages."""
        for i in range(5):
            (tmp_path / f"{i+1}.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 5
        assert result.total_pages == 5

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test parsing an empty directory raises error."""
        parser = MangaParser()
        with pytest.raises(MangaParseError, match="No supported image files"):
            parser.parse(MangaInput(path=tmp_path))

    def test_directory_with_unsupported_files_ignored(self, tmp_path: Path) -> None:
        """Test unsupported files are ignored."""
        (tmp_path / "1.jpg").touch()
        (tmp_path / "2.txt").touch()
        (tmp_path / "3.pdf").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert len(result.pages) == 1
        assert result.pages[0].file_path.name == "1.jpg"


class TestArchiveParsing:
    """Tests for ZIP archive parsing."""

    def test_zip_single_page(self, tmp_path: Path) -> None:
        """Test parsing a ZIP with a single page."""
        zip_path = tmp_path / "chapter.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("cover.jpg", b"")

        parser = MangaParser()
        result = parser.parse(MangaInput(path=zip_path))

        assert len(result.pages) == 1
        assert result.pages[0].file_path.name == "cover.jpg"

    def test_zip_multiple_pages(self, tmp_path: Path) -> None:
        """Test parsing a ZIP with multiple pages."""
        zip_path = tmp_path / "chapter.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(3):
                zf.writestr(f"{i+1}.jpg", b"")

        parser = MangaParser()
        result = parser.parse(MangaInput(path=zip_path))

        assert len(result.pages) == 3
        assert result.total_pages == 3

    def test_zip_natural_sorting(self, tmp_path: Path) -> None:
        """Test ZIP contents are naturally sorted."""
        zip_path = tmp_path / "chapter.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name in ["10.jpg", "2.jpg", "1.jpg"]:
                zf.writestr(name, b"")

        parser = MangaParser()
        result = parser.parse(MangaInput(path=zip_path))

        filenames = [p.file_path.name for p in result.pages]
        assert filenames == ["1.jpg", "2.jpg", "10.jpg"]

    def test_zip_unsupported_files_ignored(self, tmp_path: Path) -> None:
        """Test unsupported files in ZIP are ignored."""
        zip_path = tmp_path / "chapter.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("1.jpg", b"")
            zf.writestr("readme.txt", b"")

        parser = MangaParser()
        result = parser.parse(MangaInput(path=zip_path))

        assert len(result.pages) == 1
        assert result.pages[0].file_path.name == "1.jpg"

    def test_zip_empty_archive(self, tmp_path: Path) -> None:
        """Test parsing an empty ZIP raises error."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            pass

        parser = MangaParser()
        with pytest.raises(MangaParseError, match="No supported image files"):
            parser.parse(MangaInput(path=zip_path))

    def test_zip_malformed_archive(self, tmp_path: Path) -> None:
        """Test parsing a malformed ZIP raises error."""
        zip_path = tmp_path / "malformed.zip"
        zip_path.write_bytes(b"not a zip file")

        parser = MangaParser()
        with pytest.raises(MangaParseError, match="Invalid or corrupted"):
            parser.parse(MangaInput(path=zip_path))


class TestChapterExtraction:
    """Tests for chapter number extraction from path."""

    def test_chapter_underscore(self, tmp_path: Path) -> None:
        """Test chapter extraction with underscore."""
        for i in range(3):
            (tmp_path / f"{i+1}.jpg").touch()

        chapter_dir = tmp_path.parent / "chapter_12"
        chapter_dir.mkdir()
        for i in range(3):
            (chapter_dir / f"{i+1}.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=chapter_dir))

        assert result.metadata.chapter == 12

    def test_chapter_hyphen(self, tmp_path: Path) -> None:
        """Test chapter extraction with hyphen."""
        chapter_dir = tmp_path.parent / "chapter-5"
        chapter_dir.mkdir()
        (chapter_dir / "1.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=chapter_dir))

        assert result.metadata.chapter == 5

    def test_chapter_space(self, tmp_path: Path) -> None:
        """Test chapter extraction with space."""
        chapter_dir = tmp_path.parent / "Chapter 10"
        chapter_dir.mkdir()
        (chapter_dir / "1.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=chapter_dir))

        assert result.metadata.chapter == 10

    def test_chapter_zip(self, tmp_path: Path) -> None:
        """Test chapter extraction from ZIP filename."""
        zip_path = tmp_path / "chapter_7.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("1.jpg", b"")

        parser = MangaParser()
        result = parser.parse(MangaInput(path=zip_path))

        assert result.metadata.chapter == 7

    def test_no_chapter_in_name(self, tmp_path: Path) -> None:
        """Test chapter is None when not in name."""
        (tmp_path / "1.jpg").touch()

        parser = MangaParser()
        result = parser.parse(MangaInput(path=tmp_path))

        assert result.metadata.chapter is None


class TestInputValidation:
    """Tests for input validation."""

    def test_missing_input(self) -> None:
        """Test parsing with no path or URL raises error at MangaInput creation."""
        with pytest.raises(ValueError, match="Either path or url must be provided"):
            MangaInput()

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """Test parsing nonexistent path raises error."""
        nonexistent = tmp_path / "does_not_exist"

        parser = MangaParser()
        with pytest.raises(MangaInputError, match="does not exist"):
            parser.parse(MangaInput(path=nonexistent))

    def test_unsupported_file_type(self, tmp_path: Path) -> None:
        """Test parsing unsupported file type raises error."""
        (tmp_path / "document.pdf").touch()

        parser = MangaParser()
        with pytest.raises(MangaInputError, match="Unsupported file type"):
            parser.parse(MangaInput(path=tmp_path / "document.pdf"))

    def test_url_input_not_supported(self) -> None:
        """Test URL input raises error."""
        parser = MangaParser()
        with pytest.raises(MangaInputError, match="URL input is not supported"):
            parser.parse(MangaInput(url="https://example.com/manga.zip"))


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self, tmp_path: Path) -> None:
        """Test same input produces same output."""
        for i in range(5):
            (tmp_path / f"{i+1}.jpg").touch()

        parser = MangaParser()
        result1 = parser.parse(MangaInput(path=tmp_path))
        result2 = parser.parse(MangaInput(path=tmp_path))

        assert len(result1.pages) == len(result2.pages)
        for p1, p2 in zip(result1.pages, result2.pages, strict=True):
            assert p1.page_number == p2.page_number
            assert p1.file_path == p2.file_path


class TestParserImports:
    """Tests for parser imports."""

    def test_import_manga_parser(self) -> None:
        """Test MangaParser can be imported."""
        from tools.manga.parser import MangaParser
        assert MangaParser is not None

    def test_supported_extensions_exported(self) -> None:
        """Test SUPPORTED_EXTENSIONS is accessible."""
        assert ".jpg" in SUPPORTED_EXTENSIONS
        assert ".png" in SUPPORTED_EXTENSIONS
        assert ".webp" in SUPPORTED_EXTENSIONS
