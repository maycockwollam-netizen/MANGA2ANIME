# Renderer Architecture

This document describes the renderer integration architecture for the MANGA2ANIME animation system.

## Overview

The renderer architecture defines the boundary between the animation runtime system and concrete rendering implementations. The animation system produces `RenderFrame` data; the renderer consumes it.

## Architecture

```
tools/frame/models.py (FrameTransform)
        â†“
tools/render/__init__.py (RenderFrame)
        â†“
tools/render/protocol.py (Renderer Protocol)
        â†“
[Concrete Renderer Implementations]
```

## Concrete Renderer V1

A concrete renderer implementation (`ConcreteRenderer`) exists that renders `RenderFrame` to RGBA images using Pillow.

### Implementation

- **Backend**: Pillow (PIL)
- **Output**: RGBA PNG images
- **Entities**: Placeholder colored rectangles
- **Color derivation**: Deterministic using SHA-256 hash of clip_id

### Module

```
tools/render/concrete_renderer.py
```

### Usage

```python
from tools.render import ConcreteRenderer, RenderFrame
from tools.frame.models import FrameTransform

renderer = ConcreteRenderer(canvas_size=(800, 600))
frame = RenderFrame(
    frame_index=0,
    timestamp_seconds=0.0,
    frame_rate=24.0,
    duration_frames=24,
    transforms={"hero": FrameTransform(position_x=100, position_y=100)},
)
renderer.render(frame)
image = renderer.last_output  # PIL Image
image.save("frame_0.png")
```

## Dependency Constraints

The Renderer protocol and RenderFrame **must NOT** depend on:

- `runtime.animation` (ANY module)
- `AnimationRuntime` internals
- `AnimationTimeline`
- `AnimationClip`
- `tools.manga_frame`

This ensures the renderer boundary remains clean and decoupled from animation logic.

## RenderFrame Contract

The `RenderFrame` is the primary data contract passed from the animation runtime to the renderer.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `frame_index` | `int` | Zero-based frame index in the animation sequence |
| `timestamp_seconds` | `float` | Elapsed time from animation start (frame_index / frame_rate) |
| `frame_rate` | `float` | Animation frame rate (FPS) |
| `duration_frames` | `int` | Total animation duration in frames |
| `duration_seconds` | `float` | Total animation duration in seconds (property) |
| `transforms` | `Mapping[str, FrameTransform]` | Read-only mapping of clip_id â†’ transform |
| `entity_count` | `int` | Number of entities in this frame (property) |

### Immutability

`RenderFrame` is a frozen dataclass. The `transforms` mapping is wrapped in `MappingProxyType` to prevent adding/deleting keys.

## Renderer Protocol

The `Renderer` protocol defines the structural contract for renderers.

### Definition

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderer(Protocol):
    def render(self, frame: RenderFrame) -> None:
        """Render a single frame.
        
        Args:
            frame: Immutable frame context to render.
        """
        ...
```

### Requirements

1. **Accept RenderFrame only**: The renderer receives `RenderFrame` as its only input.
2. **No runtime access**: The renderer must not access `AnimationRuntime`, `AnimationTimeline`, or other runtime internals.
3. **No mutation**: The renderer must not mutate the input `RenderFrame`.
4. **clip_id identity**: Use `clip_id` as the authoritative entity identity.
5. **FrameTransform semantics**: Preserve the semantics of `FrameTransform` fields.

### Protocol Checking

The `Renderer` is a `runtime_checkable` Protocol. Use `isinstance()` to check if an object implements the protocol:

```python
from tools.render import Renderer

if isinstance(my_renderer, Renderer):
    my_renderer.render(frame)
```

Implementations do not need to inherit from `Renderer`. Structural subtyping means any class with a compatible `render()` method satisfies the protocol.

## Entity Lifecycle Semantics

The renderer uses a **stateless request-response** model. Entity lifecycle is implicit in the `transforms` mapping.

### Entity Appears

```python
def render(frame: RenderFrame) -> None:
    for clip_id, transform in frame.transforms.items():
        # clip_id first appears in this frame
        # Create entity if needed, apply transform
        ...
```

### Entity Remains Present

```python
def render(frame: RenderFrame) -> None:
    for clip_id, transform in frame.transforms.items():
        # clip_id was present in previous frame
        # Apply new transform to existing entity
        ...
```

### Entity Disappears

```python
def render(frame: RenderFrame) -> None:
    # In frame N, clip_id is NOT in transforms
    # Entity simply not rendered in this frame
    # Renderer may hide/destroy the entity
    ...
```

### Empty Frame

```python
def render(frame: RenderFrame) -> None:
    if len(frame.transforms) == 0:
        # Clear the canvas / render empty frame
        ...
```

### Multiple Entities

```python
def render(frame: RenderFrame) -> None:
    for clip_id, transform in frame.transforms.items():
        # Render each entity with its transform
        ...
```

## FrameTransform Semantics

The renderer receives `FrameTransform` values as-is from the animation runtime.

### Fields

| Field | Type | Semantics |
|-------|------|----------|
| `position_x` | `float \| None` | X offset from origin |
| `position_y` | `float \| None` | Y offset from origin |
| `scale` | `float \| None` | Relative scale (1.0 = unchanged) |
| `rotation_deg` | `float \| None` | Clockwise rotation in degrees |
| `opacity` | `float \| None` | Opacity 0.0-1.0 |
| `anchor_x` | `float \| None` | Normalized pivot X (0-1) |
| `anchor_y` | `float \| None` | Normalized pivot Y (0-1) |

### Coordinate System

**The RenderFrame contract does NOT specify a coordinate system.**

The animation system provides transform values as-is:
- `position_x`, `position_y`: offset from origin (units unspecified)
- `scale`: relative to original size (1.0 = unchanged)
- `rotation_deg`: clockwise positive
- `opacity`: 0.0 (transparent) to 1.0 (opaque)
- `anchor_x`, `anchor_y`: normalized pivot points (0-1 range)

The renderer is responsible for interpreting these values according to its own coordinate conventions.

### None Values

`None` values mean "use default". The renderer should apply sensible defaults when values are `None`.

## clip_id Identity

`clip_id` is the **authoritative entity identity**.

### What IS allowed

- Use `clip_id` as-is from `transforms` keys
- Track entities by `clip_id`
- Map `clip_id` to renderer-specific entity handles

### What is NOT allowed

- Generate numeric entity IDs
- Transform/hash `clip_id`
- Create separate identity systems
- Rename `clip_id` to another field

## Error Hierarchy

```
RendererError (base)
    â”śâ”€â”€ RenderFrameError (invalid frame data)
    â””â”€â”€ TransformError (invalid transform)
```

### When to use

| Exception | When to Raise |
|-----------|---------------|
| `RendererError` | General rendering failure |
| `RenderFrameError` | Invalid or unexpected RenderFrame data |
| `TransformError` | Failed to apply FrameTransform |

## V1 Limitations

The ConcreteRenderer V1 implementation has the following limitations:

### Not Implemented

- **Real image assets**: Only placeholder rectangles are rendered
- **GPU rendering**: CPU-based Pillow rendering only
- **Resource management**: No texture/sprite pooling
- **Batching**: No frame batching optimization
- **Caching**: No transform or asset caching
- **Dirty tracking**: No incremental update detection
- **Async rendering**: No async/await support
- **Multi-threading**: Single-threaded only
- **Video export**: No built-in video encoding
- **Serialization**: No renderer state persistence

### Design Decisions

These limitations are intentional for V1. They may be addressed in future increments based on concrete use cases and profiling data.

### Deferred Features

Future renderer implementations may consider:

- **Real assets**: AssetProvider abstraction for loading images
- **GPU backend**: OpenGL/Vulkan accelerated rendering
- **Animation sequences**: Built-in sequence rendering to frames
- **Video export**: FFmpeg-based video encoding
- **Performance**: Caching, batching, dirty tracking

## Example Usage

### Simple Renderer Implementation

```python
from tools.render import RenderFrame, Renderer

class LoggingRenderer:
    """Simple renderer that logs frame data."""
    
    def render(self, frame: RenderFrame) -> None:
        print(f"Frame {frame.frame_index} at {frame.timestamp_seconds}s")
        print(f"Entities: {frame.entity_count}")
        for clip_id, transform in frame.transforms.items():
            print(f"  {clip_id}: pos=({transform.position_x}, {transform.position_y})")
```

### Using the Renderer

```python
from tools.render import RenderFrame, Renderer
from tools.frame.models import FrameTransform

# Create a frame
frame = RenderFrame(
    frame_index=12,
    timestamp_seconds=0.5,
    frame_rate=24.0,
    duration_frames=240,
    transforms={
        "hero_1": FrameTransform(position_x=100, position_y=50),
        "villain_2": FrameTransform(position_x=300, position_y=50),
    },
)

# Use renderer
renderer: Renderer = LoggingRenderer()
renderer.render(frame)
```

## Testing

Renderer protocol tests verify:

- Protocol compliance (runtime-checkable structural typing works)
- isinstance(renderer, Renderer) correctly identifies protocol implementers
- Accepts RenderFrame as input
- Consumes transforms by clip_id
- Handles empty frames
- Handles multiple entities
- Produces deterministic results
- Does not mutate input

## Single-Frame Render Integration

The integration layer connects `RenderFrame` production to PNG output.

### Architecture

```
AnimationOrchestrator.render_frame()
        ↓
    RenderFrame
        ↓
    FrameAdapter
        ↓
    ConcreteRenderer
        ↓
    PNG file
```

### Module

```
tools/render/integration.py
```

### Usage

```python
from tools.render import render_frame_to_png

# From AnimationOrchestrator
frame = orchestrator.render_frame()
render_frame_to_png(frame, "output.png")

# Or from any RenderFrame source
from tools.render import RenderFrame
frame = RenderFrame(
    frame_index=0,
    timestamp_seconds=0.0,
    frame_rate=24.0,
    duration_frames=24,
    transforms={"hero": FrameTransform(position_x=100)},
)
render_frame_to_png(frame, "output.png")
```

### API

```python
def render_frame_to_png(
    frame: RenderFrame,
    output_path: Path | str,
    *,
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> None:
    """Render a RenderFrame to a PNG file."""
```

### Behavior

1. Accepts an existing `RenderFrame`
2. Creates/uses `ConcreteRenderer` when no renderer is supplied
3. Passes the exact `RenderFrame` through `FrameAdapter`
4. Obtains `renderer.last_output`
5. Saves the Pillow image as PNG
6. Returns `None`

### Constraints

The integration layer **does NOT**:

- Produce `RenderFrame` (delegates to runtime)
- Implement animation playback
- Implement video rendering
- Access runtime internals (`AnimationRuntime`, `AnimationTimeline`, etc.)

See: `tests/tools/render/test_render_integration.py`

## Module Structure

```
tools/render/
    __init__.py      # RenderFrame, Renderer, exceptions, render_frame_to_png
    protocol.py      # Renderer protocol definition
    exceptions.py    # RendererError hierarchy
    adapter.py      # FrameAdapter for frame forwarding
    concrete_renderer.py  # ConcreteRenderer (Pillow backend)
    integration.py   # Single-frame render integration (RenderFrame -> PNG)
    sequence.py     # Multi-frame PNG sequence export
    export.py      # End-to-end export entry point

tests/tools/render/
    test_protocol.py  # Renderer protocol tests
    test_adapter.py   # FrameAdapter tests
    test_concrete_renderer.py  # ConcreteRenderer tests
    test_render_integration.py  # Single-frame integration tests
    test_sequence.py  # PNG sequence export tests
    test_export.py  # Export entry point tests
```

## Future Considerations

Future renderer implementations may consider:

- **Concrete renderers**: PIL, Canvas2D, OpenGL, Vulkan
- **Output abstractions**: Image bytes, canvas handles, GPU textures
- **Performance**: Caching, batching, dirty tracking
- **Async**: Async rendering pipelines
- **Lifecycle callbacks**: If stateful rendering is needed
- **begin_frame/end_frame**: If frame boundaries need explicit handling

## Multi-Frame PNG Sequence Export

The sequence export layer renders multiple RenderFrame objects to numbered PNG files.

### Architecture

```
Iterable[RenderFrame]
        ↓
render_frames_to_png()
        ↓
PNG sequence (frame_000000.png, frame_000001.png, ...)
```

### Module

```
tools/render/sequence.py
```

### Usage

```python
from tools.render import render_frames_to_png

# From orchestrator frames
frames = [orchestrator.render_frame() for _ in range(10)]
count = render_frames_to_png(frames, "output_frames")
```

### API

```python
def render_frames_to_png(
    frames: Iterable[RenderFrame],
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> int:
    """Render a sequence of RenderFrame objects to numbered PNG files."""
```

### Filename Convention

- Format: `{prefix}_{frame_index:06d}.png`
- Example: `frame_000000.png`, `frame_000001.png`, `frame_000042.png`
- Zero-padded to 6 digits for determinism

### Behavior

1. Creates output directory if it doesn't exist
2. Processes frames in supplied order
3. Preserves exact RenderFrame objects
4. Uses frame_index for filenames
5. Returns count of successfully written files

### PNG Sequence as Intermediate Artifact

PNG sequences are intermediate artifacts for video encoding. They are:

- **Deterministic**: Same input produces same output
- **Debuggable**: Individual frames can be inspected
- **Out of scope**: Video encoding/playback is not implemented

Future work may include video encoding using external tools.

See: `tests/tools/render/test_sequence.py`

## End-to-End Render Export Entry Point

The `export_render_frames()` function provides a public entry point for exporting RenderFrame sequences.

### Architecture

```
RenderFrame
    ↓
FrameAdapter
    ↓
ConcreteRenderer
    ↓
render_frame_to_png()
    ↓
render_frames_to_png()
    ↓
export_render_frames()
    ↓
PNG sequence
```

### Module

```
tools/render/export.py
```

### API

```python
def export_render_frames(
    frames: Iterable[RenderFrame],
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    canvas_size: tuple[int, int] | None = None,
    background: tuple[int, int, int, int] | None = None,
    renderer: Renderer | None = None,
) -> int:
    """Export a sequence of RenderFrame objects to numbered PNG files."""
```

### Design

This entry point is **orchestration only** — it delegates to the existing implementation without introducing new logic.

- **PNG sequence is the current terminal output artifact**
- **Video encoding remains out of scope**
- **No animation runtime coupling is introduced**

### Usage

```python
from tools.render import export_render_frames

frames = [orchestrator.render_frame() for _ in range(10)]
count = export_render_frames(frames, "output_frames")
```

See: `tests/tools/render/test_export.py`

## End-to-End Smoke Tests

The render export pipeline is verified by end-to-end smoke tests that prove the complete pipeline works.

### Architecture Verified

```
AnimationOrchestrator.render_frame()
        ↓
    RenderFrame
        ↓
    export_render_frames()
        ↓
    render_frames_to_png()
        ↓
    render_frame_to_png()
        ↓
    FrameAdapter
        ↓
    ConcreteRenderer
        ↓
    PNG files
```

### Test Coverage

The end-to-end tests verify:

- Real RenderFrame can be produced by animation orchestration
- Frames can be exported through export_render_frames()
- PNG files are created with correct properties
- PNG format is RGBA with correct dimensions
- Frame filenames contain correct frame_index
- Frame ordering is deterministic
- RenderFrame metadata remains unchanged
- clip_id keys and transforms are preserved
- Identical input produces byte-identical output
- Exceptions are not swallowed
- Output directory handling works

### Module

```
tests/tools/render/test_end_to_end.py
```

See: `tests/tools/render/test_end_to_end.py`

## Render Sequence Validation

The validation layer verifies exported PNG sequences without coupling to rendering implementation.

### Architecture

```
Exported PNG sequence
        ↓
    validate_render_sequence()
        ↓
    RenderSequenceValidation (or ValidationError)
```

### Module

```
tools/render/validation.py
```

### API

```python
@dataclass(frozen=True)
class RenderSequenceValidation:
    frame_count: int
    frame_indices: tuple[int, ...]
    dimensions: tuple[int, int]
    mode: str


def validate_render_sequence(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    expected_frame_count: int | None = None,
) -> RenderSequenceValidation:
    """Validate an exported PNG sequence."""
```

### Validation Checks

- Empty directory detection
- Missing frame indices detection
- Consistent image dimensions
- Consistent image mode
- Readable PNG files
- Expected frame count verification (optional)

### Constraints

- Does not modify files
- Does not import runtime/animation
- Does not import Pillow rendering internals beyond metadata inspection

See: `tests/tools/render/test_validation.py`

## Render Sequence Preview

The preview layer provides read-only inspection of exported PNG sequences.

### Architecture

```
PNG sequence
        ↓
    create_render_preview()
        ↓
    RenderPreview (inspection abstraction)
```

### Module

```
tools/render/preview.py
```

### API

```python
@dataclass(frozen=True)
class RenderPreview:
    frame_paths: tuple[Path, ...]
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float

    @property
    def frame_count(self) -> int:
        ...

    def frame_path(self, frame_index: int) -> Path:
        ...

    def frame_image(self, frame_index: int) -> Image.Image:
        ...


def create_render_preview(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    frame_rate: float = 24.0,
) -> RenderPreview:
    ...
```

### Preview Behavior

- Delegates validation to existing `validate_render_sequence()`
- No file modification
- No image caching
- No async behavior

### Constraints

- Does not render anything
- Does not modify files
- Does not encode video
- Does not launch a UI

See: `tests/tools/render/test_preview.py`

## Render Sequence Manifest

The manifest layer provides immutable metadata describing an already-exported PNG sequence.

### Architecture

```
PNG sequence
        ↓
    create_render_manifest()
        ↓
    RenderSequenceManifest (metadata description)
```

### Module

```
tools/render/manifest.py
```

### API

```python
@dataclass(frozen=True)
class RenderSequenceManifest:
    output_dir: Path
    prefix: str
    frame_count: int
    frame_indices: tuple[int, ...]
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str


def create_render_manifest(
    output_dir: Path | str,
    *,
    prefix: str = "frame",
    frame_rate: float = 24.0,
) -> RenderSequenceManifest:
    ...
```

### Relationship with Other Layers

- **Validation**: Manifest delegates to `validate_render_sequence()`
- **Preview**: Manifest provides metadata; Preview provides frame access
- Both are read-only, no rendering responsibility

### Constraints

- Immutable metadata only
- No file modification
- Delegates validation to existing layer

See: `tests/tools/render/test_manifest.py`

## Render Sequence Playback V1

The playback layer provides synchronous playback control over an existing RenderPreview.

### Architecture

```
RenderPreview
        ↓
    RenderPlayback
        ↓
    current frame / seek / step
```

### Module

```
tools/render/playback.py
```

### API

```python
class RenderPlayback:
    preview: RenderPreview
    frame_rate: float

    # Properties
    frame_count: int
    frame_duration: float
    current_frame_index: int
    current_frame_path: Path
    playing: bool

    # Methods
    def play() -> None: ...
    def pause() -> None: ...
    def stop() -> None: ...
    def seek(frame_index: int) -> None: ...
    def step_forward() -> None: ...
    def step_backward() -> None: ...
    def current_frame_image() -> Image.Image: ...


class PlaybackError(Exception):
    """Error controlling render playback."""
```

### V1 Constraints

- Synchronous only (no threads, no async)
- No real-time timing (timing is external)
- No caching
- No looping
- No video encoding
- No GUI

See: `tests/tools/render/test_playback.py`
