# Core Asset Module

## Purpose

The `core/asset` module defines the **asset data model** for Manga2Anime. It represents asset identity, metadata, types, references, properties, and state.

**This module does NOT:**
- Load or decode assets
- Process images or videos
- Decode audio
- Generate thumbnails
- Manage asset storage
- Perform network requests
- Render assets
- Upload to CDN
- Run AI generation

## Overview

```
core/asset/
├── __init__.py       # Public API exports
├── asset.py          # Main Asset model
├── types.py          # AssetType enum
├── metadata.py       # AssetMetadata
├── reference.py      # AssetReference
├── properties.py     # AssetProperties
├── state.py         # AssetState
├── validator.py     # AssetValidator
├── collection.py    # AssetCollection
├── serialization.py # JSON serialization
└── exceptions.py     # Asset exceptions
```

## Core Concepts

### Asset

The main asset model representing identity and properties.

```python
from core.asset import Asset, AssetType

asset = Asset(
    name="hero_sprite",
    asset_type=AssetType.SPRITE,
)
```

**Attributes:**
- `id`: Unique asset identifier (UUID)
- `name`: Internal asset name
- `asset_type`: AssetType enum
- `metadata`: AssetMetadata
- `reference`: AssetReference
- `properties`: AssetProperties
- `state`: AssetState

### AssetType

Enum representing asset categories.

```python
from core.asset import AssetType

# Image types
AssetType.IMAGE
AssetType.MANGA_PAGE
AssetType.CHARACTER_REFERENCE
AssetType.BACKGROUND
AssetType.SPRITE
AssetType.TEXTURE

# Audio types
AssetType.AUDIO
AssetType.VOICE
AssetType.MUSIC
AssetType.SFX

# Video types
AssetType.VIDEO
AssetType.ANIMATION

# Other
AssetType.FONT
AssetType.DATA
AssetType.OTHER
```

**Classification helpers:**
```python
AssetType.is_image(AssetType.SPRITE)  # True
AssetType.is_audio(AssetType.VOICE)   # True
AssetType.is_video(AssetType.VIDEO)   # True
```

### AssetMetadata

Structured metadata for assets.

```python
from core.asset import AssetMetadata

metadata = AssetMetadata(
    name="hero_sprite",
    display_name="Hero Sprite",
    description="Main character sprite sheet",
    tags=["character", "hero"],
    author="Artist Name",
    source="original_artwork",
    license="CC-BY-4.0",
)
```

### AssetReference

Lightweight reference to asset location.

```python
from core.asset import AssetReference

ref = AssetReference(
    path="assets/sprites/hero.png",
    uri="file:///assets/sprites/hero.png",
    mime_type="image/png",
    extension="png",
    checksum="abc123def456",
    size_bytes=102400,
)
```

**Important:** This is metadata only. The file is NOT loaded or verified.

### AssetProperties

Type-specific asset properties.

```python
from core.asset import AssetProperties

# Image properties
props = AssetProperties(
    width=1920,
    height=1080,
    format="PNG",
)

# Audio properties
props = AssetProperties(
    duration=180.0,
    sample_rate=44100,
    channels=2,
)

# Video properties
props = AssetProperties(
    width=1920,
    height=1080,
    duration=120.0,
    frame_count=2880,
)
```

### AssetState

Basic asset state.

```python
from core.asset import AssetState

state = AssetState(
    enabled=True,
    available=True,
    verified=False,
)
```

## Asset Collection

Registry for managing multiple assets.

```python
from core.asset import AssetCollection, AssetType

collection = AssetCollection()

# Add asset
asset = Asset(name="hero_sprite", asset_type=AssetType.SPRITE)
collection.add(asset)

# Get asset
retrieved = collection.get(asset.id)

# List all (sorted by name)
all_assets = collection.list()

# Filter by type
images = collection.list_by_type(AssetType.IMAGE)

# Filter by tag
tagged = collection.list_by_tag("character")

# Find by name
found = collection.find_by_name("hero_sprite")

# Get available
available = collection.get_available()

# Check existence
if collection.has(asset.id):
    print("Found!")

# Remove
collection.remove(asset.id)
```

## Serialization

Assets serialize to JSON with full data preservation.

```python
from core.asset import AssetSerializer

# Serialize to dict
data = AssetSerializer.serialize(asset)

# Deserialize from dict
asset = AssetSerializer.deserialize(data)

# Serialize to JSON
json_str = AssetSerializer.to_json(asset)

# Deserialize from JSON
asset = AssetSerializer.from_json(json_str)
```

### JSON Format

```json
{
  "id": "uuid-string",
  "name": "hero_sprite",
  "asset_type": "sprite",
  "metadata": {
    "name": "hero_sprite",
    "display_name": "Hero Sprite",
    "description": "Main character sprite",
    "tags": ["character", "hero"],
    "author": "Artist",
    "source": "",
    "license": "",
    "notes": "",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
    "custom_metadata": {}
  },
  "reference": {
    "path": "assets/sprites/hero.png",
    "uri": "",
    "mime_type": "image/png",
    "extension": "png",
    "checksum": "",
    "size_bytes": 0
  },
  "properties": {
    "width": 1920,
    "height": 1080,
    "duration": null,
    "frame_count": null,
    "sample_rate": null,
    "channels": null,
    "bit_rate": null,
    "format": "PNG",
    "codec": "",
    "color_space": "",
    "custom_attributes": {}
  },
  "state": {
    "enabled": true,
    "available": true,
    "verified": false,
    "custom_state": {}
  }
}
```

## Validation

```python
errors = asset.validate()
if errors:
    print("Validation failed:", errors)

asset.validate_or_raise()  # Raises AssetValidationError
```

Validation checks:
- Valid ID
- Valid name length
- Valid metadata fields
- Valid reference fields
- Valid properties
- Valid state

## AssetValidator

Standalone validator class for asset data.

```python
from core.asset import AssetValidator

# Validate path
errors = AssetValidator.validate_path("/path/to/file.png")

# Validate URI
errors = AssetValidator.validate_uri("https://example.com/file.png")

# Validate dimensions
errors = AssetValidator.validate_dimensions(1920, 1080)

# Validate duration
errors = AssetValidator.validate_duration(120.0)
```

## Exceptions

| Exception | Description |
|-----------|-------------|
| `AssetError` | Base exception |
| `AssetValidationError` | Validation failed |
| `AssetNotFoundError` | Asset not found |
| `AssetDuplicateIDError` | Duplicate ID detected |
| `AssetSerializationError` | Serialization failed |
| `AssetReferenceError` | Invalid reference |
| `AssetTypeError` | Invalid asset type |

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Asset` | Main asset model |
| `AssetMetadata` | Asset metadata |
| `AssetReference` | Asset location reference |
| `AssetProperties` | Type-specific properties |
| `AssetState` | Basic state |
| `AssetType` | Asset type enum |
| `AssetValidator` | Standalone validator |
| `AssetCollection` | Asset registry |
| `AssetSerializer` | JSON serialization |

## Dependency Boundaries

`core/asset` has NO dependencies on:
- `core/project`
- `core/scene`
- `core/timeline`
- `core/character`
- `core/camera`

Cross-module references use IDs only.

## Dependencies

- `pydantic>=2.0.0`: Data validation

## No Dependencies On

This module does NOT depend on:
- Image processing libraries
- Video codecs
- Audio libraries
- Network libraries
- Filesystem APIs
- GPU/graphics APIs
- AI/ML frameworks

## Known Limitations

1. **No asset loading**: Reference is metadata only
2. **No file verification**: File existence not checked
3. **No processing**: No image/video/audio processing
4. **No storage management**: Does not manage asset storage
5. **No caching**: No asset caching
6. **No dependency tracking**: No asset dependency graph
7. **No thumbnails**: No thumbnail generation

## Future Extension Points

1. **Asset groups**: Grouping related assets
2. **Asset variants**: Different versions/formats
3. **Asset dependencies**: Asset relationships
4. **Asset tags**: Extended tagging system
5. **Asset versioning**: Version history
6. **Asset caching**: Cache metadata
7. **Asset preprocessing**: Basic metadata extraction
