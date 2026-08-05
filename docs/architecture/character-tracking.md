# Character Tracking Contracts

## Purpose

This document defines the data contracts for character tracking in the MANGA2ANIME pipeline.

**Character Tracking V1 defines contracts only.**
**It does not detect, identify, recognize, or track characters in images.**

This module only defines the contract boundary for future character tracking implementations.

## Scope

The contracts define:
- Character tracks (logical character identity across pages)
- Character appearances (where a character appears)
- Tracking status
- Input/output contracts for future tracking implementations

## Architecture

```
tools/manga/
        |
        v
tools/manga_frame/
        |
        v
tools/manga_frame/character_tracking/ (THIS MODULE)
        |
        v
tools/frame/
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `tools/manga/` | Parse manga sources, page metadata |
| `tools/manga_frame/` | Map manga to frame, integration boundary |
| `tools/manga_frame/character_tracking/` | Define character tracking contracts |
| `tools/frame/` | Frame/animation data contracts |

## Public API

### Enums

#### TrackingStatus

```python
class TrackingStatus(StrEnum):
    """Status of a character tracking operation."""

    NOT_PROCESSED = "not_processed"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
```

| Status | Description |
|--------|-------------|
| `NOT_PROCESSED` | Tracking has not been performed |
| `SUCCESS` | All characters tracked successfully |
| `PARTIAL` | Some characters tracked (with errors) |
| `FAILED` | Tracking failed completely |

### Models

#### CharacterTrackMetadata

Immutable metadata container for character tracking results.

```python
class CharacterTrackMetadata(BaseModel):
    """Immutable metadata container for character tracking results."""

    model_config = {"frozen": True}

    total_characters: int | None = Field(default=None, ge=0)
    total_appearances: int | None = Field(default=None, ge=0)
    extra: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
```

#### CharacterAppearance

Represents one appearance of a character on a specific page/frame.

```python
class CharacterAppearance(BaseModel):
    """Represents one appearance of a character."""

    page_number: int = Field(ge=0)
    frame_index: int = Field(ge=0)
    layer_id: str | None = Field(default=None)
    region_bounds: tuple[int, int, int, int] | None = Field(default=None)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
```

**Validation:**
- `page_number` must be >= 0
- `frame_index` must be >= 0
- `layer_id`, when present, must be non-empty
- `confidence`, when present, must be 0.0-1.0
- `region_bounds`, when present, must have non-negative width/height

#### CharacterTrack

Represents one logical character tracked across manga frames/pages.

```python
class CharacterTrack(BaseModel):
    """Represents one logical character tracked across pages."""

    character_id: str = Field(min_length=1)
    display_name: str | None = Field(default=None)
    appearances: tuple[CharacterAppearance, ...] = Field(default_factory=tuple)
    palette_id: str | None = Field(default=None)
    metadata: CharacterTrackMetadata | None = Field(default=None)
```

**Validation:**
- `character_id` must be non-empty after trimming
- Appearances must be ordered by `page_number`
- No duplicate `(page_number, frame_index)` pairs

**Immutability:**
- `CharacterTrack` is NOT frozen (mutable for construction)
- `appearances` is stored as tuple (immutable collection)
- This is consistent with `LayerDescriptor` design

**Methods:**
- `appearance_count` - Get number of appearances
- `get_appearances_on_page(page_number)` - Filter by page

#### TrackingConfig

Configuration for character tracking operations.

```python
class TrackingConfig(BaseModel):
    """Configuration for character tracking operations."""

    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    track_across_pages: bool = Field(default=True)
    merge_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
```

#### CharacterTrackingInput

Input contract for character tracking operations.

```python
class CharacterTrackingInput(BaseModel):
    """Input contract for character tracking operations."""

    sequence_id: str = Field(min_length=1)
    frame_count: int = Field(ge=0)
    page_count: int = Field(ge=0)
    config: TrackingConfig | None = Field(default=None)
```

**IMPORTANT:** This contract does NOT perform character detection. Character tracking is performed by a future implementation.

#### CharacterTrackingResult

Result of a character tracking operation.

```python
class CharacterTrackingResult(BaseModel):
    """Result of a character tracking operation."""

    model_config = {"frozen": True}

    sequence_id: str
    tracks: tuple[CharacterTrack, ...] = Field(default_factory=tuple)
    status: TrackingStatus = Field(default=TrackingStatus.NOT_PROCESSED)
    metadata: CharacterTrackMetadata | None = Field(default=None)
```

**Deep Immutability:**
- This model is frozen/immutable
- `tracks` is stored as tuple (immutable collection)
- No caller-owned state can affect the result

**Methods:**
- `track_count` - Get number of tracks
- `get_track(character_id)` - Get track by ID
- `get_tracks_with_palette(palette_id)` - Filter by palette

## Validation Rules

| Field | Validation |
|-------|------------|
| `character_id` | Non-empty after trimming |
| `page_number` | >= 0 |
| `frame_index` | >= 0 |
| `layer_id` | Non-empty when present |
| `confidence` | 0.0-1.0 when present |
| `region_bounds` | 4 values, non-negative width/height |
| `appearances` | Ordered by page_number, no duplicates |
| `tracks` | Ordered by character_id, no duplicates |
| `sequence_id` | Non-empty after trimming |

## Immutability Guarantees

| Model | Frozen | Collection Type |
|-------|--------|-----------------|
| `CharacterTrackingResult` | ✅ Yes | `tuple` |
| `CharacterTrackMetadata` | ✅ Yes | `tuple` |
| `CharacterTrack` | ❌ No | `tuple` (appearances) |
| `CharacterAppearance` | ❌ No | N/A |
| `CharacterTrackingInput` | ❌ No | N/A |
| `TrackingConfig` | ❌ No | N/A |

## Serialization

All public contracts support Pydantic serialization:

```python
# Dict serialization
data = result.model_dump()

# Round-trip reconstruction
reconstructed = CharacterTrackingResult(**data)
assert reconstructed == result
```

## Determinism

The contract layer is deterministic:

- Same input produces equivalent output
- No timestamps
- No random values
- No UUID generation
- No environment-dependent values

## Dependency Graph

```
tools/manga_frame/character_tracking/
    ├── Python standard library
    ├── pydantic
    └── tools.frame (for potential integration)

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

The character tracking contracts do NOT:

- Perform character detection
- Perform character recognition
- Load or decode images
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
- Perform OCR
- Perform segmentation
- Generate embeddings

## Current Limitations

1. **No tracking implementation** - Contracts are defined but no actual tracking logic exists
2. **No character detection** - This is a contract-only module
3. **No AI/ML integration** - Future implementations may add this
4. **Reference validation limited** - Does not validate actual file/layer existence

## Future Extension Points

### Tracking Implementation

Future modules may implement:
- `tools/manga_frame/character_tracking/engine.py` - Actual tracking logic
- `tools/manga_frame/character_tracking/ml.py` - ML-based tracking

### Integration Points

Future integration may connect:
- Character tracking to manga parsing
- Character tracking to layer extraction
- Character tracks to frame construction
- Character palettes to colorization

### Algorithm Options

Future implementations may support:
- Face detection
- Character embeddings
- Cross-page matching
- Appearance merging

## Implementation Status

| Component | Status |
|-----------|--------|
| TrackingStatus enum | Implemented |
| CharacterTrackMetadata | Implemented |
| CharacterAppearance | Implemented |
| CharacterTrack | Implemented |
| TrackingConfig | Implemented |
| CharacterTrackingInput | Implemented |
| CharacterTrackingResult | Implemented |
| Deep Immutability | Implemented |
| Validation | Implemented |
| Serialization | Implemented |
| Tests | Implemented |
| Documentation | This document |
| Tracking Algorithm | NOT IMPLEMENTED |
| Character Detection | NOT IMPLEMENTED |
