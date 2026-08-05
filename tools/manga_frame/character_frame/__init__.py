"""Character Frame integration contracts for manga to frame pipeline.

This module defines the integration boundary between character tracking contracts
and frame data structures.

IMPORTANT: Character → Frame integration V1 is a structural contract.
It does not detect, recognize, track, segment, or process characters
in images.

Architecture:
    tools/manga/  -->  tools/manga_frame/
                            ├── character_tracking/  -->  character_frame/
                            ├── layer_extraction/                      (THIS MODULE)
                            └── manga_frame/                             ↓
                                                                   tools/frame/

The contracts define:
- Input contracts for mapping character tracking into frame structures
- Output contracts with mapping metadata
- Structural validation for frame/layer references
- Palette association logic

This module does NOT:
- Perform character detection
- Perform character recognition
- Load or decode images
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
- Modify frame models directly
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

from tools.frame.models import FrameSequence
from tools.frame.palette import CharacterColorPalette
from tools.manga_frame.character_tracking import (
    CharacterAppearance,
    CharacterTrackingResult,
)

# ============================================================================
# Integration Metadata
# ============================================================================


class CharacterFrameMappingMetadata(BaseModel):
    """Metadata for character to frame mapping.

    This contract stores information about the mapping operation
    without modifying the original FrameSequence structure.

    Attributes:
        characters_mapped: Number of unique characters successfully mapped
        appearances_mapped: Total number of appearances mapped
        characters_unmapped: Number of characters without valid frame references
        appearances_unmapped: Number of appearances without valid frame references
        palettes_applied: Number of palettes successfully associated
        palettes_missing: Number of characters without matching palettes
    """

    model_config = {"frozen": True}

    characters_mapped: int = Field(
        ge=0,
        description="Number of unique characters successfully mapped"
    )
    appearances_mapped: int = Field(
        ge=0,
        description="Total number of appearances mapped"
    )
    characters_unmapped: int = Field(
        ge=0,
        description="Number of characters without valid frame references"
    )
    appearances_unmapped: int = Field(
        ge=0,
        description="Number of appearances without valid frame references"
    )
    palettes_applied: int = Field(
        ge=0,
        description="Number of palettes successfully associated"
    )
    palettes_missing: int = Field(
        ge=0,
        description="Number of characters without matching palettes"
    )


# ============================================================================
# Reference Validation
# ============================================================================


@dataclass(frozen=True)
class CharacterFrameReference:
    """Validated reference from character to frame.

    This is an immutable representation of a validated character appearance
    mapping to a specific frame and optionally a specific layer.

    Attributes:
        character_id: The character's unique identifier
        frame_index: The target frame index
        layer_index: Optional layer index within the frame
        palette_id: Optional associated palette ID
    """

    character_id: str
    frame_index: int
    layer_index: int | None
    palette_id: str | None


# ============================================================================
# Input Contract
# ============================================================================


class CharacterFrameInput(BaseModel):
    """Input contract for mapping character tracking into frame structures.

    This contract represents the parameters needed to map character tracking
    results into frame structures.

    Attributes:
        tracking_result: Character tracking result to map
        frame_sequence: Frame sequence to map into
        character_palettes: Optional mapping of character_id -> CharacterColorPalette
        skip_invalid_references: If True, skip invalid references instead of failing

    Note:
        This contract does NOT modify the FrameSequence directly.
        It provides validation and produces an output contract with mapping metadata.
    """

    tracking_result: CharacterTrackingResult = Field(
        description="Character tracking result to map"
    )
    frame_sequence: FrameSequence = Field(
        description="Frame sequence to map into"
    )
    character_palettes: dict[str, CharacterColorPalette] | None = Field(
        default=None,
        description="Optional mapping of character_id -> CharacterColorPalette"
    )
    skip_invalid_references: bool = Field(
        default=False,
        description="If True, skip invalid references instead of failing"
    )

    @field_validator("character_palettes", mode="before")
    @classmethod
    def normalize_palettes(
        cls,
        v: dict[str, CharacterColorPalette] | None
    ) -> dict[str, CharacterColorPalette] | None:
        """Normalize palette keys to trimmed strings."""
        if v is None:
            return None
        if not isinstance(v, dict):
            return None
        return {k.strip(): val for k, val in v.items() if k.strip()}


# ============================================================================
# Output Contract
# ============================================================================


@dataclass(frozen=True)
class CharacterFrameOutput:
    """Output of character to frame mapping operation.

    Immutable result containing the mapping metadata and validated references.

    Attributes:
        sequence: Original frame sequence (NOT modified)
        tracking_result: Original tracking result (preserved)
        references: Tuple of validated character -> frame references
        metadata: Mapping metadata
        palette_associations: Tuple of (character_id, palette) pairs that were associated

    Invariants:
        - All references have been validated against the frame sequence
        - No duplicate (character_id, frame_index) pairs
        - References are ordered by character_id then frame_index
    """

    sequence: FrameSequence
    tracking_result: CharacterTrackingResult
    references: tuple[CharacterFrameReference, ...]
    metadata: CharacterFrameMappingMetadata
    palette_associations: tuple[tuple[str, CharacterColorPalette], ...]


# ============================================================================
# Validation Helpers
# ============================================================================


def _get_valid_frame_indices(sequence: FrameSequence) -> set[int]:
    """Get set of valid frame indices from sequence."""
    return {frame.frame_index for frame in sequence.frames}


def _get_layer_indices_for_frame(
    sequence: FrameSequence,
    frame_index: int
) -> dict[str, int]:
    """Get layer_id -> layer_index mapping for a specific frame.

    Returns empty dict if frame not found.
    """
    for frame in sequence.frames:
        if frame.frame_index == frame_index:
            return {
                layer.layer_id: layer.layer_index
                for layer in frame.layers
                if layer.layer_id is not None
            }
    return {}


def _validate_appearance(
    appearance: CharacterAppearance,
    valid_frame_indices: set[int],
    layer_indices: dict[str, int],
    skip_invalid: bool
) -> tuple[bool, str | None]:
    """Validate a single appearance reference.

    Returns:
        (is_valid, error_message)
    """
    # Check frame index
    if appearance.frame_index not in valid_frame_indices:
        if skip_invalid:
            return False, None
        return False, f"frame_index {appearance.frame_index} not in sequence"

    # Check layer reference if present
    if appearance.layer_id is not None:
        if appearance.layer_id not in layer_indices:
            if skip_invalid:
                return False, None
            return False, f"layer_id '{appearance.layer_id}' not found in frame {appearance.frame_index}"

    return True, None


# ============================================================================
# Main Mapping Function
# ============================================================================


def convert_character_tracking_to_frames(
    input_contract: CharacterFrameInput,
) -> CharacterFrameOutput:
    """Map character tracking results into frame structure references.

    This function validates character tracking references against a frame sequence
    and produces an output contract with mapping metadata.

    Mapping Rules:
    - CharacterTrack.character_id -> CharacterFrameReference.character_id
    - CharacterAppearance.frame_index -> validated against FrameSequence
    - CharacterAppearance.layer_id -> validated against Frame.layers
    - CharacterTrack.palette_id -> associated with CharacterColorPalette

    Validation:
    - All frame_index values must exist in the frame sequence
    - All layer_id references must exist in the referenced frame
    - Duplicate character IDs in result are rejected by CharacterTrackingResult
    - Duplicate appearances are rejected by CharacterTrack

    Immutability:
    - Original sequence and tracking_result are preserved
    - Output is a frozen dataclass
    - References tuple is immutable

    Determinism:
    - Same input produces same output
    - References are sorted deterministically
    - No random values, timestamps, or environment state

    Args:
        input_contract: Input contract with tracking result and frame sequence

    Returns:
        CharacterFrameOutput with validated references and mapping metadata

    Raises:
        ValueError: If validation fails and skip_invalid_references is False
    """
    tracking = input_contract.tracking_result
    sequence = input_contract.frame_sequence
    palettes = input_contract.character_palettes or {}
    skip_invalid = input_contract.skip_invalid_references

    # Get valid frame indices
    valid_frame_indices = _get_valid_frame_indices(sequence)

    # Track statistics
    characters_mapped = 0
    appearances_mapped = 0
    characters_unmapped = 0
    appearances_unmapped = 0
    palettes_applied = 0
    palettes_missing = 0

    # Collect validated references
    references: list[CharacterFrameReference] = []
    errors: list[str] = []

    # Process each character track
    for track in tracking.tracks:
        has_valid_appearance = False

        # Check palette availability
        palette_id = track.palette_id
        if palette_id and palette_id in palettes:
            palettes_applied += 1
        elif palette_id:
            palettes_missing += 1

        # Process each appearance
        for appearance in track.appearances:
            # Get layer indices for this frame
            layer_indices = _get_layer_indices_for_frame(sequence, appearance.frame_index)

            # Validate
            is_valid, error = _validate_appearance(
                appearance,
                valid_frame_indices,
                layer_indices,
                skip_invalid,
            )

            if is_valid:
                # Create validated reference
                layer_index = None
                if appearance.layer_id and appearance.layer_id in layer_indices:
                    layer_index = layer_indices[appearance.layer_id]

                ref = CharacterFrameReference(
                    character_id=track.character_id,
                    frame_index=appearance.frame_index,
                    layer_index=layer_index,
                    palette_id=palette_id,
                )
                references.append(ref)
                appearances_mapped += 1
                has_valid_appearance = True
            else:
                appearances_unmapped += 1
                if error:
                    errors.append(f"{track.character_id}: {error}")

        if has_valid_appearance:
            characters_mapped += 1
        else:
            characters_unmapped += 1

    # Check for errors if not skipping
    if errors and not skip_invalid:
        raise ValueError(f"Invalid character references: {'; '.join(errors)}")

    # Sort references deterministically
    sorted_references = tuple(
        sorted(
            references,
            key=lambda r: (r.character_id, r.frame_index)
        )
    )

    # Build palette associations
    palette_associations: list[tuple[str, CharacterColorPalette]] = []
    seen_characters = set()
    for track in tracking.tracks:
        if track.character_id not in seen_characters:
            seen_characters.add(track.character_id)
            pal_id = track.palette_id
            if pal_id and pal_id in palettes:
                palette_associations.append((track.character_id, palettes[pal_id]))

    palette_associations = tuple(sorted(palette_associations))

    # Create metadata
    metadata = CharacterFrameMappingMetadata(
        characters_mapped=characters_mapped,
        appearances_mapped=appearances_mapped,
        characters_unmapped=characters_unmapped,
        appearances_unmapped=appearances_unmapped,
        palettes_applied=palettes_applied,
        palettes_missing=palettes_missing,
    )

    return CharacterFrameOutput(
        sequence=sequence,
        tracking_result=tracking,
        references=sorted_references,
        metadata=metadata,
        palette_associations=palette_associations,
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Models
    "CharacterFrameMappingMetadata",
    "CharacterFrameInput",
    "CharacterFrameOutput",
    # Helpers
    "CharacterFrameReference",
    # Functions
    "convert_character_tracking_to_frames",
]
