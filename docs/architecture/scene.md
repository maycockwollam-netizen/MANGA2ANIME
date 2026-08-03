# Core Scene Module

## Purpose

The `core/scene` module provides the foundation for representing animation scenes in Manga2Anime. It handles scene structure, objects, transforms, and hierarchy relationships.

## Overview

```
core/scene/
├── __init__.py        # Public API exports
├── scene.py           # Scene model and management
├── object.py          # SceneObject model
├── transform.py       # Transform, Vector, Rotation
├── serialization.py   # JSON serialization/deserialization
└── exceptions.py      # Scene-specific exceptions
```

## Core Concepts

### Scene

The main container for a collection of scene objects.

```python
from core.scene import Scene, SceneMetadata

scene = Scene(metadata=SceneMetadata(name="Opening Scene"))
```

**Attributes:**
- `id`: Unique scene identifier (UUID)
- `metadata`: SceneMetadata (name, description, timestamps)
- `settings`: SceneSettings (background color, ambient light)
- `objects`: Dictionary of scene objects by ID

### SceneObject

Generic representation for any object in a scene (backgrounds, character parts, effects, etc.).

```python
from core.scene import SceneObject

obj = SceneObject(
    name="Character",
    object_type="character",
    visible=True,
    enabled=True,
)
```

**Attributes:**
- `id`: Unique object identifier (UUID)
- `name`: Human-readable name
- `object_type`: Category (generic, character, background, effect, etc.)
- `transform`: Transform (position, rotation, scale)
- `parent_id`: Parent object ID (None for root objects)
- `visible`: Whether object is visible
- `enabled`: Whether object is active
- `metadata`: ObjectMetadata (timestamps)
- `custom_data`: Dict for extensible data

### Transform

Represents position, rotation, and scale of an object.

```python
from core.scene import Transform, Vector3, EulerRotation

transform = Transform(
    position=Vector3(x=100.0, y=200.0, z=0.0),
    rotation=EulerRotation(x=0.0, y=0.0, z=45.0),
    scale=Vector3(x=1.0, y=1.0, z=1.0),
)
```

**Components:**
- `position`: Vector3 for location
- `rotation`: EulerRotation for orientation
- `scale`: Vector3 for size (1.0 = original)

**2D/3D Support:**
- `is_2d()`: Check if transform is effectively 2D (z=0)

## Hierarchy

Scene objects form a parent-child hierarchy.

### Rules

1. An object can have zero or one parent
2. An object can have multiple children
3. Self-parenting is forbidden
4. Circular hierarchies are forbidden
5. Removing an object can orphan or cascade-delete its children

### Example Hierarchy

```
Scene
│
├── Background
│   └── Sky
│
└── Character
    ├── Body
    │   ├── Head
    │   └── Torso
    ├── Weapon
    └── Effect
```

### Hierarchy Operations

```python
# Set parent
scene.set_parent(child_id, parent_id)

# Remove parent
scene.set_parent(child_id, None)

# Get children
children = scene.get_children(parent_id)

# Get root objects (no parent)
roots = scene.get_root_objects()

# Get full tree
tree = scene.get_hierarchy_tree()
```

## Object Management

### Adding Objects

```python
obj = SceneObject(name="New Object")
scene.add_object(obj)
```

### Removing Objects

```python
# Remove without children
scene.remove_object(object_id, cascade=False)

# Remove with children
scene.remove_object(object_id, cascade=True)
```

### Updating Objects

```python
scene.update_object(object_id, name="Updated Name", visible=False)
```

### Transform Updates

```python
obj = scene.get_object(object_id)
obj.update_transform(
    position=(100.0, 200.0, 0.0),
    rotation=(0.0, 0.0, 45.0),
    scale=(2.0, 2.0, 2.0),
)
```

## Serialization

Scenes serialize to JSON with full hierarchy preservation.

### JSON Format

```json
{
  "id": "uuid-string",
  "metadata": {
    "name": "Scene Name",
    "description": "...",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00"
  },
  "settings": {
    "background_color": "#000000",
    "ambient_light": 0.5
  },
  "objects": {
    "object-uuid": {
      "id": "object-uuid",
      "name": "Object Name",
      "object_type": "character",
      "transform": {
        "position": {"x": 0, "y": 0, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1}
      },
      "parent_id": null,
      "visible": true,
      "enabled": true,
      "metadata": {...},
      "custom_data": {}
    }
  }
}
```

### Serialization Operations

```python
from core.scene import SceneSerializer

# Serialize to dict
data = SceneSerializer.serialize(scene)

# Deserialize from dict
scene = SceneSerializer.deserialize(data)

# Serialize to JSON
json_str = SceneSerializer.to_json(scene)

# Deserialize from JSON
scene = SceneSerializer.from_json(json_str)
```

## Validation

The validator checks:

- **Scene ID**: Required
- **Scene name**: Max 255 characters
- **Hierarchy**: No cycles, no self-parenting, no dangling references
- **Object names**: Non-empty

```python
errors = scene.validate()
if errors:
    print("Validation failed:", errors)

scene.validate_or_raise()  # Raises SceneValidationError
```

## Exceptions

| Exception | Description |
|-----------|-------------|
| `SceneError` | Base exception |
| `SceneValidationError` | Validation failed |
| `SceneObjectError` | Object operation failed |
| `SceneHierarchyError` | Hierarchy operation failed |
| `SceneSerializationError` | Serialization failed |
| `SceneNotFoundError` | Object not found |
| `SceneDuplicateIDError` | Duplicate object ID |

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Scene` | Main scene container |
| `SceneMetadata` | Scene metadata |
| `SceneSettings` | Scene settings |
| `SceneObject` | Generic scene object |
| `ObjectMetadata` | Object metadata |
| `Transform` | Position/rotation/scale |
| `Vector2` | 2D vector |
| `Vector3` | 3D vector |
| `EulerRotation` | Euler rotation |
| `SceneSerializer` | JSON serialization |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `SceneError` | Base exception |
| `SceneValidationError` | Validation failed |
| `SceneObjectError` | Object operation failed |
| `SceneHierarchyError` | Hierarchy operation failed |
| `SceneSerializationError` | Serialization failed |
| `SceneNotFoundError` | Object not found |
| `SceneDuplicateIDError` | Duplicate ID |

## Integration Points

### With core/project

`core/scene` does not directly depend on `core/project`. Scene can be:
- Referenced by Project state
- Managed independently
- Serialized/deserialized separately

### Future Integrations

Future modules may extend:

- **Character objects**: Extend `SceneObject` for character-specific data
- **Camera objects**: Extend `SceneObject` for camera-specific properties
- **Timeline integration**: Scenes linked to timeline tracks
- **Asset integration**: SceneObjects reference assets

## Known Limitations

1. **No specialized object types**: Only generic `SceneObject`
2. **No animation data**: Transform is static, no keyframes
3. **No collision/physics**: No physics simulation
4. **No material/shader system**: Basic visibility only
5. **No scene graph optimization**: No spatial indexing

## Future Extension Points

1. **Specialized objects**: Character, Camera, Light, ParticleSystem
2. **Animation**: Keyframe, AnimationClip, AnimationTrack
3. **Materials**: Material, Shader, Texture references
4. **Physics**: Collider, RigidBody, Joint
5. **Optimization**: Spatial partitioning, LOD support

## Dependencies

- `pydantic>=2.0.0`: Data validation (shared with core/project)

## No Dependencies On

This module does not depend on:
- `core/project`
- `core/timeline`
- `core/character`
- `core/camera`
- `core/asset`
- `tools/*`
- `agents/*`
- `runtime/*`
- `apps/*`
