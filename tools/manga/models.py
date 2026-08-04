"""Manga tool data models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class MangaInput(BaseModel):
    """Represents manga source input."""

    path: Path | None = None
    url: str | None = None
    source_id: str | None = Field(default=None, description="External source identifier")

    def model_post_init(self, _):  # type: ignore[no-untyped-def]
        if self.path is None and self.url is None:
            raise ValueError("Either path or url must be provided")


class MangaPage(BaseModel):
    """Represents a single manga page."""

    page_number: int = Field(ge=0)
    width: int | None = None
    height: int | None = None
    file_path: Path | None = None


class MangaMetadata(BaseModel):
    """Manga metadata information."""

    title: str | None = None
    author: str | None = None
    chapter: int | None = None
    chapter_title: str | None = None
    source: str | None = None


class MangaParseResult(BaseModel):
    """Result of manga parsing operation."""

    metadata: MangaMetadata
    pages: list[MangaPage] = Field(default_factory=list)
    total_pages: int = 0
