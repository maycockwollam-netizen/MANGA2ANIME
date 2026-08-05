"""Character tracking contracts for manga to frame pipeline.

This module defines data contracts for tracking characters across manga pages.

IMPORTANT: Character tracking implementation is intentionally not included in this
architecture version. This module only defines the contract boundary.

Character Tracking V1 defines contracts only.
It does not detect, identify, recognize, or track characters in images.

Architecture:
    tools/manga/  -->  tools/manga_frame/  -->  character_tracking/  -->  tools/frame/
                                                                    (THIS MODULE)

The contracts define:
- Character tracks (logical character identity across pages)
- Character appearances (where a character appears)
- Tracking status
- Input/output contracts for future tracking implementations

This module does NOT:
- Perform character detection
- Perform character recognition
- Load or decode images
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# Enums
# ============================================================================


class TrackingStatus(StrEnum):
    """Status of a character tracking operation.

    These values indicate the state of a tracking operation, allowing
    callers to handle different outcomes appropriately.
    """

    NOT_PROCESSED = "not_processed"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ============================================================================
# Metadata Container
# ============================================================================


class CharacterTrackMetadata(BaseModel):
    """Immutable metadata container for character tracking results.

    This is a frozen dataclass-style model that stores arbitrary metadata
    about character tracking results.

    Note: This is a contract for metadata storage. The actual metadata
    content depends on the specific tracking implementation.
    """

    model_config = {"frozen": True}

    total_characters: int | None = Field(
        default=None,
        ge=0,
        description="Total number of unique characters tracked"
    )
    total_appearances: int | None = Field(
        default=None,
        ge=0,
        description="Total number of character appearances"
    )
    extra: tuple[tuple[str, str], ...] = Field(
        default_factory=tuple,
        description="Additional key-value metadata as immutable sorted tuple"
    )

    @field_validator("extra", mode="before")
    @classmethod
    def normalize_extra(
        cls,
        v: dict[str, str] | tuple[tuple[str, str], ...] | None
    ) -> tuple[tuple[str, str], ...]:
        """Convert dict to sorted tuple and validate."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return tuple(sorted(v))
        if isinstance(v, dict):
            return tuple(sorted(v.items()))
        return ()


# ============================================================================
# Character Appearance
# ============================================================================


class CharacterAppearance(BaseModel):
    """Represents one appearance of a character on a specific page/frame.

    This contract describes where and how a character appears in a manga page.
    It does NOT perform character detection.

    Attributes:
        page_number: Zero-based page number where the character appears
        frame_index: Frame index in the sequence
        layer_id: Optional layer ID reference
        region_bounds: Optional bounding box (x, y, width, height)
        confidence: Optional confidence score (0.0-1.0)

    Invariants:
        - page_number must be >= 0
        - frame_index must be >= 0
        - confidence, when present, must be 0.0-1.0
        - region_bounds, when present, must have valid dimensions
    """

    page_number: int = Field(
        ge=0,
        description="Zero-based page number"
    )
    frame_index: int = Field(
        ge=0,
        description="Frame index in the sequence"
    )
    layer_id: str | None = Field(
        default=None,
        description="Optional layer ID reference"
    )
    region_bounds: tuple[int, int, int, int] | None = Field(
        default=None,
        description="Bounding box as (x, y, width, height)"
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )

    @field_validator("page_number", mode="before")
    @classmethod
    def validate_page_number(cls, v: int) -> int:
        """Validate page number is non-negative integer."""
        if not isinstance(v, int):
            raise ValueError(f"page_number must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("page_number cannot be negative")
        return v

    @field_validator("frame_index", mode="before")
    @classmethod
    def validate_frame_index(cls, v: int) -> int:
        """Validate frame index is non-negative integer."""
        if not isinstance(v, int):
            raise ValueError(f"frame_index must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("frame_index cannot be negative")
        return v

    @field_validator("layer_id", mode="before")
    @classmethod
    def normalize_layer_id(cls, v: str | None) -> str | None:
        """Validate and normalize layer ID."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"layer_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("layer_id cannot be empty or whitespace-only")
        return stripped

    @field_validator("region_bounds", mode="before")
    @classmethod
    def validate_region_bounds(
        cls, v: tuple[int, int, int, int] | None
    ) -> tuple[int, int, int, int] | None:
        """Validate region bounds have non-negative dimensions."""
        if v is None:
            return None
        if len(v) != 4:
            raise ValueError("region_bounds must have exactly 4 values (x, y, width, height)")
        x, y, width, height = v
        if width < 0 or height < 0:
            raise ValueError("region_bounds width and height must be non-negative")
        return v


# ============================================================================
# Character Track
# ============================================================================


class CharacterTrack(BaseModel):
    """Represents one logical character tracked across manga frames/pages.

    This contract describes a character's identity and all its appearances.
    It does NOT perform character detection or recognition.

    Attributes:
        character_id: Unique identifier for this character
        display_name: Optional human-readable name
        appearances: Tuple of all appearances of this character
        palette_id: Optional reference to a character color palette
        metadata: Optional additional metadata

    Invariants:
        - character_id must be non-empty after trimming
        - appearances must be ordered by page_number
        - No duplicate (page_number, frame_index) pairs in appearances
        - appearances is immutable tuple

    Immutability:
        - CharacterTrack is NOT frozen (mutable for construction)
        - appearances is stored as tuple (immutable collection)
        - This is consistent with LayerDescriptor design
    """

    character_id: str = Field(
        min_length=1,
        description="Unique character identifier"
    )
    display_name: str | None = Field(
        default=None,
        description="Optional human-readable name"
    )
    appearances: tuple[CharacterAppearance, ...] = Field(
        default_factory=tuple,
        description="All appearances of this character"
    )
    palette_id: str | None = Field(
        default=None,
        description="Optional reference to character color palette"
    )
    metadata: CharacterTrackMetadata | None = Field(
        default=None,
        description="Optional additional metadata"
    )

    @field_validator("character_id", mode="before")
    @classmethod
    def normalize_character_id(cls, v: str) -> str:
        """Normalize character ID to trimmed non-empty string."""
        if not isinstance(v, str):
            raise ValueError(f"character_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("character_id cannot be empty or whitespace-only")
        return stripped

    @field_validator("appearances", mode="before")
    @classmethod
    def normalize_appearances(
        cls,
        v: list[CharacterAppearance] | tuple[CharacterAppearance, ...] | None
    ) -> tuple[CharacterAppearance, ...]:
        """Convert appearances list to tuple for immutability."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        return ()

    @model_validator(mode="after")
    def validate_appearance_ordering(self) -> CharacterTrack:
        """Validate appearances are ordered by page_number without duplicates.

        Invariant: Appearances must be provided in ascending order by page_number.
        Duplicate (page_number, frame_index) pairs are rejected to prevent ambiguity.
        """
        if self.appearances:
            page_indices = [(app.page_number, app.frame_index) for app in self.appearances]
            pages_only = [app.page_number for app in self.appearances]

            # Check ordering
            if pages_only != sorted(pages_only):
                raise ValueError("appearances must be ordered by page_number")

            # Check for duplicate (page, frame) pairs
            if len(page_indices) != len(set(page_indices)):
                raise ValueError(
                    "duplicate (page_number, frame_index) pairs are not allowed"
                )
        return self

    @property
    def appearance_count(self) -> int:
        """Get the number of appearances."""
        return len(self.appearances)

    def get_appearances_on_page(self, page_number: int) -> tuple[CharacterAppearance, ...]:
        """Get all appearances on a specific page.

        Args:
            page_number: The page number to filter by

        Returns:
            Tuple of appearances on that page
        """
        return tuple(
            app for app in self.appearances if app.page_number == page_number
        )


# ============================================================================
# Tracking Configuration
# ============================================================================


class TrackingConfig(BaseModel):
    """Configuration for character tracking operations.

    This contract defines parameters that control how character tracking
    is performed. The actual behavior depends on the implementation.

    Attributes:
        min_confidence: Minimum confidence threshold (0.0-1.0)
        track_across_pages: Whether to track character across pages
        merge_threshold: Optional threshold for merging character tracks
    """

    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    track_across_pages: bool = Field(
        default=True,
        description="Whether to track character across pages"
    )
    merge_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional threshold for merging character tracks"
    )


# ============================================================================
# Tracking Input
# ============================================================================


class CharacterTrackingInput(BaseModel):
    """Input contract for character tracking operations.

    This contract represents the parameters needed to perform character tracking.
    It contains REFERENCES and CONFIGURATION only.

    IMPORTANT: This contract does NOT perform character detection.
    Character tracking is performed by a future implementation.

    Attributes:
        sequence_id: Unique sequence identifier
        frame_count: Number of frames to track across
        page_count: Number of pages
        config: Optional tracking configuration

    Invariants:
        - sequence_id must be non-empty
        - frame_count must be >= 0
        - page_count must be >= 0
    """

    sequence_id: str = Field(
        min_length=1,
        description="Unique sequence identifier"
    )
    frame_count: int = Field(
        ge=0,
        description="Number of frames in the sequence"
    )
    page_count: int = Field(
        ge=0,
        description="Number of pages"
    )
    config: TrackingConfig | None = Field(
        default=None,
        description="Optional tracking configuration"
    )

    @field_validator("sequence_id", mode="before")
    @classmethod
    def normalize_sequence_id(cls, v: str) -> str:
        """Normalize sequence ID to trimmed non-empty string."""
        if not isinstance(v, str):
            raise ValueError(f"sequence_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("sequence_id cannot be empty or whitespace-only")
        return stripped


# ============================================================================
# Tracking Result
# ============================================================================


class CharacterTrackingResult(BaseModel):
    """Result of a character tracking operation.

    This contract represents the output of a character tracking operation,
    containing all character tracks and metadata about the operation.

    Character Tracking V1 defines contracts only.
    It does not detect, identify, recognize, or track characters in images.

    Deep Immutability:
    - This model is frozen/immutable
    - tracks is stored as tuple (immutable collection)
    - No caller-owned state can affect the result

    Determinism:
    - Same input produces equivalent output
    - No timestamps, random values, or environment state

    Attributes:
        sequence_id: Sequence that was tracked
        tracks: Tuple of character tracks
        status: Tracking operation status
        metadata: Optional result-level metadata

    Invariants:
        - No duplicate character_id values
        - tracks must be ordered by character_id
        - tracks is immutable tuple
    """

    model_config = {"frozen": True}

    sequence_id: str = Field(
        description="Sequence that was tracked"
    )
    tracks: tuple[CharacterTrack, ...] = Field(
        default_factory=tuple,
        description="Character tracks"
    )
    status: TrackingStatus = Field(
        default=TrackingStatus.NOT_PROCESSED,
        description="Tracking operation status"
    )
    metadata: CharacterTrackMetadata | None = Field(
        default=None,
        description="Optional result-level metadata"
    )

    @field_validator("tracks", mode="before")
    @classmethod
    def normalize_tracks(
        cls,
        v: list[CharacterTrack] | tuple[CharacterTrack, ...] | None
    ) -> tuple[CharacterTrack, ...]:
        """Convert tracks list to tuple for immutability."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        return ()

    @model_validator(mode="after")
    def validate_track_ordering(self) -> CharacterTrackingResult:
        """Validate tracks are ordered by character_id without duplicates.

        Invariant: Tracks must be provided in ascending order by character_id.
        Duplicate character_id values are rejected to prevent ambiguity.
        """
        if self.tracks:
            character_ids = [track.character_id for track in self.tracks]
            if character_ids != sorted(character_ids):
                raise ValueError("tracks must be ordered by character_id")
            if len(character_ids) != len(set(character_ids)):
                raise ValueError("duplicate character_id values are not allowed")
        return self

    @property
    def track_count(self) -> int:
        """Get the number of character tracks."""
        return len(self.tracks)

    def get_track(self, character_id: str) -> CharacterTrack | None:
        """Get track by character_id.

        Args:
            character_id: The character ID to search for

        Returns:
            CharacterTrack if found, None otherwise
        """
        for track in self.tracks:
            if track.character_id == character_id:
                return track
        return None

    def get_tracks_with_palette(self, palette_id: str) -> tuple[CharacterTrack, ...]:
        """Get all tracks that reference a specific palette.

        Args:
            palette_id: The palette ID to filter by

        Returns:
            Tuple of matching tracks
        """
        return tuple(
            track for track in self.tracks if track.palette_id == palette_id
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Enums
    "TrackingStatus",
    # Models
    "CharacterTrackMetadata",
    "CharacterAppearance",
    "CharacterTrack",
    "TrackingConfig",
    "CharacterTrackingInput",
    "CharacterTrackingResult",
]
