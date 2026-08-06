# Runtime Animation Architecture

This document describes the runtime animation integration layer that bridges domain contracts and runtime execution.

## Overview

The runtime animation module (`runtime.animation`) provides a deterministic, explicit interface for evaluating `AnimationClip` objects at specific frames. It sits at the bottom of the dependency hierarchy and delegates all interpolation logic to `tools/frame/animation`.

## Dependency Direction

```
tools/manga_frame
        ↓
tools/frame
        ↓
runtime.animation  (THIS MODULE)
```

## What This Module Does

- **Clip Registration**: Manages a registry of `AnimationClip` objects by `clip_id`
- **Frame Evaluation**: Delegates to `evaluate_keyframe_at_frame()` from `tools/frame/animation`
- **Multi-Clip Evaluation**: Evaluates all active clips at a specific frame
- **State Management**: Explicit, immutable runtime state (no global state)
- **Error Handling**: Domain-specific exceptions with clear error messages

## What This Module Does NOT Do

- Generate animation data
- Create keyframes
- Interpolate transforms (delegates to `tools/frame/animation`)
- Render frames
- Access GPU
- Perform I/O operations
- Manage character identities (uses authoritative `clip_id` from domain contracts)

## Core Components

### AnimationRuntime

Main runtime class for managing and evaluating animation clips.

```python
class AnimationRuntime:
    """Runtime for character animation evaluation."""
    
    def __init__(self, sequence_id: str, *, frame_rate: float = 24.0) -> None:
        """Initialize animation runtime."""
        
    def register(self, clip: AnimationClip) -> AnimationClip:
        """Register an AnimationClip in the runtime."""
        
    def replace(self, clip: AnimationClip) -> AnimationClip:
        """Replace an existing clip with a new one."""
        
    def evaluate(self, clip_id: str, frame_index: int) -> FrameTransform:
        """Evaluate an animation clip at a specific frame."""
        
    def evaluate_at_frame(self, frame_index: int) -> dict[str, FrameTransform]:
        """Evaluate all active clips at a specific frame."""
```

### RuntimeAnimationState

Immutable state snapshot for the runtime.

```python
@dataclass(frozen=True)
class RuntimeAnimationState:
    sequence_id: str
    registered_clips: int
    frame_rate: float
```

### Exceptions

| Exception | Description |
|-----------|-------------|
| `AnimationRuntimeError` | Base exception |
| `ClipNotFoundError` | Clip not found in registry |
| `DuplicateClipError` | Duplicate clip_id registration |
| `InvalidFrameError` | Invalid frame index |
| `UnsupportedInterpolationError` | Non-LINEAR interpolation attempted |

## Data Flow

```
CharacterAnimationOutput
        ↓
CharacterTransformInputSet
        ↓
AnimationClip (via create_animation_clips)
        ↓
AnimationRuntime.register()
        ↓
AnimationRuntime.evaluate()
        ↓
evaluate_keyframe_at_frame()  [tools/frame/animation]
        ↓
FrameTransform
```

## Runtime Behavior

### Clip Registration

- `clip_id` must be unique within the runtime
- Duplicate registration raises `DuplicateClipError`
- Registration order does not affect evaluation results
- Clips can be unregistered dynamically
- Clips can be replaced using `replace()` method (same `clip_id` required)
- Bulk replace using `replace_many()` for atomic updates

### Frame Evaluation

1. **Exact Keyframe**: Returns keyframe's `FrameTransform`
2. **Between Keyframes**: Delegates to `evaluate_keyframe_at_frame()`
3. **Outside Clip Range**: Raises `InvalidFrameError`
4. **Empty Keyframes**: Returns `clip.default_transform`

### LINEAR Interpolation (V1)

Only `InterpolationType.LINEAR` is supported for interpolation between keyframes. Non-LINEAR types raise `UnsupportedInterpolationError`.

### Multi-Clip Evaluation

`evaluate_at_frame()` evaluates all clips at a specific frame:
- Skips clips outside their frame range
- Gracefully handles unsupported interpolation errors
- Returns dict mapping `clip_id` to `FrameTransform`

## Determinism Guarantees

- Same clips + same frame → identical output
- Repeated evaluation → identical output
- Registration order → does not change output
- No random or time-dependent behavior

## Error Handling

### Explicit Failures

| Scenario | Error |
|----------|-------|
| Unknown clip_id | `ClipNotFoundError` |
| Duplicate clip_id | `DuplicateClipError` |
| Negative frame | `InvalidFrameError` |
| Frame outside clip range | `InvalidFrameError` |
| Non-LINEAR interpolation | `UnsupportedInterpolationError` |
| Replace non-existent clip | `ClipNotFoundError` |
| Replace with duplicate clip_ids | `ValueError` |

### Error Recovery

Errors are explicit and deterministic. No silent failures or fallback behavior.

## Integration Points

### Entry Point

```python
from runtime.animation import AnimationRuntime

runtime = AnimationRuntime(sequence_id="intro")
```

### Registration

```python
from tools.manga_frame.character_animation import create_animation_clips

# Create clips from domain data
clips = create_animation_clips(bindings, transforms)

# Register in runtime
runtime.register_many(clips)
```

### Clip Replacement

```python
# Replace a clip with updated animation data
updated_clip = AnimationClip(
    clip_id="hero_1",
    start_frame=0,
    end_frame=48,  # Extended duration
    keyframes=[...],
)
runtime.replace(updated_clip)

# Bulk replace (atomic - all or nothing)
runtime.replace_many([updated_clip_a, updated_clip_b])
```

### Evaluation

```python
# Single clip
transform = runtime.evaluate("hero_1", 12)

# All active clips
all_transforms = runtime.evaluate_at_frame(12)
```

## Testing

The runtime includes comprehensive tests covering:

- Lifecycle management (create, register, unregister, clear)
- Clip registration (success, duplicate, unregister)
- Frame evaluation (exact keyframe, between keyframes, empty keyframes)
- Multi-clip evaluation
- Determinism verification
- Error handling
- Serialization compatibility

See: `tests/runtime/test_animation_runtime.py`

## Performance Considerations

- O(1) clip lookup by `clip_id`
- O(N) multi-clip evaluation (where N = number of active clips)
- No repeated sorting or rebuilding of clips
- Delegation to `tools/frame/animation` for interpolation (already optimized)

## V1 Limitations

- Only `InterpolationType.LINEAR` interpolation is supported
- Non-LINEAR types are valid contract values but raise errors at evaluation time
- No built-in caching (evaluates on demand)
- No GPU acceleration (pure CPU evaluation)

## Future Directions

- Support for additional interpolation types
- Optional result caching
- Timeline-aware evaluation
- GPU-accelerated evaluation path
