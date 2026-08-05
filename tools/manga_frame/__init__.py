"""Manga to Frame integration contract.

Provides boundary between tools/manga/ and tools/frame/ modules.

This module is the integration layer that maps manga domain objects
to frame domain objects WITHOUT creating circular dependencies.

Architecture:
    tools/manga/  -->  tools/manga_frame/  -->  tools/frame/
                         (THIS MODULE)

This module:
- Imports from tools.manga (downstream)
- Imports from tools.frame (downstream)
- Does NOT import into either module

Responsibilities:
- Map MangaPage -> Frame with BACKGROUND layer
- Map MangaParseResult -> FrameSequence
- Preserve manga metadata as optional context
- Accept explicit CharacterColorPalette (NOT auto-generated)
- Maintain immutability and determinism
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tools.frame.models import (
    Frame,
    FrameLayer,
    FrameSequence,
    LayerType,
)
from tools.frame.palette import CharacterColorPalette
from tools.manga.models import MangaParseResult

# ============================================================================
# Input Contract
# ============================================================================


class MangaFrameInput(BaseModel):
    """Input contract for manga to frame conversion.

    This is the ONLY input contract for the manga->frame boundary.
    All conversion happens through this contract.

    Attributes:
        parse_result: MangaParseResult from tools.manga parser
        sequence_id: Unique identifier for the output FrameSequence
        name: Human-readable name for the sequence (optional)
        frame_rate: Target frame rate in FPS (default: 24.0)
        character_palettes: Explicit character color palettes (optional)
            NOTE: These must be EXPLICITLY provided.
            Color extraction from manga is NOT in scope.
    """

    parse_result: MangaParseResult = Field(
        description="Manga parse result containing pages and metadata"
    )
    sequence_id: str = Field(
        min_length=1,
        description="Unique identifier for the output sequence"
    )
    name: str | None = Field(
        default=None,
        description="Human-readable sequence name"
    )
    frame_rate: float = Field(
        default=24.0,
        gt=0,
        le=120,
        description="Target frame rate in FPS"
    )
    character_palettes: dict[str, CharacterColorPalette] | None = Field(
        default=None,
        description="Explicit character color palettes (NOT auto-generated)"
    )

    @property
    def total_frames(self) -> int:
        """Get the number of frames from parse result."""
        return self.parse_result.total_pages

    def get_palette_for_character(self, character_id: str) -> CharacterColorPalette | None:
        """Get explicit palette for a character if provided.

        Args:
            character_id: The character identifier to look up

        Returns:
            CharacterColorPalette if explicitly provided, None otherwise
        """
        if self.character_palettes is None:
            return None
        return self.character_palettes.get(character_id)


# ============================================================================
# Output Contract
# ============================================================================


@dataclass(frozen=True)
class MangaFrameOutput:
    """Output of manga to frame conversion.

    Immutable result containing the converted FrameSequence
    and any associated metadata.

    Attributes:
        sequence: The converted FrameSequence
        pages_converted: Number of pages converted to frames
        metadata_preserved: Whether manga metadata was preserved
        palettes_provided: Whether explicit palettes were provided
    """

    sequence: FrameSequence
    pages_converted: int
    metadata_preserved: bool
    palettes_provided: bool


# ============================================================================
# Mapping Logic
# ============================================================================


def _create_frame_from_page(
    page_index: int,
    file_path: Path | None,
) -> Frame:
    """Create a Frame from a manga page.

    Mapping:
    - page_index -> frame_index
    - file_path -> source_path
    - LayerType.BACKGROUND layer created automatically

    Args:
        page_index: Zero-based page index from MangaPage
        file_path: Path to the manga page file

    Returns:
        Frame with BACKGROUND layer
    """
    # Create BACKGROUND layer for the manga page
    background_layer = FrameLayer(
        layer_type=LayerType.BACKGROUND,
        layer_index=0,
        source_path=file_path,
        visible=True,
    )

    return Frame(
        frame_index=page_index,
        layers=(background_layer,),  # tuple for immutability
        source_path=file_path,
    )


def _build_sequence_name(metadata_title: str | None, chapter: int | None) -> str | None:
    """Build sequence name from manga metadata.

    Args:
        metadata_title: Title from MangaMetadata
        chapter: Chapter number from MangaMetadata

    Returns:
        Formatted name string or None
    """
    if metadata_title is None and chapter is None:
        return None

    parts = []
    if metadata_title:
        parts.append(metadata_title)
    if chapter is not None:
        parts.append(f"Chapter {chapter}")

    return " - ".join(parts)


def convert_manga_to_frames(input_contract: MangaFrameInput) -> MangaFrameOutput:
    """Convert manga parse result to frame sequence.

    This is the primary conversion function for the manga->frame boundary.

    Mapping rules:
    - MangaPage.page_number -> Frame.frame_index
    - MangaPage.file_path -> Frame.source_path AND FrameLayer.source_path
    - MangaMetadata.title/chapter -> FrameSequence.name (if provided)
    - CharacterColorPalette -> NOT auto-generated, must be explicit input

    Immutability:
    - Output FrameSequence is frozen
    - Frame.layers is tuple (immutable)
    - No side effects on input objects

    Determinism:
    - Same input produces same output
    - No random values
    - No timestamps
    - No environment-dependent values

    Args:
        input_contract: MangaFrameInput containing parse result and config

    Returns:
        MangaFrameOutput containing converted FrameSequence

    Raises:
        ValueError: If parse_result has no pages
    """
    parse_result = input_contract.parse_result

    # Validate we have pages to convert
    if not parse_result.pages:
        raise ValueError("Cannot convert empty manga parse result (no pages)")

    # Create frames from pages
    frames: list[Frame] = []
    for manga_page in parse_result.pages:
        frame = _create_frame_from_page(
            page_index=manga_page.page_number,
            file_path=manga_page.file_path,
        )
        frames.append(frame)

    # Build sequence name from metadata if available
    metadata = parse_result.metadata
    sequence_name = input_contract.name
    if sequence_name is None:
        sequence_name = _build_sequence_name(
            metadata_title=metadata.title,
            chapter=metadata.chapter,
        )

    # Create the frozen FrameSequence
    sequence = FrameSequence(
        sequence_id=input_contract.sequence_id,
        name=sequence_name,
        frame_rate=input_contract.frame_rate,
        frames=frames,  # FrameSequence validator converts to tuple
        transitions=(),  # No transitions for basic manga->frame conversion
    )

    # Determine metadata preservation and palette status
    metadata_preserved = any([
        metadata.title is not None,
        metadata.author is not None,
        metadata.chapter is not None,
        metadata.chapter_title is not None,
        metadata.source is not None,
    ])

    palettes_provided = input_contract.character_palettes is not None

    return MangaFrameOutput(
        sequence=sequence,
        pages_converted=len(frames),
        metadata_preserved=metadata_preserved,
        palettes_provided=palettes_provided,
    )


# ============================================================================
# Factory Function
# ============================================================================


def create_frame_sequence_from_manga(
    parse_result: MangaParseResult,
    sequence_id: str,
    *,
    name: str | None = None,
    frame_rate: float = 24.0,
    character_palettes: dict[str, CharacterColorPalette] | None = None,
) -> FrameSequence:
    """Factory function to convert manga to frame sequence.

    Convenience wrapper around MangaFrameInput + convert_manga_to_frames.

    Args:
        parse_result: MangaParseResult from tools.manga parser
        sequence_id: Unique identifier for the output sequence
        name: Human-readable name (optional)
        frame_rate: Target frame rate in FPS (default: 24.0)
        character_palettes: Explicit character palettes (optional)

    Returns:
        Converted FrameSequence

    Example:
        >>> from tools.manga import MangaParser
        >>> parser = MangaParser()
        >>> result = parser.parse(MangaInput(path=Path("/manga/chapter1")))
        >>> sequence = create_frame_sequence_from_manga(
        ...     parse_result=result,
        ...     sequence_id="chapter1_frames",
        ...     name="Chapter 1"
        ... )
    """
    input_contract = MangaFrameInput(
        parse_result=parse_result,
        sequence_id=sequence_id,
        name=name,
        frame_rate=frame_rate,
        character_palettes=character_palettes,
    )

    output = convert_manga_to_frames(input_contract)
    return output.sequence


__all__ = [
    "MangaFrameInput",
    "MangaFrameOutput",
    "convert_manga_to_frames",
    "create_frame_sequence_from_manga",
]
