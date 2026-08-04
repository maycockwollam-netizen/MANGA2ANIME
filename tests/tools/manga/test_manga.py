"""Tests for manga tools."""

from pathlib import Path

import pytest

from tools.manga import (
    MangaExtractionError,
    MangaInput,
    MangaInputError,
    MangaMetadata,
    MangaMetadataError,
    MangaPage,
    MangaParseError,
    MangaParseResult,
    MangaToolError,
)


class TestMangaExceptions:
    """Tests for manga exception hierarchy."""

    def test_manga_tool_error(self) -> None:
        """Test MangaToolError is base exception."""
        with pytest.raises(MangaToolError):
            raise MangaToolError("test")

    def test_manga_parse_error_inherits(self) -> None:
        """Test MangaParseError inherits from MangaToolError."""
        with pytest.raises(MangaToolError):
            raise MangaParseError("test")

    def test_manga_extraction_error_inherits(self) -> None:
        """Test MangaExtractionError inherits from MangaToolError."""
        with pytest.raises(MangaToolError):
            raise MangaExtractionError("test")

    def test_manga_metadata_error_inherits(self) -> None:
        """Test MangaMetadataError inherits from MangaToolError."""
        with pytest.raises(MangaToolError):
            raise MangaMetadataError("test")

    def test_manga_input_error_inherits(self) -> None:
        """Test MangaInputError inherits from MangaToolError."""
        with pytest.raises(MangaToolError):
            raise MangaInputError("test")


class TestMangaModels:
    """Tests for manga data models."""

    def test_manga_input_with_path(self) -> None:
        """Test MangaInput with path."""
        inp = MangaInput(path=Path("/path/to/manga"))
        assert inp.path == Path("/path/to/manga")
        assert inp.url is None

    def test_manga_input_with_url(self) -> None:
        """Test MangaInput with URL."""
        inp = MangaInput(url="https://example.com/manga")
        assert inp.url == "https://example.com/manga"
        assert inp.path is None

    def test_manga_input_requires_path_or_url(self) -> None:
        """Test MangaInput requires path or URL."""
        with pytest.raises(ValueError, match="Either path or url"):
            MangaInput()

    def test_manga_page(self) -> None:
        """Test MangaPage model."""
        page = MangaPage(page_number=1, width=1920, height=1080)
        assert page.page_number == 1
        assert page.width == 1920
        assert page.height == 1080

    def test_manga_metadata(self) -> None:
        """Test MangaMetadata model."""
        meta = MangaMetadata(
            title="Test Manga",
            author="Test Author",
            chapter=5,
        )
        assert meta.title == "Test Manga"
        assert meta.author == "Test Author"
        assert meta.chapter == 5

    def test_manga_parse_result(self) -> None:
        """Test MangaParseResult model."""
        meta = MangaMetadata(title="Test")
        result = MangaParseResult(metadata=meta, total_pages=10)
        assert result.metadata.title == "Test"
        assert result.total_pages == 10
        assert len(result.pages) == 0


class TestMangaImports:
    """Tests for manga package imports."""

    def test_import_tools_manga(self) -> None:
        """Test tools.manga package imports."""
        import tools.manga
        assert hasattr(tools.manga, "MangaToolError")

    def test_import_parser(self) -> None:
        """Test tools.manga.parser package imports."""
        import tools.manga.parser
        assert tools.manga.parser is not None

    def test_import_extractor(self) -> None:
        """Test tools.manga.extractor package imports."""
        import tools.manga.extractor
        assert tools.manga.extractor is not None

    def test_import_metadata(self) -> None:
        """Test tools.manga.metadata package imports."""
        import tools.manga.metadata
        assert tools.manga.metadata is not None


class TestDependencyRules:
    """Tests verifying dependency rules."""

    def test_tools_manga_does_not_import_runtime(self) -> None:
        """Verify tools/manga does not import runtime."""
        from pathlib import Path

        manga_dir = Path("tools/manga")
        for py_file in manga_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "from runtime" not in content
            assert "import runtime" not in content

    def test_tools_manga_does_not_import_agents(self) -> None:
        """Verify tools/manga does not import agents."""
        from pathlib import Path

        manga_dir = Path("tools/manga")
        for py_file in manga_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "from agents" not in content
            assert "import agents" not in content

    def test_tools_manga_does_not_import_apps(self) -> None:
        """Verify tools/manga does not import apps."""
        from pathlib import Path

        manga_dir = Path("tools/manga")
        for py_file in manga_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "from apps" not in content
            assert "import apps" not in content
