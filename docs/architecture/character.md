# Core Character Module

## Purpose

The `core/character` module defines the **data model** for characters in Manga2Anime. It represents what a character is - their identity, appearance, properties, state, and references to other systems.

This module does NOT handle:
- Character rendering
- Character animation
- AI character generation
- Character rigging
- Voice synthesis
- Asset loading/processing

## Overview

```
core/character/
├── __init__.py        # Public API exports
├── character.py       # Character model and management
├── appearance.py      # Character appearance
├── collection.py     # Character collection/registry
├── serialization.py  # JSON serialization/deserialization
└── exceptions.py      # Character-specific exceptions
```

## Core Concepts

### Character

The main character model representing identity and properties.

```python
from core.character import Character

char = Character(
    name="hero",
    display_name="The Hero",
)
```

**Attributes:**
- `id`: Unique character identifier (UUID)
- `name`: Internal character name
- `display_name`: Human-readable display name
- `metadata`: CharacterMetadata (description, tags, notes)
- `appearance`: CharacterAppearance (visual description)
- `properties`: CharacterProperties (height, age, role, etc.)
- `state`: CharacterState (active, visible, enabled)
- `references`: CharacterReferences (scene, object, assets, tracks)

### CharacterMetadata

Structured metadata for characters.

```python
from core.character import CharacterMetadata

metadata = CharacterMetadata(
    description="A brave warrior",
    tags=["hero", "protagonist"],
    notes="Important character in story",
)
```

### CharacterAppearance

Visual appearance description with lightweight asset references.

```python
from core.character import CharacterAppearance

appearance = CharacterAppearance(
    description="Tall with spiky blue hair",
    style="anime",
    hair_color="blue",
    eye_color="green",
)
```

**Asset References:**
Asset references are identifiers only - no asset loading:
```python
appearance.set_asset_reference("design", "asset-id-001")
appearance.set_asset_reference("portrait", "portrait-id-001")
```

### CharacterProperties

Extensible properties for character data.

```python
from core.character import CharacterProperties

props = CharacterProperties(
    height="tall",
    age="young adult",
    role="warrior",
    faction="knights",
)

# Custom properties
char.set_custom_property("weapon", "sword")
```

### CharacterState

Basic character state representation.

```python
from core.character import CharacterState

state = CharacterState(
    active=True,
    visible=True,
    enabled=True,
)
```

### CharacterReferences

Lightweight references to external resources.

```python
from core.character import CharacterReferences

refs = CharacterReferences(
    design_asset_id="design-001",
    portrait_asset_id="portrait-001",
    scene_id="scene-001",
    object_id="object-001",
)
```

**Important:** These are identifiers only. No asset loading is performed.

### Scene Relationship

Characters can reference a Scene by ID:

```python
char.set_scene_reference("scene-001")
scene_id = char.get_scene_reference()  # "scene-001"
```

**Note:** This does NOT modify `core/scene`. The reference is purely data-level.

### Timeline Relationship

Characters can reference Timeline tracks by ID:

```python
char.add_track_reference("track-001")
tracks = char.get_track_references()  # ["track-001"]
```

**Note:** This does NOT create tracks in `core/timeline`. Tracks must be created separately.

## Character Collection

A registry for managing multiple characters.

```python
from core.character import CharacterCollection

collection = CharacterCollection()

# Add characters
hero = Character(name="Hero")
collection.add(hero)

# Get character
retrieved = collection.get(hero.id)

# List all (sorted by name)
all_chars = collection.list()

# Find by tag
protagonists = collection.list_by_tag("protagonist")

# Check existence
if collection.has(hero.id):
    print("Found!")

# Remove
collection.remove(hero.id)
```

## Serialization

Characters serialize to JSON with full data preservation.

```python
from core.character import CharacterSerializer

# Serialize to dict
data = CharacterSerializer.serialize(character)

# Deserialize from dict
char = CharacterSerializer.deserialize(data)

# Serialize to JSON
json_str = CharacterSerializer.to_json(character)

# Deserialize from JSON
char = CharacterSerializer.from_json(json_str)
```

### JSON Format

```json
{
  "id": "uuid-string",
  "name": "hero",
  "display_name": "The Hero",
  "metadata": {
    "description": "A brave hero",
    "tags": ["hero", "protagonist"],
    "notes": "Important character",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
    "custom_metadata": {}
  },
  "appearance": {
    "description": "Tall with blue hair",
    "style": "anime",
    "hair_color": "blue",
    "eye_color": "green",
    "skin_tone": "",
    "height_description": "",
    "build_description": "",
    "age_description": "",
    "asset_references": {},
    "custom_attributes": {}
  },
  "properties": {
    "height": "tall",
    "age": "young adult",
    "role": "warrior",
    "faction": "knights",
    "custom_attributes": {}
  },
  "state": {
    "active": true,
    "visible": true,
    "enabled": true,
    "custom_state": {}
  },
  "references": {
    "design_asset_id": "",
    "portrait_asset_id": "",
    "model_asset_id": "",
    "voice_asset_id": "",
    "scene_id": "",
    "object_id": "",
    "track_ids": [],
    "custom_references": {}
  }
}
```

## Validation

```python
errors = character.validate()
if errors:
    print("Validation failed:", errors)

character.validate_or_raise()  # Raises CharacterValidationError
```

Validation checks:
- Valid ID
- Name/display name length limits
- Metadata constraints
- Reference validity

## Exceptions

| Exception | Description |
|-----------|-------------|
| `CharacterError` | Base exception |
| `CharacterValidationError` | Validation failed |
| `CharacterNotFoundError` | Character not found |
| `CharacterDuplicateIDError` | Duplicate ID detected |
| `CharacterSerializationError` | Serialization failed |
| `CharacterReferenceError` | Invalid reference |

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Character` | Main character model |
| `CharacterMetadata` | Character metadata |
| `CharacterAppearance` | Visual appearance |
| `CharacterProperties` | Extensible properties |
| `CharacterState` | Basic state |
| `CharacterReferences` | External references |
| `CharacterCollection` | Character registry |
| `CharacterSerializer` | JSON serialization |

## Integration Points

### With core/scene

Characters reference scenes by ID. No direct scene manipulation:
- `scene_id`: Reference to a Scene
- `object_id`: Reference to a SceneObject

### With core/timeline

Characters reference tracks by ID. No track creation:
- `track_ids`: List of animation track IDs

### Future Systems

Future modules may extend:
- **Rendering**: Apply appearance to render pipeline
- **Animation**: Connect tracks to character rig
- **AI**: Add behavior/expression data
- **Voice**: Connect voice assets

## Dependencies

- `pydantic>=2.0.0`: Data validation (shared with core modules)

## No Dependencies On

This module does NOT depend on:
- `core/scene` (reference by ID only)
- `core/timeline` (reference by ID only)
- `core/camera`
- `core/asset`
- `tools/*`
- `agents/*`
- `runtime/*`
- `apps/*`

## Known Limitations

1. **No asset loading**: Asset references are identifiers only
2. **No animation data**: No keyframe or animation track data
3. **No rigging data**: No bone or skeleton structure
4. **No behavior**: No AI or state machine
5. **No expressions**: No expression data

## Future Extension Points

1. **Character rigging**: Bone/skeleton data
2. **Expression system**: Facial expressions
3. **Costume system**: Outfit variations
4. **Character variants**: Different versions
5. **Relationship system**: Character relationships
