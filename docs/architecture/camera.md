# Core Camera Module

## Purpose

The `core/camera` module defines the **camera data model** for Manga2Anime. It represents camera state, projection, viewport, and framing configuration.

**This module does NOT handle:**
- Rendering
- GPU interaction
- Shaders
- Image generation
- Camera animation
- Cinematic editing

## Overview

```
core/camera/
├── __init__.py        # Public API exports
├── camera.py          # Camera model and configuration
├── collection.py      # Camera collection/registry
├── serialization.py   # JSON serialization/deserialization
└── exceptions.py      # Camera-specific exceptions
```

## Core Concepts

### Camera

The main camera model representing configuration and state.

```python
from core.camera import Camera

cam = Camera(name="Main Camera")
```

**Attributes:**
- `id`: Unique camera identifier (UUID)
- `name`: Camera name
- `metadata`: CameraMetadata
- `transform`: CameraTransform (position, rotation)
- `projection`: Projection (orthographic or perspective)
- `viewport`: Viewport (width, height)
- `framing`: Framing (center, size, zoom, margins)
- `state`: CameraState (enabled, active)
- `references`: CameraReferences (scene_id, target_id)

### CameraTransform

Camera position and rotation in 3D space.

```python
from core.camera import CameraTransform

transform = CameraTransform(
    position_x=0.0,
    position_y=0.0,
    position_z=10.0,
    rotation_x=0.0,
    rotation_y=0.0,
    rotation_z=0.0,
)
```

**2D/3D Support:**
- `is_2d()`: Check if transform is effectively 2D

### Projection

Camera projection configuration supporting both 2D and 3D workflows.

```python
from core.camera import Projection, ProjectionType, PerspectiveProjection, OrthographicProjection
```

#### Perspective

```python
projection = Projection(
    type=ProjectionType.PERSPECTIVE,
    perspective=PerspectiveProjection(
        field_of_view=60.0,
        near_clip=0.1,
        far_clip=1000.0,
    ),
)
```

#### Orthographic

```python
projection = Projection(
    type=ProjectionType.ORTHOGRAPHIC,
    orthographic=OrthographicProjection(size=5.0),
)
```

**Validation:**
- FOV must be between 0 and 180 degrees
- Near clip must be positive
- Far clip must be greater than near clip
- Orthographic size must be positive

### Viewport

Viewport dimensions for camera output.

```python
from core.camera import Viewport

viewport = Viewport(width=1920, height=1080)
print(viewport.aspect_ratio)  # 1.777...
```

**Validation:**
- Width must be positive
- Height must be positive

### Framing

Generic framing configuration for content composition.

```python
from core.camera import Framing

framing = Framing(
    center_x=0.0,
    center_y=0.0,
    size_width=1.0,
    size_height=1.0,
    zoom=1.0,
    margin_left=0.0,
    margin_right=0.0,
    margin_top=0.0,
    margin_bottom=0.0,
)
```

### CameraState

Basic camera state.

```python
from core.camera import CameraState

state = CameraState(
    enabled=True,
    active=False,
)
```

### CameraReferences

Lightweight references to external resources.

```python
from core.camera import CameraReferences

refs = CameraReferences(
    scene_id="scene-001",
    target_id="target-001",
)
```

**Note:** These are identifiers only. No scene manipulation occurs.

## 2D / 3D Design

The camera module supports both workflows:

**2D Animation:**
- Orthographic projection
- Z position = 0
- No rotation around X/Y axes

**3D Animation:**
- Perspective projection
- Full 3D transform
- Configurable clipping planes

## Camera Collection

Registry for managing multiple cameras.

```python
from core.camera import CameraCollection

collection = CameraCollection()

# Add camera
cam = Camera(name="Main Camera")
collection.add(cam)

# Get camera
retrieved = collection.get(cam.id)

# List all (sorted by name)
all_cameras = collection.list()

# Get active cameras
active = collection.get_active()

# Check existence
if collection.has(cam.id):
    print("Found!")

# Remove
collection.remove(cam.id)
```

## Serialization

Cameras serialize to JSON with full data preservation.

```python
from core.camera import CameraSerializer

# Serialize to dict
data = CameraSerializer.serialize(camera)

# Deserialize from dict
cam = CameraSerializer.deserialize(data)

# Serialize to JSON
json_str = CameraSerializer.to_json(camera)

# Deserialize from JSON
cam = CameraSerializer.from_json(json_str)
```

### JSON Format

```json
{
  "id": "uuid-string",
  "name": "Main Camera",
  "metadata": {
    "description": "",
    "tags": [],
    "notes": "",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
    "custom_metadata": {}
  },
  "transform": {
    "position_x": 0.0,
    "position_y": 0.0,
    "position_z": 10.0,
    "rotation_x": 0.0,
    "rotation_y": 0.0,
    "rotation_z": 0.0
  },
  "projection": {
    "type": "perspective",
    "orthographic": {
      "size": 5.0
    },
    "perspective": {
      "field_of_view": 60.0,
      "near_clip": 0.1,
      "far_clip": 1000.0
    }
  },
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "framing": {
    "center_x": 0.0,
    "center_y": 0.0,
    "size_width": 1.0,
    "size_height": 1.0,
    "zoom": 1.0,
    "margin_left": 0.0,
    "margin_right": 0.0,
    "margin_top": 0.0,
    "margin_bottom": 0.0
  },
  "state": {
    "enabled": true,
    "active": false,
    "custom_state": {}
  },
  "references": {
    "scene_id": "",
    "target_id": "",
    "custom_references": {}
  }
}
```

## Validation

```python
errors = camera.validate()
if errors:
    print("Validation failed:", errors)

camera.validate_or_raise()  # Raises CameraValidationError
```

Validation checks:
- Valid ID
- Name length limits
- Transform validity
- Projection parameters (FOV, clips, size)
- Viewport dimensions
- Framing parameters
- Reference validity

## Exceptions

| Exception | Description |
|-----------|-------------|
| `CameraError` | Base exception |
| `CameraValidationError` | Validation failed |
| `CameraNotFoundError` | Camera not found |
| `CameraDuplicateIDError` | Duplicate ID detected |
| `CameraProjectionError` | Invalid projection |
| `CameraSerializationError` | Serialization failed |
| `CameraReferenceError` | Invalid reference |

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Camera` | Main camera model |
| `CameraMetadata` | Camera metadata |
| `CameraState` | Camera state |
| `CameraTransform` | Position/rotation |
| `CameraReferences` | External references |
| `Projection` | Projection config |
| `ProjectionType` | Projection enum |
| `OrthographicProjection` | Orthographic settings |
| `PerspectiveProjection` | Perspective settings |
| `Viewport` | Viewport dimensions |
| `Framing` | Framing configuration |
| `CameraCollection` | Camera registry |
| `CameraSerializer` | JSON serialization |

## Integration Points

### With core/scene

Cameras reference scenes by ID. No direct scene manipulation:
- `scene_id`: Reference to a Scene

### With core/timeline

Camera data may be animated by Timeline in future systems:
- Camera transform can be animated via tracks
- Camera properties can be animated via keyframes

**Note:** This module does not create Timeline tracks.

### With Rendering (Future)

Future rendering systems will:
- Read camera configuration
- Apply projection matrices
- Render to viewport

## Dependencies

- `pydantic>=2.0.0`: Data validation

## No Dependencies On

This module does NOT depend on:
- `core/scene` (reference by ID only)
- `core/timeline` (reference by ID only)
- `core/character`
- `core/asset`
- `tools/*`
- `agents/*`
- `runtime/*`
- `apps/*`
- GPU/renderer

## Known Limitations

1. **No rendering**: Does not produce images
2. **No GPU interaction**: Pure data model
3. **No animation**: No keyframe or timeline data
4. **No tracking**: No automatic target following
5. **No post-processing**: No effects or filters
6. **No stereoscopic**: No 3D stereo support

## Future Extension Points

1. **Camera shake**: Shake/effect parameters
2. **Depth of field**: DOF configuration
3. **Motion blur**: MB configuration
4. **Post-processing**: Effect chain
5. **Stereo 3D**: VR/stereo camera
6. **Multi-view**: Multiple viewports
7. **Camera switcher**: Transition logic
