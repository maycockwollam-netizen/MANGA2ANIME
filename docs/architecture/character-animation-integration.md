# Character Animation Integration Contracts

## Purpose

This document defines the structural integration boundary between character tracking output and animation data structures in the MANGA2ANIME pipeline.

**Character → Animation Integration V1 defines structural bindings only.**
**It does not generate animation, keyframes, transforms, interpolation, motion, or rendered frames.**

This module creates the structural contract needed by a future animation implementation.

## Scope

The contracts define:
- Character animation target identity
- Binding between character references and animation targets
- Input/output contracts for structural mapping
- Validation for structural references only

## Architecture

```
tools/manga/
        |
        v
tools/manga_frame/
        ├── layer_extraction/
        ├── character_tracking/
        ├── character_frame/
        └── character_animation/  (THIS MODULE)
                        |
                        v
                tools/frame/animation/
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `tools/manga/` | Parse manga sources |
| `tools/manga_frame/character_tracking/` | Character tracking contracts |
| `tools/manga_frame/character_frame/` | Map tracking to frame structures |
| `tools/manga_frame/character_animation/` | Bind characters to animation targets |
| `tools/frame/animation/` | Actual animation generation |

## Public API

### Identity Contract

#### CharacterAnimationTarget

Immutable target identity for character animation.

```python
@dataclass(frozen=True, slots=True)
class CharacterAnimationTarget:
    """Immutable target identity for character animation."""

    character_id: str
    layer_id: str | None
    sequence_id: str
```

### Binding Contract

#### CharacterAnimationBinding

Structural binding from character to animation target.

```python
@dataclass(frozen=True, slots=True)
class CharacterAnimationBinding:
    """Structural binding from character to animation target."""

    target: CharacterAnimationTarget
    frame_index: int
    palette_id: str | None
```

### Metadata Contract

#### CharacterAnimationMetadata

Immutable metadata about the binding operation.

```python
class CharacterAnimationMetadata(BaseModel):
    """Metadata for character animation binding operation."""

    model_config = {"frozen": True}

    bindings_created: int
    characters_bound: int
    palettes_available: int
    palettes_missing: int
```

### Input Contract

#### CharacterAnimationInput

Input boundary for binding operation.

```python
class CharacterAnimationInput(BaseModel):
    """Input contract for character animation binding."""

    sequence_id: str
    frame_count: int
    palette_associations: tuple[tuple[str, str], ...]
```

### Output Contract

#### CharacterAnimationOutput

Immutable output contract.

```python
@dataclass(frozen=True)
class CharacterAnimationOutput:
    """Output of character animation binding operation."""

    sequence_id: str
    bindings: tuple[CharacterAnimationBinding, ...]
    metadata: CharacterAnimationMetadata
```

### Main Function

```python
def build_character_animation_bindings(
    input_contract: CharacterAnimationInput,
    references: tuple,
) -> CharacterAnimationOutput:
    """Build structural bindings from character references to animation targets."""
```

## Mapping Rules

| Source | Target | Notes |
|--------|--------|-------|
| `CharacterFrameReference.character_id` | `CharacterAnimationTarget.character_id` | Preserved |
| `CharacterFrameReference.layer_index` | `CharacterAnimationTarget.layer_id` | int → str conversion |
| `CharacterFrameReference.frame_index` | `CharacterAnimationBinding.frame_index` | Preserved |
| `palette_associations` | `CharacterAnimationBinding.palette_id` | Lookup by character |

**Note:** `layer_index` (int, Z-order) is converted to `layer_id` (str) for target identity.

## What This Module Does NOT Do

This module intentionally does NOT implement:

- **Keyframe generation** - Belongs to `tools/frame/animation`
- **Transform interpolation** - Belongs to `tools/frame/animation`
- **Motion calculation** - Belongs to `tools/frame/animation`
- **AnimationClip creation** - Belongs to `tools/frame/animation`
- **AnimationKeyframe creation** - Belongs to `tools/frame/animation`
- **Easing functions** - Belongs to `tools/frame/animation`
- **Frame evaluation** - Belongs to `tools/frame/animation`
- **Timeline modification** - Belongs to `tools/frame/animation`

## Validation Rules

| Validation | Behavior |
|-----------|----------|
| `frame_index` exceeds `frame_count` | Reject |
| Empty `sequence_id` | Reject |
| Negative `frame_index` | Reject |
| Invalid frame reference | Reject |

## Palette Behavior

| Scenario | Behavior |
|---------|----------|
| Palette provided | Preserved in binding |
| Palette not provided | `palette_id = None` |
| Palette missing | Reported in metadata |

**Important:** This module does NOT generate or infer palettes.

## Immutability Guarantees

| Contract | Frozen | Rationale |
|----------|--------|-----------|
| `CharacterAnimationOutput` | ✅ Yes | Output contract |
| `CharacterAnimationBinding` | ✅ Yes | Frozen dataclass |
| `CharacterAnimationTarget` | ✅ Yes | Frozen dataclass |
| `CharacterAnimationMetadata` | ✅ Yes | Immutable metadata |
| `CharacterAnimationInput` | ❌ No | Input contract |

## Serialization

Structural contracts support serialization:

```python
# Target serialization
data = target.model_dump()

# Binding serialization
data = binding.model_dump()
```

## Determinism

The integration is deterministic:

- Same input produces same output
- Bindings are sorted by `(character_id, frame_index)`
- No random values
- No timestamps
- No UUID generation

## Dependency Graph

```
tools/manga_frame/character_animation/
    ├── Python standard library
    ├── pydantic
    └── tools.frame.animation (for future integration)

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

The character animation integration does NOT:

- Generate keyframes
- Interpolate transforms
- Calculate motion
- Create AnimationClip
- Create AnimationKeyframe
- Modify AnimationTimeline
- Render anything
- Perform image processing
- Access GPU
- Access network

## Known Limitations

1. **No animation generation** - This module creates structural bindings only
2. **No transform interpolation** - Belongs to `tools/frame/animation`
3. **No keyframe generation** - Belongs to `tools/frame/animation`

## Future Extension Points

### Animation Construction

Future modules may implement:
- Keyframe generation from character positions
- Transform interpolation between appearances
- AnimationClip construction from bindings
- Easing function application

### Integration with tools/frame/animation

Future integration may connect:
- Bindings to AnimationClip generation
- Target identity to AnimationClip.clip_id
- Palette associations to colorization

## Implementation Status

| Component | Status |
|-----------|--------|
| CharacterAnimationTarget | Implemented |
| CharacterAnimationBinding | Implemented |
| CharacterAnimationMetadata | Implemented |
| CharacterAnimationInput | Implemented |
| CharacterAnimationOutput | Implemented |
| build_character_animation_bindings | Implemented |
| Deep Immutability | Implemented |
| Structural Validation | Implemented |
| Palette Preservation | Implemented |
| Tests | Implemented |
| Documentation | This document |
| Keyframe Generation | NOT IMPLEMENTED |
| Transform Interpolation | NOT IMPLEMENTED |
| Motion Calculation | NOT IMPLEMENTED |
| AnimationClip Creation | NOT IMPLEMENTED |
