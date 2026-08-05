# Frame Palette

## Purpose

The Frame Palette (`tools/frame/palette/`) V1 provides **character color palette contracts** for the Motion Comic pipeline. It defines the canonical colors for each character as an immutable, validated data contract.

> Palette V1 defines the color contract. It does not perform colorization.

## Deep Immutability

The `CharacterColorPalette` provides deep immutability guarantees:

- **The palette is frozen** - Cannot modify any field after creation
- **`custom_colors` is stored as `tuple[tuple[str, str], ...]`** - Sorted for deterministic ordering
- **Source dictionary modifications are protected** - Modifying the input dict after construction doesn't affect the palette

```python
palette = CharacterColorPalette(
    character_id="naruto",
    hair="#FF9900",
    skin="#FFCC99",
    eyes="#4477EE",
    outfit="#FFCC00",
    custom_colors={"cape": "#FF0000"},
)

# These raise exceptions:
palette.hair = "#000000"  # Frozen instance
palette.custom_colors.append(...)  # Tuple has no append
```

## Character Color Consistency Concept

```
Character
    |
    v
CharacterColorPalette
    |
    v
LOCKED, VALIDATED, IMMUTABLE COLOR CONTRACT
             |
             v
    future Colorization Agent
             |
             v
      colorized panels
```

The Colorization Agent will READ this palette as the **single source of truth**. It must NOT modify the palette.

## CharacterColorPalette

### Data Model

```python
CharacterColorPalette (frozen/immutable, deep immutability)
|-- character_id: str          # Unique character identifier (required, non-empty)
|-- hair: str                  # Hair color in HEX (#RRGGBB)
|-- skin: str                  # Skin color in HEX
|-- eyes: str                  # Eye color in HEX
|-- outfit: str                # Primary outfit color in HEX
|-- accessories: str | None    # Accessories color in HEX (optional)
|-- custom_colors: tuple[tuple[str, str], ...]  # Sorted, IMMUTABLE tuple
```

### Color Roles

| Role | Required | Description |
|------|----------|-------------|
| `character_id` | Yes | Unique identifier for the character |
| `hair` | Yes | Hair color |
| `skin` | Yes | Skin color |
| `eyes` | Yes | Eye color |
| `outfit` | Yes | Primary outfit/clothing color |
| `accessories` | No | Accessories color (e.g., headband, weapons) |
| `custom_colors` | No | Additional named color mappings, sorted for determinism |

### Example

```python
from tools.frame.palette import CharacterColorPalette

palette = CharacterColorPalette(
    character_id="naruto",
    hair="#FF9900",
    skin="#FFCC99",
    eyes="#4477EE",
    outfit="#FFCC00",
    accessories="#333333",
    custom_colors={"cape": "#FF0000", "headband": "#FFFFFF"},
)

# custom_colors is stored as sorted tuple of tuples
# palette.custom_colors == (("cape", "#FF0000"), ("headband", "#FFFFFF"))
```

## HEX Validation

### Accepted Format

```python
#RRGGBB  # 6 hexadecimal digits, case-insensitive input
```

### Examples

| Input | Normalized Output |
|-------|-------------------|
| `#FF0000` | `#FF0000` |
| `#ff0000` | `#FF0000` |
| `#aabbcc` | `#AABBCC` |
| `#ABCDEF` | `#ABCDEF` |

### Rejected Formats

| Input | Reason |
|-------|--------|
| `red` | Color names not accepted |
| `123456` | Missing `#` prefix |
| `#FFF` | Wrong length (3 vs 6) |
| `#GGGGGG` | Invalid hex characters |
| `##FFFFFF` | Double `#` prefix |

## Normalization

All HEX colors are normalized to **uppercase canonical representation**.

```python
palette = CharacterColorPalette(
    character_id="test",
    hair="#ff9900",
    skin="#FFCC99",
    ...
)
# Both are normalized to uppercase
# palette.hair == "#FF9900"
# palette.skin == "#FFCC99"
```

## Immutability Guarantees

| Protection | Mechanism |
|-----------|-----------|
| Field mutation | `frozen=True` on model |
| Collection mutation | `tuple` instead of `dict` |
| Source dict protection | Copied and converted at construction |
| Nested tuple protection | Tuples are inherently immutable |

```python
# Source dict modification protection
source = {"cape": "#FF0000"}
palette = CharacterColorPalette(
    character_id="test",
    hair="#FF0000",
    skin="#FFFFFF",
    eyes="#000000",
    outfit="#FFFFFF",
    custom_colors=source,
)
source["cape"] = "#00FF00"  # Palette unaffected
# palette.custom_colors still has "#FF0000"
```

## Character ID Validation

| Input | Behavior |
|-------|----------|
| `"character1"` | Valid |
| `""` | Rejected (empty) |
| `"   "` | Rejected (whitespace-only) |
| `"  id  "` | Normalized to `"id"` |

## Serialization

All palettes support Pydantic serialization:

```python
# Dict serialization
data = palette.model_dump()

# JSON serialization
json_str = palette.model_dump_json()

# Round-trip reconstruction
reconstructed = CharacterColorPalette(**data)
assert reconstructed == palette
```

**Note:** `custom_colors` is serialized as a list of tuples in JSON, which is JSON-compatible.

## Dependency Boundary

```
tools/frame/palette
    |-- standard library (re)
    +-- pydantic (existing dependency)
```

**Forbidden dependencies:**
- runtime
- agents
- apps
- core
- torch/tensorflow
- opencv/PIL
- diffusers/transformers
- requests/httpx
- FFmpeg/MoviePy

## Explicit Non-Responsibilities

The palette module does NOT:

- Perform colorization
- Generate colors
- Use AI/LLM inference
- Process images
- Segment characters
- Detect colors from images
- Access external APIs
- Render panels
- GPU operations

## Future Colorization Agent Integration

```
CharacterColorPalette (this module)
        |
        v
future Colorization Agent
        |
        v
  reads palette colors
        |
        v
  applies to character regions
        |
        v
   Colorized Panel Output
```

The Colorization Agent will:
1. READ `CharacterColorPalette` for canonical colors
2. NOT modify the palette
3. Apply colors to detected character regions
4. Output colorized panels

## Known Limitations

1. **No AI inference** - Palette must be manually defined or sourced from another system
2. **No automatic color extraction** - Colors cannot be detected from images automatically
3. **Fixed color schema** - Limited to hair, skin, eyes, outfit, accessories, and custom colors
4. **No image processing** - Cannot apply colors to images directly

## Implementation Status

| Feature | Status |
|---------|--------|
| CharacterColorPalette model | Implemented |
| Character ID validation | Implemented |
| HEX validation | Implemented |
| Canonical normalization | Implemented |
| Deep Immutability | Implemented |
| Serialization | Implemented |
| Tests | 30+ tests |
| Documentation | This document |
