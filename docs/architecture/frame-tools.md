# Frame Tools

## Purpose

The Frame Tools (`tools/frame/`) provides **data contracts** for the Frame/Motion Comic pipeline. This is currently an **architecture skeleton V0** — no rendering, animation execution, or AI processing is implemented.

## Architecture

```
tools/frame/
├── __init__.py        # Public API exports
├── models.py         # Frame data contracts
├── exceptions.py     # Exception hierarchy
├── palette/          # Character color palette contracts
│   └── __init__.py
├── transforms/        # Future: transform execution
│   └── __init__.py
└── animation/         # Future: animation sequencing
    └── __init__.py
```

## Public API

```python
from tools.frame import (
    Frame,
    FrameLayer,
    FrameTransform,
    FrameTransition,
    LayerType,
    FrameToolError,
    FrameValidationError,
    FrameTransformError,
    FrameTransitionError,
)

from tools.frame.palette import CharacterColorPalette
```

## Data Models

### Frame

Represents a frame in a timeline.

```python
Frame
├── frame_index: int          # Zero-based frame index
├── timestamp_ms: int | None  # Timestamp in milliseconds
├── duration_ms: int | None   # Duration in milliseconds
└── layers: list[FrameLayer]  # Frame layers
```

**Note:** Does not contain raw image data.

### FrameLayer

Represents a layer within a frame.

```python
FrameLayer
├── layer_type: LayerType     # BACKGROUND, CHARACTER, FOREGROUND, EFFECT
├── source_path: Path | None  # Path to layer source
├── layer_index: int          # Layer order index
└── transform: FrameTransform | None  # Layer transform
```

**Note:** Does not decode or manipulate image data.

### FrameTransform

Data contract for frame/layer transform.

```python
FrameTransform
├── position_x: float | None  # X position offset
├── position_y: float | None  # Y position offset
├── scale: float | None       # Scale factor (default: 1.0)
├── rotation_deg: float | None # Rotation in degrees (default: 0)
└── opacity: float | None     # Opacity 0-1 (default: 1.0)
```

**Note:** This is DATA only. Does not implement animation engine.

### FrameTransition

Data contract for transition between frames.

```python
FrameTransition
├── source_frame_index: int    # Source frame index
├── target_frame_index: int    # Target frame index
├── duration_ms: int           # Transition duration in milliseconds
└── transition_type: str       # "cut", "fade", "dissolve", etc.
```

**Note:** Does not implement interpolation or rendering.

### LayerType

Enum for layer types:

```python
class LayerType(StrEnum):
    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"
```

## CharacterColorPalette

### Purpose

> Lock màu của từng nhân vật để Colorization Agent trong tương lai đọc palette thay vì tự quyết định màu khác nhau ở từng panel.

The palette is the **source of truth** for character colors.

### Data Contract

```python
CharacterColorPalette (frozen/immutable)
├── character_id: str          # Unique character identifier (required)
├── hair: str                  # Hair color in HEX (#RRGGBB)
├── skin: str                  # Skin color in HEX
├── eyes: str                  # Eye color in HEX
├── outfit: str                # Primary outfit color in HEX
├── accessories: str | None    # Accessories color in HEX
└── custom_colors: dict[str, str]  # Additional custom color mappings
```

### Example

```python
palette = CharacterColorPalette(
    character_id="naruto",
    hair="#FF9900",
    skin="#FFCC99",
    eyes="#4477EE",
    outfit="#FFCC00",
    accessories="#333333",
    custom_colors={"cape": "#FF0000"},
)
```

### Usage Pattern

```
CharacterColorPalette
        ↓
Colorization Agent
        ↓
Colorized Panel
```

The Colorization Agent will READ this palette. It must NOT modify the palette.

### Validation Rules

| Field | Rule |
|-------|------|
| `character_id` | Non-empty string |
| All color fields | Valid HEX format (#RRGGBB), uppercase normalized |
| `custom_colors` | Keys are strings, values are valid HEX |

## Immutability Guarantees

- `CharacterColorPalette` is frozen/immutable
- Attempting to modify after creation raises exception
- Ensures palette remains source of truth

## Serialization

All models are Pydantic models supporting:
- `model_dump()` for dict serialization
- `model_validate()` for dict deserialization
- JSON-compatible output

## Determinism

All frame models are:
- Fully deterministic
- Serializable
- Free of timestamps
- Free of randomness
- Free of filesystem state
- Free of network state

## Dependency Graph

```
tools/frame
    ├── standard library
    └── pydantic (existing project dependency)
```

**Forbidden dependencies:**
- ❌ runtime
- ❌ agents
- ❌ apps
- ❌ core (no reverse dependency)
- ❌ GPU libraries
- ❌ Network clients
- ❌ Image processing libraries

## Explicit Non-Responsibilities (V0)

The frame tools do NOT implement:

- AI colorization
- Colorization Agent
- Stable Diffusion
- ControlNet
- Image decoding
- Image manipulation
- potrace integration
- SVG rendering
- Ken Burns execution
- Parallax execution
- Vector morph execution
- FFmpeg
- MoviePy
- GPU processing
- CUDA
- Multiprocessing
- Threading
- Network requests
- Filesystem crawling
- Video rendering
- Audio processing

## Future Extension Points

### transforms/

Future may implement:
- Transform execution
- Animation interpolation
- Easing functions

### animation/

Future may implement:
- Animation sequencing
- Timeline management
- Keyframe interpolation

### Colorization Pipeline

Future layers may implement:
- Colorization Agent
- AI-based colorization
- External color palette databases

## Exception Hierarchy

```python
FrameToolError (base)
├── FrameValidationError
├── FrameTransformError
├── FrameTransitionError
└── FramePaletteError
```

V0 provides these as placeholders. Actual usage deferred to future implementation.

## Known Limitations

1. **No execution** — Frame tools are pure data contracts. No rendering or animation execution.
2. **No external sources** — No metadata fetching from APIs or databases.
3. **No AI** — No ML model integration or inference.
4. **Minimal validation** — Basic type/format validation only.

## Implementation Status

| Component | Status |
|-----------|--------|
| Frame models | ✅ Skeleton V0 |
| FrameTransform | ✅ Skeleton V0 |
| FrameTransition | ✅ Skeleton V0 |
| CharacterColorPalette | ✅ Skeleton V0 |
| Exceptions | ✅ Skeleton V0 |
| Transforms package | ⬜ Future |
| Animation package | ⬜ Future |
| Tests | ✅ Implemented |
| Documentation | ✅ This document |
