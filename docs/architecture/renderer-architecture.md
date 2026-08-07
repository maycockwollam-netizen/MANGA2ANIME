# Renderer Architecture

This document describes the renderer integration architecture for the MANGA2ANIME animation system.

## Overview

The renderer architecture defines the boundary between the animation runtime system and concrete rendering implementations. The animation system produces `RenderFrame` data; the renderer consumes it.

**Important**: No concrete renderer implementation exists yet. This document describes the contract that future renderers must implement.

## Architecture

```
tools/frame/models.py (FrameTransform)
        ↓
tools/render/__init__.py (RenderFrame)
        ↓
tools/render/protocol.py (Renderer Protocol)
        ↓
[Concrete Renderer Implementations - NOT YET IMPLEMENTED]
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
| `transforms` | `Mapping[str, FrameTransform]` | Read-only mapping of clip_id → transform |
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
    ├── RenderFrameError (invalid frame data)
    └── TransformError (invalid transform)
```

### When to use

| Exception | When to Raise |
|-----------|---------------|
| `RendererError` | General rendering failure |
| `RenderFrameError` | Invalid or unexpected RenderFrame data |
| `TransformError` | Failed to apply FrameTransform |

## V1 Limitations

The current renderer architecture has the following limitations:

### Not Implemented

- **Concrete renderer**: No actual rendering implementation exists
- **Output abstraction**: No image/canvas/buffer output contract
- **GPU rendering**: No GPU backend integration
- **Resource management**: No texture/sprite pooling
- **Batching**: No frame batching optimization
- **Caching**: No transform caching
- **Dirty tracking**: No incremental update detection
- **Async rendering**: No async/await support
- **Multi-threading**: Single-threaded only
- **Serialization**: No renderer state persistence

### Design Decisions

These limitations are intentional for V1. They may be addressed in future increments based on concrete use cases and profiling data.

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

See: `tests/tools/render/test_protocol.py`

## Module Structure

```
tools/render/
    __init__.py      # RenderFrame, Renderer, exceptions
    protocol.py      # Renderer protocol definition
    exceptions.py    # RendererError hierarchy

tests/tools/render/
    test_protocol.py  # Renderer protocol tests
```

## Future Considerations

Future renderer implementations may consider:

- **Concrete renderers**: PIL, Canvas2D, OpenGL, Vulkan
- **Output abstractions**: Image bytes, canvas handles, GPU textures
- **Performance**: Caching, batching, dirty tracking
- **Async**: Async rendering pipelines
- **Lifecycle callbacks**: If stateful rendering is needed
- **begin_frame/end_frame**: If frame boundaries need explicit handling
