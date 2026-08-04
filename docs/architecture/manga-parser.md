# Manga Parser

## Purpose

The Manga Parser (`tools/manga/parser/`) converts manga input sources (directories, archives) into structured page metadata. It is a **pure input/parsing layer** with no image processing, AI, or network functionality.

## Architecture

```
MangaInput → MangaParser → MangaParseResult
```

## Supported Inputs

### Directory Input

Parses a local directory containing manga page images.

```
chapter_12/
├── 001.jpg
├── 002.jpg
├── 003.jpg
└── cover.png
```

### ZIP Archive Input

Parses a ZIP archive containing manga page images.

```
chapter_12.zip
├── 001.jpg
├── 002.jpg
└── 003.jpg
```

## Supported Image Extensions

| Extension | Case-Insensitive |
|-----------|------------------|
| `.jpg` | ✅ |
| `.jpeg` | ✅ |
| `.png` | ✅ |
| `.webp` | ✅ |

Unsupported files (e.g., `.gif`, `.pdf`, `.txt`) are ignored.

## Natural Sorting

The parser implements **natural sorting** to ensure correct page order:

```
Input:  1.jpg, 10.jpg, 2.jpg, 3.jpg
Output: 1.jpg, 2.jpg, 3.jpg, 10.jpg
```

Handles mixed text and numbers:

```
Input:  page1.jpg, page10.jpg, page2.jpg
Output: page1.jpg, page2.jpg, page10.jpg
```

## Page Numbering

Pages are assigned sequential indices starting from `0`:

| Index | File |
|-------|------|
| 0 | 001.jpg |
| 1 | 002.jpg |
| 2 | 003.jpg |
| n | (n+1).jpg |

The `page_number` field uses 0-based indexing as defined by the existing `MangaPage` model.

## Chapter Extraction

The parser extracts chapter numbers from path names using pattern matching:

| Pattern | Example | Result |
|---------|---------|--------|
| `chapter_N` | `chapter_12/` | `chapter = 12` |
| `chapter-N` | `chapter-5/` | `chapter = 5` |
| `Chapter N` | `Chapter 10/` | `chapter = 10` |
| ZIP name | `chapter_7.zip` | `chapter = 7` |

If no chapter number is detected, `metadata.chapter` remains `None`.

## Error Behavior

| Error | Exception | Condition |
|-------|-----------|-----------|
| Missing input | `MangaInputError` | No path or URL provided |
| Nonexistent path | `MangaInputError` | Path does not exist |
| Unsupported file type | `MangaInputError` | Non-ZIP/non-image file |
| URL input | `MangaInputError` | URL provided (V1 limitation) |
| No images found | `MangaParseError` | Directory/ZIP has no supported images |
| Malformed ZIP | `MangaParseError` | Corrupted archive |

## URL Limitation

**Parser V1 does not support URL input.** URLs will raise `MangaInputError` with a message indicating this limitation.

Network functionality is intentionally deferred to a future layer.

## Explicit Non-Responsibilities

The parser does NOT implement:

- OCR
- AI/LLM calls
- Image decoding/processing
- Computer vision
- Panel detection
- Character detection
- Speech bubble detection
- GPU operations
- Rendering
- Network requests
- Web scraping
- Multiprocessing
- Background workers

## Public API

```python
from tools.manga.parser import MangaParser

parser = MangaParser()
result = parser.parse(manga_input)
```

### MangaParser

```python
class MangaParser:
    def parse(self, manga_input: MangaInput) -> MangaParseResult:
        """Parse manga input and return structured result."""
```

### Supported Extensions

```python
from tools.manga.parser import SUPPORTED_EXTENSIONS
# frozenset({'.jpg', '.jpeg', '.png', '.webp'})
```

## Dependency Boundary

```
tools/manga/parser
    └── tools/manga/models (existing)
    └── tools/manga/exceptions (existing)
    └── standard library only
```

The parser has **no runtime dependencies** on:
- `runtime/`
- `agents/`
- `apps/`
- `core/` (intentionally)

## Deterministic Behavior

The parser produces deterministic, repeatable results:

- Same input → Same output
- No randomness
- No side effects
- No caching
- No global state

## Implementation Status

| Feature | Status |
|---------|--------|
| Directory parsing | ✅ Implemented |
| ZIP parsing | ✅ Implemented |
| Natural sorting | ✅ Implemented |
| Supported extensions | ✅ Implemented |
| Chapter extraction | ✅ Implemented |
| Input validation | ✅ Implemented |
| URL rejection | ✅ Implemented |
| Error handling | ✅ Implemented |
| Tests | ✅ Comprehensive |
| Documentation | ✅ This document |
