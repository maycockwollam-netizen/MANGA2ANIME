# Integration Layer

## Purpose

The Integration Layer provides orchestration above Core modules while maintaining Core isolation.

It allows Core modules to be used together without:
- Introducing circular dependencies
- Coupling Core modules to each other
- Breaking Core's clean architecture

## Architecture Direction

```
core/*           (pure data/model layer)
     ↓
integration/*   (orchestration layer)
```

**Critical rule:** Core MUST NOT import the Integration Layer.

## Overview

```
integration/
├── __init__.py       # Public API exports
├── context.py        # ProjectContext
├── registry.py       # Generic Registry
├── resolver.py       # ReferenceResolver
├── validator.py      # IntegrationValidator
└── exceptions.py     # Integration exceptions
```

## Dependency Direction

```
                 ┌─ core/project
                 ├─ core/scene
                 ├─ core/timeline
Integration ─────┼─ core/character
                 ├─ core/camera
                 └─ core/asset
```

The Integration Layer imports Core modules. Core modules do NOT import Integration.

## Why Core Remains Isolated

Core modules are intentionally isolated because:

1. **Independence**: Each module can be used standalone
2. **Testing**: Easy to test without dependencies
3. **Flexibility**: Different projects may use different Core combinations
4. **Evolution**: Modules can evolve independently
5. **Serialization**: Each module owns its serialization format

The Integration Layer bridges modules when they need to work together.

## ProjectContext

Central container for Core entities.

```python
from integration import ProjectContext

context = ProjectContext()

# Set project
context.set_project(project)

# Register entities
context.register_scene(scene)
context.register_character(character)
context.register_camera(camera)
context.register_timeline(timeline)
context.register_asset(asset)

# Retrieve entities
scene = context.get_scene("scene-1")
character = context.get_character("char-1")
```

### Entity Management

| Operation | Method |
|-----------|--------|
| Register | `context.register_scene(scene)` |
| Unregister | `context.unregister_scene(scene_id)` |
| Get | `context.get_scene(scene_id)` |
| Check | `context.has_scene(scene_id)` |
| List | `context.list_scenes()` |
| Count | `context.scene_count()` |

### Bulk Operations

```python
# List all entities
context.list_scenes()
context.list_characters()
context.list_cameras()
context.list_timelines()
context.list_assets()

# Total count
context.total_count()

# Clear all
context.clear()
```

## Registry

Generic registry for Core entities.

```python
from integration import Registry

registry = Registry()

# Register entity (must have 'id' attribute)
registry.register(entity)

# Operations
registry.get(entity_id)
registry.exists(entity_id)
registry.list()
registry.count()
registry.unregister(entity_id)
registry.clear()
```

### Registry vs ProjectContext

- **Registry**: Generic, reusable for any entity type
- **ProjectContext**: Pre-configured for all 6 Core entity types

Use ProjectContext for full projects, Registry for specific collections.

## ReferenceResolver

Resolves cross-module ID references.

```python
from integration import ReferenceResolver

resolver = ReferenceResolver(context)

# Resolve individual references
scene = resolver.resolve_scene_reference("scene-1")
character = resolver.resolve_character_reference("char-1")
camera = resolver.resolve_camera_reference("cam-1")
timeline = resolver.resolve_timeline_reference("timeline-1")
asset = resolver.resolve_asset_reference("asset-1")

# Resolve nested references
obj = resolver.resolve_object_reference("scene-1", "obj-1")
track = resolver.resolve_track_reference("timeline-1", "track-1")

# Resolve all references for an entity
char_refs = resolver.resolve_character_references(character)
cam_refs = resolver.resolve_camera_references(camera)
```

### Reference Resolution

| Reference Type | Method |
|---------------|--------|
| Scene | `resolve_scene_reference(scene_id)` |
| Character | `resolve_character_reference(character_id)` |
| Camera | `resolve_camera_reference(camera_id)` |
| Timeline | `resolve_timeline_reference(timeline_id)` |
| Asset | `resolve_asset_reference(asset_id)` |
| Scene Object | `resolve_object_reference(scene_id, object_id)` |
| Timeline Track | `resolve_track_reference(timeline_id, track_id)` |

### Error Handling

```python
try:
    scene = resolver.resolve_scene_reference("nonexistent")
except DanglingReferenceError as e:
    print(f"Reference {e.reference_id} not found")
except ReferenceResolutionError as e:
    print(f"Resolution failed: {e}")
```

## IntegrationValidator

Validates ProjectContext integrity.

```python
from integration import IntegrationValidator

validator = IntegrationValidator(context)

# Validate
errors = validator.validate()
if errors:
    print("Validation errors:", errors)

# Or raise on error
validator.validate_or_raise()
```

### Validation Checks

1. **Duplicate IDs**: Checks for duplicate IDs across all registries
2. **Scene References**: Verifies character scene references exist
3. **Object References**: Verifies character object references exist
4. **Camera References**: Verifies camera scene/target references exist
5. **Asset References**: Verifies character asset references exist

## Reference Lifecycle

References in Core are lightweight IDs:

```python
# In Character
scene_id: str = ""      # Reference by ID only
object_id: str = ""     # Not the actual object
track_ids: list[str] = []  # Not the actual tracks
```

The Integration Layer resolves these IDs to actual objects:

```python
# Integration resolves IDs to objects
resolver = ReferenceResolver(context)
scene = resolver.resolve_scene_reference(character.scene_id)
```

### Reference Patterns

| Entity | References |
|--------|------------|
| Character | scene_id, object_id, track_ids, asset_ids |
| Camera | scene_id, target_id |
| SceneObject | parent_id |
| Track | (contained in Timeline) |
| Project | (references all) |

## Exception Hierarchy

```
IntegrationError
├── DuplicateRegistrationError
├── EntityNotFoundError
├── ReferenceResolutionError
│   └── DanglingReferenceError
└── IntegrationValidationError
```

### Usage

```python
from integration import (
    IntegrationError,
    DuplicateRegistrationError,
    EntityNotFoundError,
    ReferenceResolutionError,
    DanglingReferenceError,
    IntegrationValidationError,
)

# Specific exceptions for specific cases
raise DuplicateRegistrationError(f"ID '{id}' already exists")
raise EntityNotFoundError(f"Entity '{id}' not found")
raise DanglingReferenceError(f"Reference '{id}' points to missing entity")
raise IntegrationValidationError("Validation failed", errors=[...])
```

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `ProjectContext` | Central container for Core entities |
| `Registry` | Generic entity registry |
| `ReferenceResolver` | Resolves ID references to objects |
| `IntegrationValidator` | Validates context integrity |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `IntegrationError` | Base exception |
| `DuplicateRegistrationError` | Duplicate ID registration |
| `EntityNotFoundError` | Entity not in context |
| `ReferenceResolutionError` | Reference resolution failed |
| `DanglingReferenceError` | Reference points to missing entity |
| `IntegrationValidationError` | Context validation failed |

## Known Limitations

1. **No persistence**: Context is in-memory only
2. **No automatic resolution**: References must be explicitly resolved
3. **No transaction support**: No atomic operations across entities
4. **No event system**: No callbacks for entity changes
5. **No lazy loading**: All entities must be in memory for resolution

## Future Extension Points

1. **Serialization**: Context serialization for persistence
2. **Event system**: Entity change callbacks
3. **Lazy loading**: On-demand entity loading
4. **Transaction support**: Atomic multi-entity operations
5. **Query system**: Filtered entity queries

## Example Usage

```python
from integration import ProjectContext, ReferenceResolver, IntegrationValidator
from core.project import Project
from core.scene import Scene
from core.character import Character

# Create context
context = ProjectContext()

# Set project
context.set_project(Project(id="proj-1", name="My Project"))

# Register entities
scene = Scene(id="scene-1", name="Main Scene")
context.register_scene(scene)

character = Character(
    id="char-1",
    name="Hero",
    scene_id="scene-1",  # Reference by ID
)
context.register_character(character)

# Validate
validator = IntegrationValidator(context)
validator.validate_or_raise()

# Resolve references
resolver = ReferenceResolver(context)
resolved_scene = resolver.resolve_character_references(character)
# Returns: {"scene": <Scene object>}

# Work with resolved objects
if "scene" in resolved_scene:
    print(f"Character is in scene: {resolved_scene['scene'].name}")
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ProjectContext                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │ Project │ │ Scenes  │ │Characters│ │ Cameras │ │Assets │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌────────────────┐
│ReferenceResolver│  │IntegrationValidator│  │    Registry    │
└───────────────┘  └───────────────┘  └────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                         Core                                │
│  project  scene  timeline  character  camera  asset       │
└─────────────────────────────────────────────────────────────┘
```
