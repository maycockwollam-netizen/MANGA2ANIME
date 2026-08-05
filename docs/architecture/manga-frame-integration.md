# Manga to Frame Integration Contract

## Purpose

This document defines the integration boundary between `tools/manga/` and `tools/frame/` modules.

The integration contract provides a clean mapping from manga domain objects to frame domain objects without creating circular dependencies.

## Architecture

```
tools/manga/  -->  tools/manga_frame/  -->  tools/frame/
   (source)          (THIS BOUNDARY)        (target)
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `tools/manga/` | Parse manga sources, extract page metadata |
| `tools/manga_frame/` | Map manga objects to frame objects |
| `tools/frame/` | Frame/animation data contracts |

### Boundary Rules

1. **`tools/manga/` does NOT import `tools.frame`** - Manga is upstream
2. **`tools/frame/` does NOT import `tools.manga`** - Frame is downstream
3. **`tools/manga_frame/` imports both** - Acts as integration layer

## Input/Output Contracts

### Input: MangaFrameInput

```python
class MangaFrameInput(BaseModel):
    """Input contract for manga to frame conversion."""

    parse_result: MangaParseResult  # From tools.manga parser
    sequence_id: str              # Unique identifier
    name: str | None = None      # Optional human-readable name
    frame_rate: float = 24.0    # Target FPS
    character_palettes: dict[str, CharacterColorPalette] | None = None
```

### Output: MangaFrameOutput

```python
@dataclass(frozen=True)
class MangaFrameOutput:
    """Output of manga to frame conversion."""

    sequence: FrameSequence       # Converted frame sequence
    pages_converted: int        # Number of pages converted
    metadata_preserved: bool    # Whether metadata was preserved
    palettes_provided: bool     # Whether palettes were provided
```

## Mapping Table

### MangaPage → Frame

| MangaPage Field | Frame Field | Notes |
|----------------|-------------|-------|
| `page_number` | `frame_index` | Zero-based index |
| `file_path` | `source_path` | Path to manga page file |
| `file_path` | `FrameLayer.source_path` | Layer also references source |
| `width` | _(ignored)_ | Image processing not in scope |
| `height` | _(ignored)_ | Image processing not in scope |

### MangaParseResult → FrameSequence

| MangaParseResult Field | FrameSequence Field | Notes |
|------------------------|---------------------|-------|
| `pages` | `frames` | Each page becomes a Frame |
| `metadata.title` | `name` | If no explicit name provided |
| `metadata.chapter` | `name` | Appended to title |
| _(none)_ | `transitions` | Always empty for basic conversion |

### MangaMetadata → FrameSequence

| MangaMetadata Field | FrameSequence Field | Notes |
|--------------------|---------------------|-------|
| `title` | `name` | Part of name if available |
| `chapter` | `name` | Appended as "Chapter N" |
| `author` | _(ignored)_ | Not in frame scope |
| `chapter_title` | _(ignored)_ | Not in frame scope |
| `source` | _(ignored)_ | Not in frame scope |

### CharacterColorPalette

| CharacterPalette | Notes |
|-----------------|-------|
| Must be **explicitly provided** | Color extraction NOT in scope |
| Keyed by `character_id` | Used for future coloring |
| Associated via input contract | Not auto-mapped |

## Validation Ownership

| Validation | Owner | Location |
|------------|-------|----------|
| MangaInput validation | `tools/manga/parser/` | MangaParser |
| MangaPage validation | `tools/manga/models/` | MangaPage model |
| MangaParseResult validation | `tools/manga/parser/` | MangaParser |
| Frame validation | `tools/frame/models/` | Frame model |
| FrameSequence validation | `tools/frame/models/` | FrameSequence model |
| Transition validation | `tools/frame/models/` | FrameSequence model validator |
| Cross-reference validation | `tools/manga_frame/` | convert_manga_to_frames() |

### Integration-level Validation

The boundary adapter performs:
- Empty pages check (cannot convert empty manga)
- Sequence ID uniqueness (delegated to FrameSequence)

### NOT Performed by Boundary

The boundary does NOT perform:
- Image decoding or loading
- Color extraction from images
- Character segmentation
- Automatic palette generation
- OCR or text recognition
- Animation execution

## Immutability

### Output Guarantees

| Property | Guarantee |
|----------|-----------|
| `FrameSequence` | Frozen/immutable |
| `FrameSequence.frames` | Tuple (immutable) |
| `Frame.layers` | Tuple (immutable) |
| `MangaFrameOutput` | Frozen dataclass |

### Source Protection

- Input `MangaParseResult` is NOT modified
- Input `MangaPage` objects are NOT modified
- Output is constructed from copies/derived values

## Determinism

Same input produces same output:

```
input = MangaFrameInput(parse_result=..., sequence_id="x", ...)
output1 = convert_manga_to_frames(input)
output2 = convert_manga_to_frames(input)
assert output1 == output2
```

No randomness, timestamps, or environment-dependent values.

## Forbidden Responsibilities

The integration contract does NOT:

- Load or decode images
- Perform color extraction
- Generate CharacterColorPalette automatically
- Execute animations
- Render frames
- Access GPU
- Call AI/LLM
- Access network
- Perform filesystem crawling

## Usage Example

```python
from pathlib import Path
from tools.manga import MangaParser, MangaInput
from tools.manga_frame import create_frame_sequence_from_manga

# Parse manga
parser = MangaParser()
result = parser.parse(MangaInput(path=Path("/manga/chapter1")))

# Convert to frames
sequence = create_frame_sequence_from_manga(
    parse_result=result,
    sequence_id="chapter1_frames",
    name="Chapter 1 - The Beginning",
    frame_rate=24.0,
)

# Result is a frozen FrameSequence
assert isinstance(sequence, FrameSequence)
```

## Future Extension Points

1. **Layer extraction** - Detect and extract character layers from manga pages
2. **Automatic palette generation** - Extract colors from manga images (requires image processing)
3. **Character tracking** - Map characters across pages
4. **Animation metadata** - Generate Ken Burns or parallax effects
5. **Transition inference** - Analyze panel layout for transition types

These extensions would modify the mapping rules but NOT the contract structure.

## Module Dependencies

```
tools/manga_frame/
    ├── tools.manga (models, parser)
    ├── tools.frame (models, palette)
    └── standard library

tools/manga/
    └── standard library + pydantic

tools/frame/
    └── standard library + pydantic
```

## Test Coverage

| Test Class | Coverage |
|------------|----------|
| `TestMangaFrameInput` | Input contract validation |
| `TestConvertMangaToFrames` | Mapping logic |
| `TestCreateFrameSequenceFromManga` | Factory function |
| `TestImmutability` | Immutability guarantees |
| `TestDeterminism` | Deterministic behavior |
| `TestBoundaryViolations` | Architecture rules |

## Implementation Status

| Component | Status |
|-----------|--------|
| MangaFrameInput | Implemented |
| MangaFrameOutput | Implemented |
| convert_manga_to_frames() | Implemented |
| create_frame_sequence_from_manga() | Implemented |
| Boundary tests | Implemented |
| Documentation | This document |
