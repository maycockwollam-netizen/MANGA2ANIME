# Frame Animation

## Purpose

The Frame Animation (`tools/frame/animation/`) V1 provides a **pure, deterministic animation/timeline layer** for the frame system. It describes how frames are generated over time without rendering images.

> Animation V1 is a mathematical/data orchestration layer only. It does not perform image manipulation, rendering, or GPU operations.

## Public API

```python
from tools.frame.animation import (
    DEFAULT_FRAME_RATE,              # 24.0
    AnimationClip,                  # Animation for one layer
    AnimationFrame,                 # Evaluated frame state
    AnimationKeyframe,              # Transform at a frame
    AnimationTimeline,              # Timeline management
    evaluate_keyframe_at_frame,     # Evaluate at frame
    evaluate_at_frame,             # Evaluate multiple clips at frame
    generate_animation_frames,     # Generate all frames
)
```

## Default Frame Rate

The project targets **24 frames per second (FPS)**:

```python
DEFAULT_FRAME_RATE = 24.0
```

Time calculations:

```
1 second  = 24 frames
2 seconds = 48 frames
5 seconds = 120 frames
```

## AnimationKeyframe

Represents a transform state at a specific frame.

```python
AnimationKeyframe (frozen)
├── frame_index: int              # Frame number (>= 0)
├── transform: FrameTransform      # Transform state at this frame
└── interpolation: InterpolationType  # How to interpolate (default: LINEAR)
```

## AnimationClip

Represents animation for one layer/object.

```python
AnimationClip
├── clip_id: str                  # Unique identifier (required)
├── start_frame: int              # First frame (inclusive, >= 0)
├── end_frame: int                # Last frame (inclusive, >= 0)
├── keyframes: list[Keyframe]     # Ordered keyframes
└── default_transform: FrameTransform  # Transform before first keyframe
```

**Validation:**
- `clip_id` is trimmed and cannot be empty/whitespace-only
- `end_frame` must be >= `start_frame`
- Keyframes must be ordered by `frame_index`
- Duplicate keyframe indexes are rejected
- Keyframes cannot exist outside the clip range

## AnimationTimeline

Timeline for animation with configurable frame rate.

```python
AnimationTimeline (frozen)
├── frame_rate: float            # FPS (default: 24.0, 0-120)
└── duration_frames: int          # Total frames
```

### Timeline Methods

```python
timeline.frame_time(frame_index)      # Frame → seconds
timeline.frame_time_ms(frame_index)    # Frame → milliseconds
timeline.frame_index_at(seconds)      # Seconds → frame
timeline.duration_seconds()            # Total duration in seconds
timeline.duration_ms()                # Total duration in milliseconds
```

### 24 FPS Examples

```python
timeline = AnimationTimeline(duration_frames=24)

# 1 second = 24 frames
timeline.frame_time(24) == 1.0
timeline.frame_time_ms(24) == 1000

# Midpoint
timeline.frame_time(12) == 0.5
timeline.frame_time_ms(12) == 500
```

## AnimationFrame

Evaluated animation state at a specific frame.

```python
AnimationFrame (frozen dataclass, slots)
├── frame_index: int              # Frame number
├── timestamp_ms: int             # Timestamp in ms
├── transform: FrameTransform      # Evaluated transform
└── clip_id: str | None           # Source clip ID
```

**Note:** This is pure data only. No image buffers, PIL/OpenCV objects, GPU tensors, or rendered pixels.

## Frame/Time Semantics

The timeline uses inclusive frame ranges:

```python
# Frame 0 to 24 = 25 frames
start_frame = 0
end_frame = 24
# range(0, 25) = [0, 1, 2, ..., 24]
```

## Interpolation

For two keyframes:

```
A @ frame 0: position_x = 0
B @ frame 24: position_x = 100
```

At frame 12 (midpoint):

```
t = 12 / 24 = 0.5
position_x = 0 + (100 - 0) * 0.5 = 50
```

### Supported Interpolation

V1 supports only **LINEAR** interpolation:

```python
InterpolationType.LINEAR  # Linear interpolation
```

Other interpolation types (EASE_IN, EASE_OUT, etc.) will raise a `ValueError` if used.

### Rotation Interpolation

Rotation uses **direct numeric interpolation**, not shortest-angle:

```python
# Interpolating 350° to 10°:
# Direct: 350 + (10 - 350) * 0.5 = 180°
```

## Determinism Guarantees

All animation operations are:
- Fully deterministic
- No random values
- No timestamps from system clock
- No global mutable state
- No I/O operations
- Same inputs → identical outputs

## Mutation Guarantees

Source objects are never mutated:
- `AnimationClip` is not modified
- `AnimationKeyframe` is not modified
- `FrameTransform` is not modified
- Generated `AnimationFrame` objects are independent

## Dependencies

```
tools/frame/animation
    ├── standard library (dataclasses)
    ├── pydantic (existing)
    ├── tools.frame.models (FrameTransform, InterpolationType)
    └── tools.frame.transforms (interpolate_transform)
```

**Forbidden dependencies:**
- ❌ runtime
- ❌ agents
- ❌ apps
- ❌ core
- ❌ tools/audio
- ❌ tools/render
- ❌ tools/vfx
- ❌ torch/tensorflow
- ❌ opencv/PIL
- ❌ diffusers/transformers
- ❌ requests/httpx
- ❌ FFmpeg/MoviePy
- ❌ GPU libraries

## Explicit Non-Responsibilities

The animation module does NOT:
- ❌ Perform image manipulation
- ❌ Execute rendering
- ❌ Access GPU
- ❌ Perform I/O operations
- ❌ Process audio
- ❌ Use AI/LLM
- ❌ Render to video
- ❌ Encode video streams

## Future Ken Burns Usage

The animation layer can represent Ken Burns effects:

```python
# Pan and zoom effect
clip = AnimationClip(
    clip_id="background",
    start_frame=0,
    end_frame=24,
    keyframes=[
        AnimationKeyframe(
            frame_index=0,
            transform=FrameTransform(scale=1.0, position_x=0)
        ),
        AnimationKeyframe(
            frame_index=24,
            transform=FrameTransform(scale=1.15, position_x=20)
        ),
    ],
)
```

## Future Parallax Usage

Independent animation clips for parallax:

```python
background_clip = AnimationClip(
    clip_id="background",
    start_frame=0,
    end_frame=48,
    keyframes=[...],
)

character_clip = AnimationClip(
    clip_id="character",
    start_frame=0,
    end_frame=48,
    keyframes=[...],
)

foreground_clip = AnimationClip(
    clip_id="foreground",
    start_frame=0,
    end_frame=48,
    keyframes=[...],
)
```

The renderer will later consume these evaluated states.

## Architecture Relationship

```
tools/frame/
├── models.py          ← FrameTransform, InterpolationType
├── palette/           ← CharacterColorPalette
├── transforms/        ← interpolate_transform
└── animation/         ← THIS MODULE
        ↓
Timeline + Keyframes
        ↓
evaluate_keyframe_at_frame
        ↓
AnimationFrame
        ↓
future tools/render/  ← RENDERING (not implemented)
```

## Known Limitations

1. **Only LINEAR interpolation** — Ease curves not yet supported
2. **No easing curves** — EASE_IN, EASE_OUT, BOUNCE, ELASTIC raise errors
3. **No shortest-angle rotation** — Rotation uses direct numeric interpolation
4. **No audio sync** — No audio timeline support
5. **No event system** — No trigger/action mechanisms

## Implementation Status

| Component | Status |
|-----------|--------|
| DEFAULT_FRAME_RATE | ✅ V1 |
| AnimationKeyframe | ✅ V1 |
| AnimationClip | ✅ V1 |
| AnimationTimeline | ✅ V1 |
| AnimationFrame | ✅ V1 |
| evaluate_keyframe_at_frame | ✅ V1 |
| evaluate_at_frame | ✅ V1 |
| generate_animation_frames | ✅ V1 |
| 24 FPS default | ✅ V1 |
| Tests | ✅ 48 tests |
| Documentation | ✅ This document |
