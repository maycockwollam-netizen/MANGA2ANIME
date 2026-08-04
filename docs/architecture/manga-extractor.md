# Manga Extractor

## Purpose

The Manga Extractor (`tools/manga/extractor/`) V1 provides **metadata-level extraction validation and statistics** from `MangaParseResult`. It does NOT perform image processing, OCR, or visual extraction.

## Architecture

```
MangaParseResult → MangaExtractor → ExtractionResult
```

## Input

```python
MangaParseResult
├── metadata: MangaMetadata
├── pages: list[MangaPage]
└── total_pages: int
```

## Output

### ExtractionResult

```python
ExtractionResult
├── total_pages: int
├── pages: list[PageExtraction]
├── known_dimensions: int
├── missing_dimensions: int
├── valid: bool
└── validation_errors: list[str]
```

### PageExtraction

```python
PageExtraction
├── page_number: int
├── file_path: str | None
├── width: int | None
├── height: int | None
└── has_dimensions: bool
```

## Public API

```python
from tools.manga.extractor import MangaExtractor, extract

# Function API
result = extract(parse_result)

# Class API
extractor = MangaExtractor()
result = extractor.extract(parse_result)
```

## Validation Behavior

The extractor validates the incoming `MangaParseResult`:

### Page Numbering

| Check | Behavior |
|-------|----------|
| Empty pages | Returns `valid=False` with error |
| Wrong starting number | Returns `valid=False` with error |
| Duplicate numbers | Returns `valid=False` with error |
| Missing numbers | Returns `valid=False` with error |
| Negative numbers | Returns `valid=False` with error |

### total_pages Consistency

If `total_pages != len(pages)`, raises `MangaExtractionError`.

## Dimension Handling

The extractor reports dimension statistics based on existing `MangaPage` metadata:

| Scenario | `known_dimensions` | `missing_dimensions` |
|----------|-------------------|----------------------|
| All pages have width+height | N | 0 |
| No pages have dimensions | 0 | N |
| Mixed | K | M |

**V1 does NOT:**
- Open image files
- Decode images
- Inspect image headers
- Calculate dimensions
- Modify MangaPage objects

## Determinism

The extractor is fully deterministic:

- Same `MangaParseResult` → Same `ExtractionResult`
- No randomness
- No timestamps
- No global mutable state
- No filesystem access
- No network access

## Mutation Safety

The extractor treats input as **read-only**:

```python
result = extractor.extract(parse_result)
# parse_result is unchanged
```

The original `MangaPage` objects and `MangaParseResult` are never modified.

## Exception Handling

Uses the existing exception hierarchy:

```python
MangaToolError
├── MangaExtractionError  # Used for critical validation failures
├── MangaParseError
├── MangaMetadataError
└── MangaInputError
```

**MangaExtractionError** is raised when:
- `total_pages` mismatch is detected

Non-critical validation errors are collected in `validation_errors` list.

## Explicit Non-Responsibilities (V1)

The extractor does NOT implement:

- Image processing
- Image decoding
- Image inspection
- Pixel analysis
- OCR
- Panel detection
- Character detection
- Speech bubble detection
- Computer vision
- AI/LLM processing
- GPU processing
- Rendering
- Network access
- Web scraping
- Filesystem crawling
- Archive extraction
- Runtime execution

## Dependency Boundary

```
tools/manga/extractor
    ├── tools/manga/models (existing)
    ├── tools/manga/exceptions (existing)
    └── Python standard library
```

The extractor has **no dependencies** on:
- `runtime/`
- `agents/`
- `apps/`
- GPU libraries
- Image processing libraries
- ML frameworks
- Network clients

## Future Extension Points

Future layers may implement:

- Panel extraction from images
- Character region detection
- Speech bubble detection
- OCR for text extraction
- Image dimension detection
- Computer vision processing

These are explicitly deferred to future implementation.

## Implementation Status

| Feature | Status |
|---------|--------|
| Page extraction | ✅ Implemented |
| Page validation | ✅ Implemented |
| Dimension statistics | ✅ Implemented |
| Mutation safety | ✅ Implemented |
| Exception handling | ✅ Implemented |
| Deterministic behavior | ✅ Implemented |
| Tests | ✅ Comprehensive |
| Documentation | ✅ This document |
