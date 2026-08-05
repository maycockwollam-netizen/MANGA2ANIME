# Character Frame Integration Contracts

## Purpose

This document defines the integration contracts for mapping character tracking results into frame data structures in the MANGA2ANIME pipeline.

**Character → Frame integration V1 is a structural contract.**
**It does not detect, recognize, track, segment, or process characters in images.**

This module defines the boundary between character tracking contracts and frame structures.

## Scope

The contracts define:
- Input contracts for mapping character tracking into frame structures
- Output contracts with mapping metadata
- Structural validation for frame/layer references
- Palette association logic

## Architecture

```
tools/manga/
        |
        v
tools/manga_frame/
        ├── character_tracking/  -->  character_frame/
        ├── layer_extraction/                      (THIS MODULE)
        └── manga_frame/                             |
                                                   v
                                              tools/frame/
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `tools/manga/` | Parse manga sources, page metadata |
| `tools/manga_frame/character_tracking/` | Character tracking contracts |
| `tools/manga_frame/character_frame/` | Map tracking to frame structures |
| `tools/frame/` | Frame/animation data contracts |

## Public API

### Models

#### CharacterFrameMappingMetadata

Immutable metadata about the mapping operation.

```python
@dataclass(frozen=True)
class CharacterFrameMappingMetadata(BaseModel):
    """Metadata for character to frame mapping."""

    model_config = {"frozen": True}

    characters_mapped: int
    appearances_mapped: int
    characters_unmapped: int
    appearances_unmapped: int
    palettes_applied: int
    palettes_missing: int
```

#### CharacterFrameReference

Validated reference from character to frame.

```python
@dataclass(frozen=True)
class CharacterFrameReference:
    """Validated reference from character to frame."""

    character_id: str
    frame_index: int
    layer_index: int | None
    palette_id: str | None
```

#### CharacterFrameInput

Input contract for mapping.

```python
class CharacterFrameInput(BaseModel):
    """Input contract for mapping character tracking into frame structures."""

    tracking_result: CharacterTrackingResult
    frame_sequence: FrameSequence
    character_palettes: dict[str, CharacterColorPalette] | None
    skip_invalid_references: bool = False
```

#### CharacterFrameOutput

Immutable output contract.

```python
@dataclass(frozen=True)
class CharacterFrameOutput:
    """Output of character to frame mapping operation."""

    sequence: FrameSequence
    tracking_result: CharacterTrackingResult
    references: tuple[CharacterFrameReference, ...]
    metadata: CharacterFrameMappingMetadata
    palette_associations: tuple[tuple[str, CharacterColorPalette], ...]
```

### Functions

#### convert_character_tracking_to_frames

```python
def convert_character_tracking_to_frames(
    input_contract: CharacterFrameInput,
) -> CharacterFrameOutput:
    """Map character tracking results into frame structure references."""
```

## Mapping Rules

| Character Tracking Field | Frame Structure Field | Notes |
|-------------------------|----------------------|-------|
| `CharacterTrack.character_id` | `CharacterFrameReference.character_id` | Preserved |
| `CharacterAppearance.frame_index` | Validated against `FrameSequence` | Must exist in sequence |
| `CharacterAppearance.layer_id` | **Validated, then discarded** | Resolved to numeric index; see Layer Identifier Semantics below |
| `CharacterAppearance.region_bounds` | Metadata only | Not used for structural mapping |
| `CharacterTrack.palette_id` | Associated with `CharacterColorPalette` | Lookup in provided palettes |

### Layer Identifier Semantics

**Important:** There is a semantic boundary between `character_tracking` and `character_frame`:

| Source | Identifier Type | Example |
|--------|----------------|---------|
| `CharacterAppearance.layer_id` | Stable semantic identifier (string) | `"character_layer_01"` |
| `FrameLayer.layer_index` | Numeric z-order position (integer) | `3` |

**What happens during mapping:**

1. `CharacterAppearance.layer_id` (string) is validated to exist in the referenced `Frame.layers`
2. The identifier is resolved to its corresponding `layer_index` (integer)
3. The original `layer_id` string is **intentionally discarded**
4. `CharacterFrameReference.layer_index` (integer) is stored in the output

**Why this is intentional:**

- `character_tracking` operates at the manga layer abstraction where `layer_id` is a semantic identifier
- `character_frame` operates at the frame data structure where `FrameLayer` uses numeric z-order
- Preserving the original string identifier would require modifying `CharacterFrameReference` and breaking the frame-level semantics
- Downstream consumers working at the frame level should use `layer_index` for structural operations

**Consequence:**

Downstream consumers **cannot reconstruct the original semantic `layer_id`** from `CharacterFrameReference.layer_index` alone. If the original identifier is required, it must be preserved earlier in the pipeline (e.g., in character tracking results).

## Validation Rules

| Validation | Behavior |
|-----------|----------|
| `frame_index` not in sequence | Reject (or skip if `skip_invalid_references=True`) |
| `layer_id` not in frame | Reject (or skip if `skip_invalid_references=True`) |
| Duplicate character IDs | Rejected by `CharacterTrackingResult` |
| Duplicate appearances | Rejected by `CharacterTrack` |

## Palette Behavior

| Scenario | Behavior |
|---------|----------|
| Palette provided and matches `palette_id` | Associated successfully |
| Palette not provided | Reported as missing, not invented |
| Palette ID references non-existent palette | Reported as missing |
| Multiple characters with same palette | Each association recorded separately |

**Important:** This module does NOT generate or infer palettes. It only associates pre-existing palettes.

## Immutability Guarantees

| Contract | Frozen | Collection Type |
|----------|--------|-----------------|
| `CharacterFrameOutput` | ✅ Yes | N/A (dataclass) |
| `CharacterFrameMappingMetadata` | ✅ Yes | N/A (Pydantic frozen) |
| `CharacterFrameReference` | ✅ Yes | N/A (dataclass frozen) |
| `CharacterFrameInput` | ❌ No | dict is normalized on input |

## Serialization

The output contracts support serialization:

```python
# Metadata serialization
data = metadata.model_dump()

# Reference comparison
ref1 == ref2  # True if all fields equal
```

## Determinism

The integration is deterministic:

- Same input produces same output
- References are sorted by `(character_id, frame_index)`
- Palette associations are sorted by `character_id`
- No random values
- No timestamps
- No UUID generation

## Dependency Graph

```
tools/manga_frame/character_frame/
    ├── tools.manga_frame.character_tracking
    ├── tools.frame.models (Frame, FrameSequence)
    ├── tools.frame.palette (CharacterColorPalette)
    ├── Python standard library
    └── pydantic

Forbidden:
- runtime
- agents
- apps
- core
- PIL/Pillow
- OpenCV
- NumPy
- torch/tensorflow
- diffusers/transformers
- requests/httpx
- FFmpeg/MoviePy
- GPU/CUDA
- render
- audio
- vfx
```

## Forbidden Responsibilities

The character frame integration does NOT:

- Perform character detection
- Perform character recognition
- Load or decode images
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
- Perform OCR
- Perform segmentation
- Generate animations
- Modify Frame or FrameLayer models

## Known Limitations

1. **No Frame modification** - This module validates references but does not modify Frame structures
2. **No character detection** - This is a contract-only integration module
3. **Reference validation only** - Cannot validate actual file/layer existence without runtime
4. **Layer identifier loss** - The original `CharacterAppearance.layer_id` (string) is validated against `Frame.layers` then resolved to `layer_index` (integer). The semantic identifier is **intentionally not preserved** in `CharacterFrameReference`. See Layer Identifier Semantics above.

## Future Extension Points

### Frame Modification

Future modules may implement:
- Direct modification of Frame/FrameLayer with character metadata
- Addition of character-specific layers
- Integration with animation generation

### Enhanced Validation

Future implementations may support:
- File existence validation
- Image format validation
- Layer content validation

## Implementation Status

| Component | Status |
|-----------|--------|
| CharacterFrameMappingMetadata | Implemented |
| CharacterFrameReference | Implemented |
| CharacterFrameInput | Implemented |
| CharacterFrameOutput | Implemented |
| convert_character_tracking_to_frames | Implemented |
| Deep Immutability | Implemented |
| Structural Validation | Implemented |
| Palette Association | Implemented |
| Tests | Implemented |
| Documentation | This document |
| Frame Modification | NOT IMPLEMENTED |
| Character Detection | NOT IMPLEMENTED |
