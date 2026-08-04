# Manga Tools

## Purpose

Manga Tools provides input, parsing, and extraction functionality for manga sources. This is currently an **architecture skeleton** — no actual manga processing is implemented.

## Architecture Direction

```
core ← tools/manga
```

Tools may consume Core data models when genuinely necessary.

## Package Structure

```
tools/
└── manga/
    ├── __init__.py       # Public API
    ├── exceptions.py     # Exception hierarchy
    ├── models.py         # Data models
    ├── parser/           # Parser boundary (future)
    ├── extractor/        # Extractor boundary (future)
    └── metadata/         # Metadata boundary (future)
```

## Dependency Rules

| Direction | Allowed? | Notes |
|-----------|----------|-------|
| core → tools/manga | ❌ | Core must not depend on Tools |
| integration → tools/manga | ❌ | Not yet allowed |
| runtime → tools/manga | ❌ | Not yet allowed |
| tools/manga → core | ✅ | Only when genuinely necessary |
| tools/manga → agents | ❌ | Forbidden |
| tools/manga → apps | ❌ | Forbidden |
| tools/manga → runtime | ❌ | Forbidden |

## Public API

```python
# Exceptions
from tools.manga import (
    MangaToolError,
    MangaParseError,
    MangaExtractionError,
    MangaMetadataError,
    MangaInputError,
)

# Models
from tools.manga import (
    MangaInput,
    MangaPage,
    MangaMetadata,
    MangaParseResult,
)
```

## Data Models

| Model | Purpose |
|-------|---------|
| `MangaInput` | Represents manga source (path or URL) |
| `MangaPage` | Represents a single manga page |
| `MangaMetadata` | Manga metadata (title, author, chapter) |
| `MangaParseResult` | Result of parsing operation |

## Package Boundaries

### tools/manga/parser

**Future responsibility:**
- Manga page parsing
- Chapter detection
- Page ordering

**Current status:** Architecture skeleton only.

### tools/manga/extractor

**Future responsibility:**
- Panel extraction
- Character region detection
- Speech bubble extraction

**Current status:** Architecture skeleton only.

### tools/manga/metadata

**Future responsibility:**
- Metadata extraction
- Metadata validation
- Metadata enrichment

**Current status:** Architecture skeleton only.

## Exception Hierarchy

```
MangaToolError
├── MangaParseError
├── MangaExtractionError
├── MangaMetadataError
└── MangaInputError
```

## Explicitly Excluded Functionality

The following are **NOT implemented** and should not be added without architectural review:

- OCR
- AI / LLM
- Image decoding/processing
- Computer vision
- Panel detection
- Character detection
- Speech bubble detection
- Filesystem crawling
- Network requests
- Web scraping
- GPU operations
- Threads/multiprocessing
- Rendering
- Video/audio processing

## Relationship to Core

Tools/manga may eventually produce data that maps to Core entities:
- `MangaMetadata` → `core.project.Project`
- `MangaPage` content → `core.scene.Scene`

However, this mapping should be defined in Integration or a dedicated adapter layer.

## Relationship to Runtime

Runtime provides execution infrastructure. Tools/manga should not depend on Runtime.

## Relationship to Future Agents

Agents will orchestrate the manga processing pipeline. This skeleton provides the input boundary that Agents will invoke.

## Implementation Status

| Component | Status |
|-----------|--------|
| Exception hierarchy | ✅ Implemented |
| Data models | ✅ Implemented |
| Parser boundary | ✅ Skeleton |
| Extractor boundary | ✅ Skeleton |
| Metadata boundary | ✅ Skeleton |
| Parser implementation | ❌ Not implemented |
| Extractor implementation | ❌ Not implemented |
| Metadata implementation | ❌ Not implemented |
| Tests | ✅ Basic tests |
| Documentation | ✅ This document |

## Known Limitations

1. **No parser implementation** — `parser/` is empty
2. **No extractor implementation** — `extractor/` is empty
3. **No metadata implementation** — `metadata/` is empty
4. **No file I/O** — models do not read/write files
5. **No network access** — no URL fetching

## Next Steps

To implement functional manga processing, the following would be needed:

1. Add parser implementation
2. Add extractor implementation
3. Add metadata handling
4. Integrate with Core/Integration for output
5. Consider Runtime for GPU-accelerated processing
