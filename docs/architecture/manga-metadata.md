# Manga Metadata

## Purpose

The Manga Metadata (`tools/manga/metadata/`) V1 provides **metadata normalization and validation** for `MangaMetadata`. It does NOT fetch metadata from external sources.

## Architecture

```
MangaMetadata → MangaMetadataProcessor → MetadataResult
```

## Input

```python
MangaMetadata
├── title: str | None
├── author: str | None
├── chapter: int | None
├── chapter_title: str | None
└── source: str | None
```

## Output

### MetadataResult

```python
MetadataResult
├── metadata: MangaMetadata
├── valid: bool
└── validation_errors: list[str]
```

## Public API

```python
from tools.manga.metadata import MangaMetadataProcessor, process

# Function API
result = process(metadata)

# Class API
processor = MangaMetadataProcessor()
result = processor.process(metadata)
```

## Normalization Rules

The processor applies deterministic normalization:

| Field | Rule |
|-------|------|
| `title` | Trim whitespace, empty string → `None` |
| `author` | Trim whitespace, empty string → `None` |
| `chapter` | No normalization (integer) |
| `chapter_title` | Trim whitespace, collapse internal spaces, empty → `None` |
| `source` | Trim whitespace, empty string → `None` |

## Validation Rules

| Check | Behavior |
|-------|----------|
| Chapter < 1 | Returns `valid=False` with error |
| Chapter >= 1 | Valid |
| Chapter = `None` | Valid (optional field) |

All other fields are optional and do not produce validation errors.

## Determinism

The processor is fully deterministic:

- Same `MangaMetadata` → Same `MetadataResult`
- No randomness
- No timestamps
- No global mutable state
- No filesystem access
- No network access

## Mutation Safety

The processor creates a **normalized copy** without mutating the original:

```python
result = process(metadata)
# metadata is unchanged
# result.metadata is a new object
```

## Exception Behavior

V1 does not raise exceptions for metadata validation failures. Non-critical validation errors are collected in the `validation_errors` list and `valid` is set to `False`.

The existing `MangaMetadataError` exception class exists in the exception hierarchy but is not raised in V1.

## Explicit Non-Responsibilities (V1)

The metadata processor does NOT:

- Fetch metadata from the internet
- Scrape metadata from websites
- Use OCR to extract metadata
- Use AI/LLM to generate metadata
- Access external APIs
- Inspect image contents
- Create database records
- Cache metadata
- Perform network requests

## Dependency Boundary

```
tools/manga/metadata
    ├── tools/manga/models (existing)
    ├── tools/manga/exceptions (existing, not used in V1)
    └── Python standard library
```

The metadata processor has **no dependencies** on:
- `runtime/`
- `agents/`
- `apps/`
- GPU libraries
- Network clients
- Image processing libraries
- External APIs

## Future Extension Points

Future layers may implement:

- External metadata fetching (e.g., manga APIs)
- AI-assisted metadata enrichment
- OCR-based text extraction for metadata
- Database integration for metadata storage
- Web scraping for metadata lookup

These are explicitly deferred to future implementation.

## Implementation Status

| Feature | Status |
|---------|--------|
| Metadata normalization | ✅ Implemented |
| Metadata validation | ✅ Implemented |
| Mutation safety | ✅ Implemented |
| Deterministic behavior | ✅ Implemented |
| Tests | ✅ Comprehensive |
| Documentation | ✅ This document |
