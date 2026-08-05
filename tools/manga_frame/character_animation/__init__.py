"""Character Animation Integration Contracts.

This module defines the structural integration boundary between character tracking
output and animation data structures.

IMPORTANT: Character → Animation Integration V1 defines structural bindings only.
It does not generate animation, keyframes, transforms, interpolation,
motion, or rendered frames.

Architecture:
    tools/manga/
            ↓
    tools/manga_frame/
            ├── layer_extraction/
            ├── character_tracking/
            ├── character_frame/
            └── character_animation/  (THIS MODULE)
                            ↓
                    tools/frame/animation/

The contracts define:
- Character animation target identity
- Binding between character references and animation targets
- Input/output contracts for structural mapping
- Validation for structural references only

This module does NOT:
- Generate keyframes
- Interpolate transforms
- Calculate motion
- Generate animation frames
- Perform easing
- Modify AnimationTimeline
- Render anything
- Access GPU
- Access network
- Generate random values
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Animation Target Identity
# ============================================================================


@dataclass(frozen=True, slots=True)
class CharacterAnimationTarget:
    """Immutable target identity for character animation.

    This contract identifies what entity in the animation system a character
    should be bound to.

    Attributes:
        character_id: Unique character identifier from tracking
        layer_id: Layer identifier from frame structure
        sequence_id: Sequence identifier for context

    Note:
        This is a frozen dataclass used as an identity key.
        It does NOT contain animation data.
    """

    character_id: str
    layer_id: str | None
    sequence_id: str

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "character_id": self.character_id,
            "layer_id": self.layer_id,
            "sequence_id": self.sequence_id,
        }


# ============================================================================
# Animation Binding
# ============================================================================


@dataclass(frozen=True, slots=True)
class CharacterAnimationBinding:
    """Structural binding from character to animation target.

    Maps one character-frame reference to its animation target identity
    and provides metadata for future animation construction.

    Attributes:
        target: The animation target identity
        frame_index: Frame index in the sequence
        palette_id: Optional palette identifier for colorization

    Note:
        This is a structural binding ONLY.
        No animation data (keyframes, transforms, interpolation) is generated.
    """

    target: CharacterAnimationTarget
    frame_index: int
    palette_id: str | None

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "target": self.target.model_dump(),
            "frame_index": self.frame_index,
            "palette_id": self.palette_id,
        }


# ============================================================================
# Animation Metadata
# ============================================================================


class CharacterAnimationMetadata(BaseModel):
    """Metadata for character animation binding operation.

    Immutable metadata about the binding operation.

    Attributes:
        bindings_created: Number of structural bindings created
        characters_bound: Number of unique characters with bindings
        palettes_available: Number of characters with palette associations
        palettes_missing: Number of characters without palette associations
    """

    model_config = {"frozen": True}

    bindings_created: int = Field(
        ge=0,
        description="Number of structural bindings created"
    )
    characters_bound: int = Field(
        ge=0,
        description="Number of unique characters with bindings"
    )
    palettes_available: int = Field(
        ge=0,
        description="Number of characters with palette associations"
    )
    palettes_missing: int = Field(
        ge=0,
        description="Number of characters without palette associations"
    )


# ============================================================================
# Input Contract
# ============================================================================


class CharacterAnimationInput(BaseModel):
    """Input contract for character animation binding.

    This contract represents the parameters needed to bind character
    tracking references to animation targets.

    Attributes:
        sequence_id: Sequence identifier (must match source)
        frame_count: Number of frames in the sequence
        bindings: Tuple of CharacterFrameReference to bind

    Note:
        This contract does NOT perform animation generation.
        It only creates structural bindings for future animation.
    """

    sequence_id: str = Field(
        min_length=1,
        description="Sequence identifier"
    )
    frame_count: int = Field(
        ge=0,
        description="Number of frames in the sequence"
    )
    palette_associations: tuple[tuple[str, str], ...] = Field(
        default_factory=tuple,
        description="(character_id, palette_id) pairs"
    )

    @field_validator("sequence_id", mode="before")
    @classmethod
    def normalize_sequence_id(cls, v: str) -> str:
        """Validate and normalize sequence ID."""
        if not isinstance(v, str):
            raise ValueError(f"sequence_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("sequence_id cannot be empty or whitespace-only")
        return stripped

    @field_validator("palette_associations", mode="before")
    @classmethod
    def normalize_palettes(
        cls,
        v: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None
    ) -> tuple[tuple[str, str], ...]:
        """Normalize palette associations to tuple."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        return ()


# ============================================================================
# Output Contract
# ============================================================================


@dataclass(frozen=True)
class CharacterAnimationOutput:
    """Output of character animation binding operation.

    Immutable result containing structural bindings for animation construction.

    Attributes:
        sequence_id: Sequence that was processed
        bindings: Tuple of structural character-to-animation bindings
        metadata: Binding operation metadata

    Note:
        This contract defines WHO should be animated and WHERE,
        but does NOT define HOW to animate (keyframes, transforms, etc.).
        The HOW belongs to tools/frame/animation.
    """

    sequence_id: str
    bindings: tuple[CharacterAnimationBinding, ...]
    metadata: CharacterAnimationMetadata


# ============================================================================
# Validation Helpers
# ============================================================================


def _validate_frame_index(frame_index: int, max_frame: int) -> int:
    """Validate frame index is within range.

    Args:
        frame_index: Frame index to validate
        max_frame: Maximum valid frame index (inclusive)

    Returns:
        Validated frame index

    Raises:
        ValueError: If frame_index is negative or exceeds max_frame
    """
    if not isinstance(frame_index, int):
        raise ValueError(f"frame_index must be int, got {type(frame_index).__name__}")
    if frame_index < 0:
        raise ValueError("frame_index cannot be negative")
    if frame_index > max_frame:
        raise ValueError(f"frame_index {frame_index} exceeds frame_count {max_frame + 1}")
    return frame_index


# ============================================================================
# Main Binding Function
# ============================================================================


def build_character_animation_bindings(
    input_contract: CharacterAnimationInput,
    references: tuple,
) -> CharacterAnimationOutput:
    """Build structural bindings from character references to animation targets.

    This function creates the structural contract needed by a future animation
    implementation. It does NOT generate animation.

    Mapping Rules:
    - CharacterFrameReference.character_id -> CharacterAnimationTarget.character_id
    - CharacterFrameReference.layer_index -> str(CharacterAnimationTarget.layer_id)
    - CharacterFrameReference.frame_index -> CharacterAnimationBinding.frame_index
    - Palette associations -> preserved for colorization

    What this function does NOT do:
    - Generate keyframes
    - Interpolate transforms
    - Calculate motion
    - Create AnimationClip
    - Create AnimationKeyframe
    - Modify AnimationTimeline

    Immutability:
    - Output is frozen
    - Bindings tuple is immutable
    - Original references are preserved

    Determinism:
    - Same input produces same output
    - Bindings are sorted by (character_id, frame_index)
    - No random values, timestamps, or environment state

    Args:
        input_contract: Input contract with sequence context
        references: Tuple of CharacterFrameReference from CharacterFrameOutput

    Returns:
        CharacterAnimationOutput with structural bindings

    Raises:
        ValueError: If validation fails
    """
    sequence_id = input_contract.sequence_id
    max_frame = input_contract.frame_count - 1
    palette_map: dict[str, str] = {}

    # Build palette map from associations
    for char_id, palette_id in input_contract.palette_associations:
        palette_map[char_id] = palette_id

    # Track statistics
    bindings_created = 0
    characters_bound: set[str] = set()
    palettes_available = 0
    palettes_missing = 0

    # Collect bindings
    bindings: list[CharacterAnimationBinding] = []

    for ref in references:
        # Validate frame index
        if ref.frame_index > max_frame:
            raise ValueError(
                f"frame_index {ref.frame_index} exceeds frame_count {input_contract.frame_count}"
            )

        # Create target
        # Note: layer_index is Z-order int from Frame, converted to str for target
        target = CharacterAnimationTarget(
            character_id=ref.character_id,
            layer_id=str(ref.layer_index) if ref.layer_index is not None else None,
            sequence_id=sequence_id,
        )

        # Get palette ID for this character
        palette_id = palette_map.get(ref.character_id)

        # Create binding
        binding = CharacterAnimationBinding(
            target=target,
            frame_index=ref.frame_index,
            palette_id=palette_id,
        )
        bindings.append(binding)
        bindings_created += 1
        characters_bound.add(ref.character_id)

        # Track palette availability
        if palette_id:
            palettes_available += 1
        else:
            palettes_missing += 1

    # Sort bindings deterministically: by (character_id, frame_index)
    sorted_bindings = tuple(
        sorted(
            bindings,
            key=lambda b: (b.target.character_id, b.frame_index)
        )
    )

    # Create metadata
    metadata = CharacterAnimationMetadata(
        bindings_created=bindings_created,
        characters_bound=len(characters_bound),
        palettes_available=palettes_available,
        palettes_missing=palettes_missing,
    )

    return CharacterAnimationOutput(
        sequence_id=sequence_id,
        bindings=sorted_bindings,
        metadata=metadata,
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Identity
    "CharacterAnimationTarget",
    # Binding
    "CharacterAnimationBinding",
    # Metadata
    "CharacterAnimationMetadata",
    # Contracts
    "CharacterAnimationInput",
    "CharacterAnimationOutput",
    # Functions
    "build_character_animation_bindings",
]
