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

from tools.frame.models import FrameTransform, InterpolationType

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
# Transform Input Contracts
# ============================================================================


@dataclass(frozen=True, slots=True)
class CharacterTransformInput:
    """Transform input for a character appearance.

    Provides FrameTransform data for a specific character at a specific frame.
    This contract defines HOW to animate (transform parameters) for a character
    at a specific frame.

    Identity: References binding via (character_id, frame_index) tuple.

    Attributes:
        character_id: Character identifier (must be non-empty trimmed string)
        frame_index: Frame number (must be >= 0)
        transform: FrameTransform data for this frame
        interpolation: How to interpolate from this keyframe (default: LINEAR)

    Note:
        This contract is separate from CharacterAnimationBinding to maintain
        separation of concerns:
        - CharacterAnimationBinding defines structural identity (WHO, WHERE)
        - CharacterTransformInput defines animation data (HOW)

    Example:
        >>> from tools.frame.models import FrameTransform
        >>> transform = FrameTransform(position_x=100, scale=1.5)
        >>> input = CharacterTransformInput(
        ...     character_id="hero",
        ...     frame_index=5,
        ...     transform=transform,
        ... )
    """

    character_id: str
    frame_index: int
    transform: FrameTransform
    interpolation: InterpolationType | None = None

    def __post_init__(self) -> None:
        """Validate and normalize after initialization."""
        # Validate and normalize character_id
        if not isinstance(self.character_id, str):
            raise ValueError(
                f"character_id must be string, got {type(self.character_id).__name__}"
            )
        stripped = self.character_id.strip()
        if not stripped:
            raise ValueError("character_id cannot be empty or whitespace-only")

        # Trim character_id to normalized form
        object.__setattr__(self, "character_id", stripped)

        # Validate frame_index
        if not isinstance(self.frame_index, int):
            raise ValueError(
                f"frame_index must be int, got {type(self.frame_index).__name__}"
            )
        if self.frame_index < 0:
            raise ValueError("frame_index cannot be negative")

        # Normalize interpolation to LINEAR if None
        if self.interpolation is None:
            object.__setattr__(self, "interpolation", InterpolationType.LINEAR)

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "character_id": self.character_id,
            "frame_index": self.frame_index,
            "transform": self.transform.model_dump(),
            "interpolation": self.interpolation.value,
        }


@dataclass(frozen=True)
class CharacterTransformInputSet:
    """Collection of transform inputs for a sequence.

    Immutable container for multiple CharacterTransformInput objects.
    Provides aggregation and validation for transform input collections.

    Attributes:
        transforms: Tuple of transform inputs (sorted by character_id, frame_index)
        default_interpolation: Fallback interpolation type

    Invariants:
        - No duplicate (character_id, frame_index) pairs
        - Transforms are sorted deterministically

    Example:
        >>> from tools.frame.models import FrameTransform
        >>> inputs = [
        ...     CharacterTransformInput("hero", 0, FrameTransform(position_x=0)),
        ...     CharacterTransformInput("hero", 10, FrameTransform(position_x=100)),
        ... ]
        >>> input_set = CharacterTransformInputSet(transforms=inputs)
    """

    transforms: tuple[CharacterTransformInput, ...]
    default_interpolation: InterpolationType | None = None

    def __post_init__(self) -> None:
        """Validate and normalize after initialization."""
        # Set default interpolation
        if self.default_interpolation is None:
            object.__setattr__(self, "default_interpolation", InterpolationType.LINEAR)

        # Normalize transforms to tuple
        if isinstance(self.transforms, list):
            object.__setattr__(self, "transforms", tuple(self.transforms))

        # Validate for duplicates and sort
        if self.transforms:
            seen: set[tuple[str, int]] = set()
            sorted_transforms: list[CharacterTransformInput] = []

            for t in self.transforms:
                key = (t.character_id, t.frame_index)
                if key in seen:
                    raise ValueError(
                        f"duplicate (character_id, frame_index) pair: "
                        f"('{t.character_id}', {t.frame_index})"
                    )
                seen.add(key)
                sorted_transforms.append(t)

            # Sort by (character_id, frame_index)
            sorted_transforms.sort(key=lambda t: (t.character_id, t.frame_index))
            object.__setattr__(self, "transforms", tuple(sorted_transforms))

    def model_dump(self) -> dict:
        """Serialize to dictionary."""
        return {
            "transforms": [t.model_dump() for t in self.transforms],
            "default_interpolation": self.default_interpolation.value,
        }


# ============================================================================
# Animation Clip Creation
# ============================================================================


def _build_clip_id(character_id: str, layer_id: str | None) -> str:
    """Build collision-safe clip_id from character_id and layer_id.

    Uses escaped underscores to prevent collisions when character_id or layer_id
    contain underscores.

    Encoding rules:
    - Underscores in inputs are escaped as "__" (double underscore)
    - Separator is a single underscore "_"
    - None layer_id is represented as "default"

    This guarantees bijective mapping: different (character_id, layer_id) pairs
    always produce different clip_ids.

    Examples:
        ("hero", "1")      -> "hero_1"
        ("hero", "1_2")    -> "hero_1__2"
        ("hero_1", "2")    -> "hero__1_2"
        ("hero", None)     -> "hero_default"

    Args:
        character_id: The character identifier
        layer_id: The layer identifier (or None for default)

    Returns:
        Collision-safe clip_id string
    """
    # Escape underscores in both components
    encoded_char = character_id.replace("_", "__")
    encoded_layer = "default" if layer_id is None else layer_id.replace("_", "__")
    # Join with single underscore separator
    return f"{encoded_char}_{encoded_layer}"


def create_animation_clips(
    animation_output: CharacterAnimationOutput,
    transform_inputs: CharacterTransformInputSet,
) -> tuple:
    """Create AnimationClip objects from character animation bindings and transforms.

    Combines structural identity (from CharacterAnimationOutput) with animation
    data (from CharacterTransformInputSet) to produce AnimationClip objects.

    Grouping:
        One clip per unique (character_id, layer_id) pair.
        Multiple bindings for the same (character_id, layer_id) across different
        frames produce one clip spanning the frame range.

    clip_id Derivation:
        Uses _build_clip_id() for collision-safe encoding.
        Underscores in character_id/layer_id are escaped before joining.
        None layer_id is represented as "default".

    Transform Lookup:
        For each binding, look up transform by (character_id, frame_index).
        If found, create AnimationKeyframe with the transform.
        If not found, no keyframe is created (clip uses default_transform).

    Default Transform:
        FrameTransform() (identity transform with all defaults).
        Applied at frames without explicit keyframes.

    Duplicate Policy:
        Duplicate (character_id, layer_id, frame_index) bindings raise ValueError.
        Duplicate transform inputs are already rejected by CharacterTransformInputSet.

    Palette:
        palette_id from CharacterAnimationBinding is NOT included in clips.
        Palette remains separate metadata.

    Determinism:
        Clips are sorted by clip_id.
        Keyframes within each clip are sorted by frame_index.
        Same input produces identical output.

    Args:
        animation_output: CharacterAnimationOutput containing structural bindings
        transform_inputs: CharacterTransformInputSet containing animation transforms

    Returns:
        Tuple of AnimationClip objects, sorted by clip_id

    Raises:
        ValueError: If duplicate (character_id, layer_id, frame_index) found

    Example:
        >>> bindings = (binding_for_hero_layer1, binding_for_villain_layer1)
        >>> transforms = CharacterTransformInputSet(transforms=[...])
        >>> clips = create_animation_clips(bindings, transforms)
    """
    from tools.frame.animation import AnimationClip, AnimationKeyframe
    from tools.frame.models import FrameTransform

    # Build transform lookup: (character_id, frame_index) -> CharacterTransformInput
    transform_map: dict[tuple[str, int], CharacterTransformInput] = {}
    for t in transform_inputs.transforms:
        key = (t.character_id, t.frame_index)
        transform_map[key] = t

    # Group bindings by (character_id, layer_id)
    clip_groups: dict[tuple[str, str | None], list[CharacterAnimationBinding]] = {}

    for binding in animation_output.bindings:
        char_id = binding.target.character_id
        layer_id = binding.target.layer_id
        group_key = (char_id, layer_id)

        if group_key not in clip_groups:
            clip_groups[group_key] = []

        # Check for duplicate (character_id, layer_id, frame_index) within group
        for existing in clip_groups[group_key]:
            if existing.frame_index == binding.frame_index:
                raise ValueError(
                    f"duplicate binding for (character_id='{char_id}', "
                    f"layer_id='{layer_id}', frame_index={binding.frame_index})"
                )

        clip_groups[group_key].append(binding)

    # Create clips
    clips: list = []

    for (char_id, layer_id), bindings in clip_groups.items():
        # Derive collision-safe clip_id
        clip_id = _build_clip_id(char_id, layer_id)

        # Determine frame range
        frame_indices = [b.frame_index for b in bindings]
        start_frame = min(frame_indices)
        end_frame = max(frame_indices)

        # Create keyframes from transforms
        keyframes: list = []

        for binding in bindings:
            transform_key = (binding.target.character_id, binding.frame_index)
            transform_input = transform_map.get(transform_key)

            if transform_input is not None:
                keyframe = AnimationKeyframe(
                    frame_index=transform_input.frame_index,
                    transform=transform_input.transform,
                    interpolation=transform_input.interpolation
                    or transform_inputs.default_interpolation,
                )
                keyframes.append(keyframe)

        # Sort keyframes by frame_index
        keyframes.sort(key=lambda k: k.frame_index)

        clip = AnimationClip(
            clip_id=clip_id,
            start_frame=start_frame,
            end_frame=end_frame,
            keyframes=keyframes,
            default_transform=FrameTransform(),
        )
        clips.append(clip)

    # Sort clips by clip_id for deterministic output
    clips.sort(key=lambda c: c.clip_id)

    return tuple(clips)


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
        # Validate frame index (handles negative and out-of-bounds)
        _validate_frame_index(ref.frame_index, max_frame)

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
    # Transform Input Contracts
    "CharacterTransformInput",
    "CharacterTransformInputSet",
    # Functions
    "build_character_animation_bindings",
    "create_animation_clips",
]
