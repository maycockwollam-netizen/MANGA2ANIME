"""Manga tools exceptions."""


class MangaToolError(Exception):
    """Base exception for manga tool errors."""

    pass


class MangaParseError(MangaToolError):
    """Raised when manga parsing fails."""

    pass


class MangaExtractionError(MangaToolError):
    """Raised when manga extraction fails."""

    pass


class MangaMetadataError(MangaToolError):
    """Raised when manga metadata operations fail."""

    pass


class MangaInputError(MangaToolError):
    """Raised when manga input is invalid."""

    pass
