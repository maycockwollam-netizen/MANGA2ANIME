# Core Project Module

## Purpose

The `core/project` module is the foundation for representing, creating, saving, loading, validating, and versioning a Manga2Anime project. It provides the core data models and persistence layer that all other modules depend on.

## Overview

```
core/project/
├── __init__.py       # Public API exports
├── model.py          # Project, ProjectMetadata, ProjectSettings, ProjectState
├── repository.py     # File-based persistence
├── serialization.py  # JSON serialization/deserialization
├── validator.py      # Project validation
└── exceptions.py     # Custom exceptions
```

## Project Model

### Project

The main container for a Manga2Anime project.

```python
from core.project import Project

project = Project(
    metadata=ProjectMetadata(name="My Anime"),
    settings=ProjectSettings(resolution_width=1920)
)
```

**Attributes:**
- `id`: Unique project identifier (UUID)
- `version`: Project version string (e.g., "0.1.0")
- `metadata`: ProjectMetadata instance
- `settings`: ProjectSettings instance
- `state`: ProjectState instance

### ProjectMetadata

Contains descriptive information about the project.

**Attributes:**
- `name`: Project name (max 255 characters)
- `description`: Project description (max 2000 characters)
- `author`: Author name (max 255 characters)
- `tags`: List of tags
- `created_at`: Creation timestamp (UTC)
- `updated_at`: Last modified timestamp (UTC)

### ProjectSettings

Contains technical settings for rendering.

**Attributes:**
- `resolution_width`: Video width in pixels (640-3840, even numbers only)
- `resolution_height`: Video height in pixels (360-2160, even numbers only)
- `frame_rate`: Frames per second (12-120)
- `audio_sample_rate`: Audio sample rate in Hz (16000-96000)
- `default_duration_seconds`: Default scene duration (0.1-60 seconds)

### ProjectState

Tracks the current state of the project.

**Attributes:**
- `status`: Project status string (default: "created")
- `scenes`: List of scene IDs
- `assets`: List of asset IDs

## Serialization Format

Projects are serialized to JSON with the following structure:

```json
{
  "id": "uuid-string",
  "version": "0.1.0",
  "metadata": {
    "name": "Project Name",
    "description": "...",
    "author": "Author Name",
    "tags": ["tag1", "tag2"],
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00"
  },
  "settings": {
    "resolution_width": 1280,
    "resolution_height": 720,
    "frame_rate": 24,
    "audio_sample_rate": 48000,
    "default_duration_seconds": 3.0
  },
  "state": {
    "status": "created",
    "scenes": [],
    "assets": []
  }
}
```

## Save/Load Behavior

### Saving a Project

```python
from core.project import Project, ProjectRepository
from pathlib import Path

repo = ProjectRepository()
project = Project(metadata=ProjectMetadata(name="My Project"))

# Save to directory (creates project.json inside)
path = repo.save(project, Path("./projects/my_anime"))
# Returns: /path/to/projects/my_anime/project.json
```

The save operation:
1. Creates the target directory if it doesn't exist
2. Serializes the project to JSON
3. Writes to `project.json` file
4. Returns the path to the saved file

### Loading a Project

```python
repo = ProjectRepository()
project = repo.load(Path("./projects/my_anime"))
```

The load operation:
1. Checks if `project.json` exists
2. Reads and parses the JSON file
3. Validates the project structure
4. Returns a Project instance

## Validation Behavior

The validator checks:

- **ID**: Required, max 255 characters
- **Version**: Must be in supported versions list
- **Metadata**: Name max 255 chars, description max 2000 chars, author max 255 chars
- **Settings**: Resolution (640-3840 width, 360-2160 height), frame rate (12-120), audio sample rate (16000-96000), duration (0.1-60 seconds)
- **State**: Scene and asset IDs must be non-empty and max 255 characters

### Validation Example

```python
from core.project import Project, ProjectValidator, ProjectValidationError

project = Project()
validator = ProjectValidator()

errors = validator.validate(project)
if errors:
    print("Validation errors:", errors)

# Or raise on invalid:
validator.validate_or_raise(project)  # Raises ProjectValidationError
```

## Versioning

### Supported Versions

- `0.1.0` (current)

### Version Constraints

- Version must be explicitly set and validated
- Version is preserved through serialization
- Invalid versions raise `ValueError` on project creation

### Future Extension Points

A migration framework may be added in the future to handle:
- Automatic version upgrades
- Data transformation between versions
- Compatibility checks

**Current limitation**: No automatic migration is implemented. Projects with unsupported versions will fail to load.

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Project` | Main project container |
| `ProjectMetadata` | Project descriptive information |
| `ProjectSettings` | Technical rendering settings |
| `ProjectState` | Project state tracking |
| `ProjectRepository` | File-based persistence |
| `ProjectValidator` | Project validation |
| `ProjectSerializer` | JSON serialization |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `ProjectError` | Base exception |
| `ProjectValidationError` | Validation failed |
| `ProjectLoadError` | Loading failed |
| `ProjectSaveError` | Saving failed |
| `ProjectFormatError` | Invalid format |
| `ProjectVersionError` | Version incompatibility |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `CURRENT_VERSION` | `"0.1.0"` | Current project version |
| `SUPPORTED_VERSIONS` | `["0.1.0"]` | List of supported versions |

## Usage Examples

### Creating a New Project

```python
from core.project import Project, ProjectMetadata, ProjectSettings

project = Project(
    metadata=ProjectMetadata(
        name="My Anime Project",
        description="A test project",
        author="Creator",
        tags=["demo", "test"]
    ),
    settings=ProjectSettings(
        resolution_width=1920,
        resolution_height=1080,
        frame_rate=24
    )
)
```

### Managing Scenes and Assets

```python
project.add_scene("scene-001")
project.add_asset("character_sprite")
project.remove_scene("scene-001")
```

### Save and Load

```python
from core.project import ProjectRepository

repo = ProjectRepository()
repo.save(project, Path("./projects/my_anime"))
loaded = repo.load(Path("./projects/my_anime"))
```

### Validation

```python
from core.project import ProjectValidator

validator = ProjectValidator()
errors = validator.validate(project)
```

## Known Limitations

1. **No automatic migration**: Projects with unsupported versions cannot be loaded
2. **No project locking**: No mechanism to prevent concurrent edits
3. **No backup**: Save operation overwrites without creating backups
4. **Single file format**: All project data stored in one JSON file

## Future Extension Points

1. **Migration Framework**: Add automatic version upgrades
2. **Backup System**: Automatic backup before save
3. **Locking**: Project file locking for multi-user scenarios
4. **Incremental Save**: Save only changed portions
5. **Cloud Sync**: Remote project storage support
6. **Encryption**: Encrypted project files for sensitive content

## Dependencies

- `pydantic>=2.0.0`: Data validation and settings

## No Dependencies On

This module does not depend on:
- `core/scene`
- `core/timeline`
- `core/character`
- `core/camera`
- `core/asset`
- `tools/*`
- `agents/*`
- `runtime/*`
- `apps/*`
- `interfaces/*`
