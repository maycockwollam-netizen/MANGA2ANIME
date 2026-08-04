# Frame Models

## Purpose

The Frame Models (`tools/frame/models.py`) V1 provides **data contracts** for the frame/animation pipeline. It defines the core data structures for representing frames, layers, transforms, transitions, and sequences.

> Models V1 defines data contracts only. It does not implement rendering, animation, or image processing.

## Data Models

### Frame

Represents a single frame/panel state in the animation pipeline.

```python
Frame
├── frame_index: int          # Zero-based index (required, >= 0)
├── timestamp_ms: int | None   # Timestamp in ms from sequence start (optional)
├── duration_ms: int | None    # Display duration in ms (optional)
├── layers: list[FrameLayer]   # Ordered layers (bottom to top)
└── source_path: Path | None   # Optional frame source
```

**Validation:**
- `frame_index` must be >= 0
- `timestamp_ms` and `duration_ms` must be >= 0 if provided
- Layers must be ordered by `layer_index`

### FrameLayer

Represents a logical visual layer within a frame.

```python
FrameLayer
├── layer_id: str | None       # Unique layer identifier (optional)
├── layer_type: LayerType      # BACKGROUND, CHARACTER, FOREGROUND, EFFECT
├── layer_index: int           # Z-order index (>= 0)
├── source_path: Path | None   # Optional layer source
├── transform: FrameTransform | None  # Optional transform
└── visible: bool              # Layer visibility (default: True)
```

**Validation:**
- `layer_id` is trimmed and cannot be whitespace-only if provided
- `layer_index` must be >= 0

### FrameTransform

Data contract for transformation parameters.

```python
FrameTransform
├── position_x: float | None  # X position offset
├── position_y: float | None  # Y position offset
├── scale: float | None      # Scale factor (default: 1.0, >= 0)
├── rotation_deg: float | None  # Rotation in degrees (default: 0)
├── opacity: float | None    # Opacity 0-1 (default: 1.0)
├── anchor_x: float | None    # Anchor X point (default: 0.5)
└── anchor_y: float | None    # Anchor Y point (default: 0.5)
```

**Note:** This is DATA only. Does not execute transformations.

**Validation:**
- `scale` must be >= 0
- `opacity` must be 0-1
- `anchor_x` and `anchor_y` must be 0-1
- `rotation_deg` must be within reasonable range (±360000 degrees)

### FrameTransition

Data contract for transition between frames.

```python
FrameTransition
├── source_frame_index: int   # Source frame index (>= 0)
├── target_frame_index: int   # Target frame index (>= 0)
├── duration_ms: int          # Transition duration in ms (>= 0)
├── transition_type: str      # Transition type (normalized to lowercase)
└── interpolation: InterpolationType | None  # Optional interpolation
```

**Note:** This is DATA only. Does not execute interpolation.

**Validation:**
- Frame indexes must be >= 0
- Source and target frames must be different

### FrameSequence

Represents a sequence of frames with metadata.

```python
FrameSequence (frozen/immutable)
├── sequence_id: str          # Unique identifier (required, non-empty)
├── name: str | None         # Human-readable name
├── frame_rate: float        # FPS (default: 24.0, 0-120)
├── frames: list[Frame]      # Ordered frames
└── transitions: list[FrameTransition]  # Transitions
```

**Validation:**
- `sequence_id` is trimmed and cannot be empty/whitespace-only
- `frame_rate` must be 0 < x <= 120

## Enums

### LayerType

```python
class LayerType(StrEnum):
    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"
```

### TransitionType

```python
class TransitionType(StrEnum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
```

### InterpolationType

```python
class InterpolationType(StrEnum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
```

## Public API

```python
from tools.frame import (
    Frame,
    FrameLayer,
    FrameSequence,
    FrameTransform,
    FrameTransition,
    InterpolationType,
    LayerType,
    TransitionType,
)
```

## Serialization

All models support Pydantic serialization:

```python
# Dict serialization
data = frame.model_dump()

# JSON serialization
json_str = frame.model_dump_json()

# Round-trip reconstruction
reconstructed = Frame(**data)
assert reconstructed == frame
```

## Immutability

- `FrameSequence` is frozen/immutable
- Other models are mutable (can be used in nested contexts)
- Validation ensures deterministic behavior

## Dependency Boundary

```
tools/frame/models
    ├── standard library (enum.StrEnum, pathlib)
    └── pydantic (existing dependency)
```

**Forbidden dependencies:**
- ❌ runtime
- ❌ agents
- ❌ apps
- ❌ core
- ❌ torch/tensorflow
- ❌ opencv/PIL
- ❌ diffusers/transformers
- ❌ requests/httpx
- ❌ FFmpeg/MoviePy

## Explicit Non-Responsibilities

The models do NOT:
- ❌ Load/decode images
- ❌ Execute transforms
- ❌ Execute transitions
- ❌ Interpolate animations
- ❌ Render frames
- ❌ Process video/audio
- ❌ Access GPU
- ❌ Call AI/LLM
- ❌ Access network

## Future Extension Points

### tools/frame/transforms/

Future may implement:
- Transform execution engine
- Transform interpolation
- Easing function library

### tools/frame/animation/

Future may implement:
- Animation sequencing
- Timeline management
- Keyframe interpolation
- Playback engine

## Architecture Relationship

```
tools/frame/models.py (THIS MODULE)
        ↓
pure data contracts
        ↓
future tools/frame/transforms/ (execution)
        ↓
future tools/frame/animation/ (orchestration)
        ↓
future rendering pipeline
```

## Known Limitations

1. **No execution** — Models are pure data only
2. **No validation of frame relationships** — FrameSequence doesn't validate that transition frame indexes exist in frames
3. **No automatic layer ordering** — Layers must be provided in correct order
4. **No timing calculations** — No built-in duration/timing calculations

## Implementation Status

| Component | Status |
|-----------|--------|
| Frame | ✅ V1 |
| FrameLayer | ✅ V1 |
| FrameTransform | ✅ V1 |
| FrameTransition | ✅ V1 |
| FrameSequence | ✅ V1 |
| LayerType enum | ✅ V1 |
| TransitionType enum | ✅ V1 |
| InterpolationType enum | ✅ V1 |
| Validation | ✅ Implemented |
| Serialization | ✅ Implemented |
| Tests | ✅ 41 tests |
| Documentation | ✅ This document |
