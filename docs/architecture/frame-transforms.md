# Frame Transforms

## Purpose

The Frame Transforms (`tools/frame/transforms/`) V1 provides **pure, deterministic transformation logic** for frame/layer transforms. It converts validated `FrameTransform` data into transformation results for consumption by future animation/rendering layers.

> Transforms V1 defines mathematical transformation logic only. It does not perform image manipulation, rendering, or GPU operations.

## Public API

```python
from tools.frame.transforms import (
    TransformResult,       # Immutable transformation result
    apply_transform,       # Apply single transform
    compose_transforms,    # Compose multiple transforms
    interpolate_transform, # Linear interpolation between transforms
    lerp_float,           # Linear interpolation helper
    identity_transform,    # Create identity transform
)
```

## TransformResult

Immutable result of applying transformations.

```python
@dataclass(frozen=True, slots=True)
class TransformResult:
    position_x: float   # Final X position
    position_y: float   # Final Y position
    scale: float        # Final scale factor
    rotation_deg: float # Final rotation in degrees
    opacity: float      # Final opacity (0-1)
    anchor_x: float     # Anchor X point used
    anchor_y: float     # Anchor Y point used
```

## Mathematical Semantics

### Translation

Translation offsets are added to position:

```
final_x = origin_x + position_x
final_y = origin_y + position_y
```

### Scale

Scale factors are multiplicative:

```
final_scale = scale_1 * scale_2 * ... * scale_n
```

### Rotation

Rotation values are additive:

```
final_rotation = rotation_1 + rotation_2 + ... + rotation_n
```

### Opacity

Opacity uses the last value in composition (no blending):

```
final_opacity = last_transform.opacity
```

### Anchor

Anchor points use the last value in composition:

```
final_anchor_x = last_transform.anchor_x
final_anchor_y = last_transform.anchor_y
```

## Composition Order

When composing multiple transforms, they are applied **in order** (first to last in the list):

```
T1 → T2 → T3 → ... → Tn
```

For each transform T_i:
1. Add T_i's position to cumulative position
2. Multiply T_i's scale with cumulative scale
3. Add T_i's rotation to cumulative rotation
4. Use T_i's opacity (last wins)
5. Use T_i's anchor (last wins)

## Anchor Behavior

The anchor point represents a normalized position (0-1) within an element:
- `(0.0, 0.0)` = top-left
- `(0.5, 0.5)` = center
- `(1.0, 1.0)` = bottom-right

The transform applies around this anchor point.

## Interpolation Semantics

Linear interpolation is used for all parameters:

```
result = start + (end - start) * t
```

Where `t` is in range `[0.0, 1.0]`:
- `t = 0.0` → start value
- `t = 1.0` → end value
- `t = 0.5` → midpoint

### Rotation Interpolation

Rotation uses **direct numeric interpolation**, not shortest-angle:

```python
# Example: interpolating 350° to 10°
# Direct: 350 + (10 - 350) * 0.5 = 180°
# Shortest-path would give: 180° (going the other way)
```

## Determinism Guarantees

All transform operations are:
- Fully deterministic
- No random values
- No timestamps
- No global state
- No I/O operations
- Same inputs → identical outputs

## Mutation Guarantees

Source `FrameTransform` objects are never mutated:
- All functions are pure
- Original data is preserved
- New instances are returned

## Dependencies

```
tools/frame/transforms
    ├── standard library (dataclasses)
    ├── tools.frame.models (FrameTransform)
    └── tools.frame.exceptions (via FrameTransform)
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
- ❌ GPU libraries

## Explicit Non-Responsibilities

The transforms module does NOT:
- ❌ Perform image manipulation
- ❌ Execute rendering
- ❌ Access GPU
- ❌ Perform I/O operations
- ❌ Implement easing curves (beyond linear)
- ❌ Implement animation playback
- ❌ Implement timeline management
- ❌ Render to video/audio
- ❌ Apply transforms to actual images

## Future Extension Points

### Easing Functions

Future may add easing curve implementations:
- Ease-in
- Ease-out
- Ease-in-out
- Bounce
- Elastic

### Non-Linear Interpolation

Future may add shortest-angle rotation interpolation.

### Transform Matrices

Future may add 2D/3D transformation matrices.

## Known Limitations

1. **No easing curves** — Only linear interpolation is implemented
2. **No shortest-angle rotation** — Rotation uses direct numeric interpolation
3. **No blending** — Opacity uses last-value-wins, not alpha blending
4. **No matrix operations** — Only basic parameter composition

## Implementation Status

| Component | Status |
|-----------|--------|
| TransformResult | ✅ V1 |
| apply_transform | ✅ V1 |
| compose_transforms | ✅ V1 |
| interpolate_transform | ✅ V1 |
| lerp_float | ✅ V1 |
| identity_transform | ✅ V1 |
| Tests | ✅ 47 tests |
| Documentation | ✅ This document |
