# Layer Extraction Contracts

## Purpose

This document defines the data contracts for manga page layer extraction in the MANGA2ANIME pipeline.

**Layer extraction implementation is intentionally not included in this architecture version.** This module only defines the contract boundary for future extraction implementations.

## Scope

The contracts define:
- Layer categories (BACKGROUND, CHARACTER, FOREGROUND, EFFECT, UNKNOWN)
- Layer descriptors with metadata
- Input contracts for future extraction implementations
- Output contracts for extraction results
- Status tracking for extraction operations

## Architecture

```
tools/manga/
        |
        v
tools/manga_frame/
        |
        v
tools/manga_frame/layer_extraction/ (THIS MODULE)
        |
        v
tools/frame/
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `tools/manga/` | Parse manga sources, page metadata |
| `tools/manga_frame/` | Map manga to frame, integration boundary |
| `tools/manga_frame/layer_extraction/` | Define layer extraction contracts |
| `tools/frame/` | Frame/animation data contracts |

## Public API

### Enums

#### LayerCategory

```python
class LayerCategory(StrEnum):
    """Categories for extracted layer types."""

    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"
    UNKNOWN = "unknown"
```

Categories describe the structural type of a layer extracted from a manga page.

| Category | Description |
|----------|-------------|
| `BACKGROUND` | Background layer (panels, scenery) |
| `CHARACTER` | Character layer |
| `FOREGROUND` | Foreground elements |
| `EFFECT` | Effect layer (speed lines, explosions) |
| `UNKNOWN` | Category cannot be determined |

#### ExtractionStatus

```python
class ExtractionStatus(StrEnum):
    """Status of a layer extraction operation."""

    NOT_PROCESSED = "not_processed"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
```

| Status | Description |
|--------|-------------|
| `NOT_PROCESSED` | Extraction has not been performed |
| `SUCCESS` | All layers extracted successfully |
| `PARTIAL` | Some layers extracted (with errors) |
| `FAILED` | Extraction failed completely |

### Models

#### LayerMetadata

Immutable metadata container for layer extraction results.

```python
class LayerMetadata(BaseModel):
    """Immutable metadata container for layer extraction results."""

    model_config = {"frozen": True}

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the extraction (0.0-1.0)"
    )
    region_bounds: tuple[int, int, int, int] | None = Field(
        default=None,
        description="Bounding box as (x, y, width, height)"
    )
    extra: tuple[tuple[str, str], ...] = Field(
        default_factory=tuple,
        description="Additional key-value metadata"
    )
```

#### LayerDescriptor

Represents metadata about one extracted layer.

```python
class LayerDescriptor(BaseModel):
    """Represents metadata about one extracted layer."""

    layer_id: str = Field(min_length=1, description="Semantic layer identifier (name/label)")
    category: LayerCategory = Field(
        default=LayerCategory.UNKNOWN,
        description="Structural category of the layer"
    )
    layer_index: int = Field(ge=0, description="Z-order index for layer stacking")
    source_path: Path | None = Field(default=None, description="Path to layer source")
    metadata: LayerMetadata | None = Field(default=None, description="Extraction metadata")
```

**Validation:**
- `layer_id` must be non-empty after trimming (uniqueness NOT enforced)
- `layer_index` must be >= 0
- No duplicate `layer_index` values in a `LayerExtractionResult`

#### Layer Identity Semantics

This module distinguishes between two types of layer identification:

| Field | Purpose | Uniqueness | Use Case |
|-------|---------|------------|----------|
| `layer_id` | Semantic name/label | NOT enforced | Meaningful names like "background", "char_1" |
| `layer_index` | Z-order identifier | Enforced unique | Unique identification, ordering |

**Important:** Multiple `LayerDescriptor` objects MAY share the same `layer_id` value
if they have different `layer_index` values. This is valid and represents layers
with the same semantic name at different z-order positions.

**Example valid usage:**
```python
# Two layers with same layer_id but different layer_index
LayerDescriptor(layer_id="character", layer_index=1)
LayerDescriptor(layer_id="character", layer_index=5)
```

For unique identification, use `layer_index`. For semantic labeling, use `layer_id`.

#### ExtractionConfig

Configuration for layer extraction operations.

```python
class ExtractionConfig(BaseModel):
    """Configuration for layer extraction operations."""

    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    include_effects: bool = Field(default=True)
    max_layers: int | None = Field(default=None, ge=1)
    detect_characters: bool = Field(default=True)
```

#### LayerExtractionInput

Input contract for layer extraction operations.

```python
class LayerExtractionInput(BaseModel):
    """Input contract for layer extraction operations."""

    source_path: Path = Field(description="Path to the manga page image")
    page_number: int = Field(ge=0, description="Zero-based page number")
    frame_reference: str | None = Field(default=None, description="Optional frame reference")
    config: ExtractionConfig | None = Field(default=None, description="Extraction configuration")
    sequence_id: str | None = Field(default=None, description="Optional sequence identifier")
```

**IMPORTANT:** This contract does NOT load or inspect the actual image. Image loading is performed by the extraction implementation.

#### LayerExtractionResult

Result of a layer extraction operation.

```python
class LayerExtractionResult(BaseModel):
    """Result of a layer extraction operation."""

    model_config = {"frozen": True}

    source_path: Path = Field(description="Source path that was processed")
    page_number: int = Field(ge=0, description="Page number that was processed")
    layers: tuple[LayerDescriptor, ...] = Field(
        default_factory=tuple,
        description="Extracted layer descriptors"
    )
    status: ExtractionStatus = Field(default=ExtractionStatus.NOT_PROCESSED)
    frame_reference: str | None = Field(default=None)
    metadata: LayerMetadata | None = Field(default=None)
    sequence_id: str | None = Field(default=None)
```

**Deep Immutability:**
- This model is frozen/immutable
- `layers` is stored as tuple (immutable collection)
- No caller-owned state can affect the result

**Methods:**
- `layer_count` - Get number of extracted layers
- `get_layer_by_index(layer_index)` - Get layer by index
- `get_layers_by_category(category)` - Get layers by category

## Validation Rules

| Field | Validation |
|-------|------------|
| `LayerDescriptor.layer_id` | Non-empty after trimming |
| `LayerDescriptor.layer_index` | >= 0 |
| `LayerExtractionInput.page_number` | >= 0 |
| `LayerMetadata.confidence` | 0.0-1.0 |
| `ExtractionConfig.min_confidence` | 0.0-1.0 |
| `ExtractionConfig.max_layers` | >= 1 or None |
| `LayerExtractionResult.layers` | Ordered by layer_index, no duplicates |

## Immutability Guarantees

| Model | Frozen | Collection Type |
|-------|--------|-----------------|
| `LayerExtractionResult` | Yes | `tuple` |
| `LayerMetadata` | Yes | `tuple` |
| `LayerDescriptor` | No | N/A |
| `LayerExtractionInput` | No | N/A |
| `ExtractionConfig` | No | N/A |

## Serialization

All public contracts support Pydantic serialization:

```python
# Dict serialization
data = result.model_dump()

# Round-trip reconstruction
reconstructed = LayerExtractionResult(**data)
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
tools/manga_frame/layer_extraction/
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
```

## Forbidden Responsibilities

The layer extraction contracts do NOT:

- Load or decode images
- Perform image processing
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
- Perform OCR
- Detect characters
- Segment images
- Trace paths
- Generate SVG

## Current Limitations

1. **No extraction implementation** - Contracts are defined but no actual extraction logic exists
2. **No image processing** - This is a contract-only module
3. **No AI/ML integration** - Future implementations may add this
4. **`LayerCategory.UNKNOWN` limitation** - When converting to `FrameLayer`, UNKNOWN category requires explicit handling via `skip_unknown_categories` option or raises `UnknownLayerCategoryError`

## Future Extension Points

### Extraction Implementation

Future modules may implement:
- `tools/manga_frame/layer_extraction/engine.py` - Actual extraction logic
- `tools/manga_frame/layer_extraction/ml.py` - ML-based extraction

### Integration Points

**IMPORTANT:** The following integration points are NOT currently implemented:

1. **LayerExtractionResult → FrameSequence/FrameLayer** ✓ IMPLEMENTED
   - Implemented in `tools/manga_frame/layer_extraction_to_frame.py`
   - Converts `LayerExtractionResult` tuples to `FrameSequence`
   - Maps `LayerDescriptor` fields to `FrameLayer`
   - Handles `LayerCategory.UNKNOWN` → `LayerType` via explicit skip/error policy

2. **Layer extraction to manga parsing**
   - Future integration connects manga parser output to layer extraction input

3. **Character tracking across pages**
   - Uses `layer_id` from `CharacterAppearance`, not from layer extraction

### Algorithm Options

Future implementations may support:
- Traditional computer vision (OpenCV)
- ML-based segmentation
- Hybrid approaches

## Implementation Status

| Component | Status |
|-----------|--------|
| LayerCategory enum | Implemented |
| ExtractionStatus enum | Implemented |
| LayerMetadata | Implemented |
| LayerDescriptor | Implemented |
| ExtractionConfig | Implemented |
| LayerExtractionInput | Implemented |
| LayerExtractionResult | Implemented |
| Deep Immutability | Implemented |
| Validation | Implemented |
| Serialization | Implemented |
| Tests | Implemented |
| Documentation | This document |
| Extraction Engine | NOT IMPLEMENTED |
| LayerExtraction → Frame Integration | Implemented |
| LayerCategory.UNKNOWN → LayerType Handling | Implemented |
