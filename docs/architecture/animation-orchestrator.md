# Animation Orchestrator

This document describes the orchestration layer that connects the character animation domain contracts to the runtime evaluation engine.

## Overview

The `AnimationOrchestrator` (`runtime.animation.consumer`) is a minimal consumer layer that:
1. Receives `CharacterAnimationOutput` and `CharacterTransformInputSet`
2. Converts them to `AnimationClip` objects via `create_animation_clips()`
3. Registers clips in `AnimationRuntime`
4. Delegates frame evaluation to `AnimationRuntime`

## Dependency Direction

```
CharacterAnimationOutput
        +
CharacterTransformInputSet
        ↓
AnimationOrchestrator.load()
        ↓
create_animation_clips()  [tools/manga_frame/character_animation]
        ↓
AnimationClip
        ↓
AnimationRuntime.register_many()
        ↓
AnimationRuntime.evaluate()
        ↓
FrameTransform
```

## Module Location

```
runtime/
    animation/
        __init__.py     # AnimationRuntime, RuntimeAnimationState
        consumer.py     # AnimationOrchestrator, OrchestratorState
```

## What This Module Does

- **Pipeline Coordination**: Orchestrates the animation pipeline from domain contracts to runtime
- **Clip Creation**: Delegates to `create_animation_clips()` for binding-to-clip conversion
- **Runtime Management**: Owns and manages an `AnimationRuntime` instance
- **Evaluation Delegation**: Delegates all evaluation to `AnimationRuntime`
- **Atomic Updates**: Load/reload clears and replaces clips atomically

## What This Module Does NOT Do

- Generate animation data (delegates to `create_animation_clips()`)
- Interpolate transforms (delegates to `AnimationRuntime`)
- Manage character identities (uses authoritative `clip_id` from domain contracts)
- Render frames
- Access GPU
- Perform I/O operations

## Core Components

### AnimationOrchestrator

Main orchestrator class for coordinating the animation pipeline.

```python
class AnimationOrchestrator:
    def __init__(self, *, frame_rate: float = 24.0) -> None:
        """Initialize orchestrator."""

    def load(
        self,
        animation_output: CharacterAnimationOutput,
        transform_inputs: CharacterTransformInputSet,
    ) -> tuple[AnimationClip, ...]:
        """Load and register animation data atomically."""

    def reload(
        self,
        animation_output: CharacterAnimationOutput,
        transform_inputs: CharacterTransformInputSet,
    ) -> tuple[AnimationClip, ...]:
        """Reload animation data, replacing existing state."""

    def evaluate(self, clip_id: str, frame_index: int) -> FrameTransform:
        """Evaluate a specific clip at a frame (delegates to AnimationRuntime)."""

    def evaluate_at_frame(self, frame_index: int) -> dict[str, FrameTransform]:
        """Evaluate all active clips at a frame (delegates to AnimationRuntime)."""

    def frames(
        self,
        start_frame: int = 0,
        end_frame: int | None = None,
    ) -> Iterator[tuple[int, dict[str, FrameTransform]]]:
        """Iterate through a frame range and evaluate each frame."""
```

### OrchestratorState

Immutable state snapshot for the orchestrator.

```python
@dataclass(frozen=True)
class OrchestratorState:
    sequence_id: str      # Current sequence ID (empty before load)
    clip_count: int       # Number of clips registered
    runtime_frame_rate: float  # Frame rate
```

## State Semantics

### Initial State

- `sequence_id = None`
- `clip_count = 0`
- No clips registered

### After load()

- `sequence_id` = sequence_id from CharacterAnimationOutput
- `clip_count` = number of clips created
- All clips registered in internal AnimationRuntime

### After reload()

- Same as load(), but replaces existing state
- Previous clips are cleared before new clips are registered

### Atomicity

If clip creation fails:
- Runtime state remains unchanged (no partial updates)

## Evaluation

### Delegation

All evaluation is delegated to the internal `AnimationRuntime`:

```
Orchestrator.evaluate()
        ↓
AnimationRuntime.evaluate()
        ↓
evaluate_keyframe_at_frame()
        ↓
FrameTransform
```

### Frame Evaluation

- `evaluate(clip_id, frame_index)` returns one `FrameTransform`
- `evaluate_at_frame(frame_index)` returns `dict[clip_id, FrameTransform]`

### Error Propagation

Runtime exceptions are propagated unchanged:
- `ClipNotFoundError` - unknown clip_id
- `InvalidFrameError` - invalid frame index
- `UnsupportedInterpolationError` - non-LINEAR interpolation

## Empty and Missing Data

| Scenario | Behavior |
|----------|----------|
| Empty `CharacterAnimationOutput` | Load succeeds, 0 clips registered |
| Empty `CharacterTransformInputSet` | Load succeeds, clips have no keyframes |
| Bindings without transforms | Clip uses `default_transform` (identity) |
| No registered clips | `evaluate_at_frame()` returns empty dict |
| Evaluation before load | Works (evaluates 0 clips) |
| Unknown clip | Raises `ClipNotFoundError` |
| Frame outside runtime range | Runtime handles (raises `InvalidFrameError`) |

## Example Usage

```python
from runtime.animation.consumer import AnimationOrchestrator

# Create orchestrator
orchestrator = AnimationOrchestrator(frame_rate=24.0)

# Load animation data (from upstream pipeline)
clips = orchestrator.load(
    animation_output,
    transform_inputs,
)

# Evaluate at frame 12
transform = orchestrator.evaluate("hero_body", 12)

# Or evaluate all clips at once
all_transforms = orchestrator.evaluate_at_frame(24)

# Iterate through all frames (inclusive range)
for frame_index, transforms in orchestrator.frames():
    print(f"Frame {frame_index}: {len(transforms)} transforms")

# Iterate through a specific range
for frame_index, transforms in orchestrator.frames(start_frame=5, end_frame=10):
    render_frame(frame_index, transforms)

# Reload with new data
new_clips = orchestrator.reload(new_output, new_transforms)

# Access underlying runtime for advanced use
runtime = orchestrator.get_runtime()
```

## Frame Iterator

The `frames()` method provides a deterministic, lazy frame iterator for batch evaluation and rendering.

### Semantics

- **Inclusive range**: Iterates from `start_frame` to `end_frame` (both inclusive)
- **Default range**: If no arguments provided, iterates from frame 0 to `duration_frames` (inclusive)
- **Lazy evaluation**: Uses a generator; frames are evaluated on-demand
- **Read-only**: Does not modify playback state (`current_frame`, `current_time`, `playback_state`)
- **Deterministic**: Same initial state produces identical iteration results

### Validation

| Condition | Behavior |
|-----------|----------|
| `start_frame < 0` | Raises `InvalidFrameError` |
| `end_frame < 0` | Raises `InvalidFrameError` |
| `start_frame > duration_frames` | Raises `InvalidFrameError` |
| `end_frame > duration_frames` | Raises `InvalidFrameError` |
| `start_frame > end_frame` | Returns empty iterator |

### Empty Runtime

When no clips are loaded (`duration_frames == 0`):
- `frames()` yields exactly one item: `(0, {})`
- Frame 0 is valid even with no clips registered

## V1 Limitations

- Only `InterpolationType.LINEAR` is supported during evaluation
- Non-LINEAR types raise `UnsupportedInterpolationError` at evaluation time
- No built-in caching
- No GPU acceleration

## Testing

The orchestrator includes comprehensive tests covering:

- Lifecycle management
- Load/reload operations
- Single and multiple character animations
- Empty inputs
- Sparse transforms
- Frame evaluation
- Frame iteration
- Unsupported interpolation
- Atomicity on failure
- Determinism
- End-to-end pipeline
- Playback state management
- Floating-point stability

See: `tests/runtime/test_animation_orchestrator.py`, `tests/runtime/test_animation_playback.py`
