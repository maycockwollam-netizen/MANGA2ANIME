# Core Timeline Module

## Purpose

The `core/timeline` module provides the animation timeline system for Manga2Anime. It handles time representation, keyframes, tracks, and evaluation of animated properties over time.

## Overview

```
core/timeline/
├── __init__.py        # Public API exports
├── timeline.py        # Timeline model and management
├── track.py          # Track model
├── keyframe.py       # Keyframe model
├── time.py           # Time/frame utilities
├── serialization.py  # JSON serialization/deserialization
└── exceptions.py     # Timeline-specific exceptions
```

## Core Concepts

### Timeline

The main container for animation data.

```python
from core.timeline import Timeline, TimelineSettings

timeline = Timeline(
    metadata=TimelineMetadata(name="Scene 1 Animation"),
    settings=TimelineSettings(frame_rate=24, duration=30.0),
)
```

**Attributes:**
- `id`: Unique timeline identifier (UUID)
- `metadata`: TimelineMetadata (name, description, timestamps)
- `settings`: TimelineSettings (frame_rate, duration)
- `tracks`: Dictionary of tracks by ID

**Properties:**
- `frame_rate`: Frames per second
- `duration`: Duration in seconds
- `total_frames`: Total number of frames

### Time Representation

#### Time Class

Represents a position on the timeline with both seconds and frame representations.

```python
from core.timeline import Time

t = Time(seconds=1.5, frame_rate=24)
print(t.frame)  # 36 (truncated)
```

#### Conversion Functions

```python
from core.timeline import seconds_to_frame, frame_to_seconds

frame = seconds_to_frame(1.5, 24)  # 36
seconds = frame_to_seconds(36, 24)   # 1.5
```

**Rounding Behavior:**
- `seconds_to_frame()`: Uses truncation (floor)
- `Time.frame` property: Uses truncation
- `Time.to_frame_rounded()`: Uses round-half-up

### Keyframe

Represents a single keyframe in an animation track.

```python
from core.timeline import Keyframe, InterpolationType

kf = Keyframe(
    time=1.0,
    value=100,
    interpolation=InterpolationType.LINEAR,
)
```

**Attributes:**
- `time`: Time in seconds (>= 0)
- `value`: The keyframe value (any type)
- `interpolation`: InterpolationType (STEP or LINEAR)
- `metadata`: Dictionary for extensibility

### Track

Represents an animation track for a single property.

```python
from core.timeline import Track, Keyframe

track = Track(
    name="Position X",
    target_id="character_01",
    property_name="position_x",
)
track.add_keyframe(Keyframe(time=0.0, value=0))
track.add_keyframe(Keyframe(time=1.0, value=100))
```

**Attributes:**
- `id`: Unique track identifier
- `name`: Human-readable name
- `target_id`: ID of the target object
- `property_name`: Property being animated
- `keyframes`: List of keyframes

### Interpolation Types

#### STEP

Value remains unchanged until the next keyframe.

```python
from core.timeline import InterpolationType

kf = Keyframe(time=0.0, value=0, interpolation=InterpolationType.STEP)
# t=0.0 → 0
# t=0.5 → 0 (same as first keyframe)
# t=1.0 → value of next keyframe
```

#### LINEAR

Linearly interpolates between surrounding keyframes.

```python
from core.timeline import InterpolationType

kf1 = Keyframe(time=0.0, value=0)
kf2 = Keyframe(time=10.0, value=100)
# t=0.0 → 0
# t=5.0 → 50
# t=10.0 → 100
```

## Evaluation Rules

### Timeline Evaluation

When evaluating at a specific time:

**Before first keyframe:**
- Returns the value of the first keyframe (hold)

**Exactly on keyframe:**
- Returns the keyframe's value

**Between keyframes:**
- Uses LINEAR interpolation by default
- Uses keyframe's interpolation mode for each segment

**After last keyframe:**
- Returns the value of the last keyframe (hold)

### Behavior Examples

```python
track = Track()
track.add_keyframe(Keyframe(time=0.0, value=0))
track.add_keyframe(Keyframe(time=5.0, value=100))
track.add_keyframe(Keyframe(time=10.0, value=200))

track.evaluate(0.0)    # 0   (on keyframe)
track.evaluate(2.5)    # 50  (interpolated)
track.evaluate(5.0)    # 100 (on keyframe)
track.evaluate(7.5)    # 150 (interpolated)
track.evaluate(15.0)   # 200 (after last, hold)
track.evaluate(-1.0)   # 0   (before first, hold)
```

## Duplicate Keyframe Behavior

When adding a keyframe at a time where one already exists:
- The existing keyframe is **replaced**
- The new keyframe's value and properties are used
- Only one keyframe exists at each unique time

## Serialization Format

Timelines serialize to JSON with the following structure:

```json
{
  "id": "uuid-string",
  "metadata": {
    "name": "Timeline Name",
    "description": "...",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00"
  },
  "settings": {
    "frame_rate": 24,
    "duration": 10.0
  },
  "tracks": {
    "track-uuid": {
      "id": "track-uuid",
      "name": "Position X",
      "target_id": "character_01",
      "property_name": "position_x",
      "keyframes": [
        {
          "time": 0.0,
          "value": 0,
          "interpolation": "linear",
          "metadata": {}
        },
        {
          "time": 5.0,
          "value": 100,
          "interpolation": "linear",
          "metadata": {}
        }
      ]
    }
  }
}
```

### Serialization Operations

```python
from core.timeline import TimelineSerializer

# Serialize to dict
data = TimelineSerializer.serialize(timeline)

# Deserialize from dict
timeline = TimelineSerializer.deserialize(data)

# Serialize to JSON
json_str = TimelineSerializer.to_json(timeline)

# Deserialize from JSON
timeline = TimelineSerializer.from_json(json_str)
```

## Validation

The validator checks:

- **Timeline ID**: Required
- **Timeline name**: Max 255 characters
- **Duration**: Must be >= 0
- **Frame rate**: Must be > 0
- **Track IDs**: Unique within timeline
- **Keyframe times**: Non-negative

```python
errors = timeline.validate()
if errors:
    print("Validation failed:", errors)

timeline.validate_or_raise()  # Raises TimelineValidationError
```

## Exceptions

| Exception | Description |
|-----------|-------------|
| `TimelineError` | Base exception |
| `TimelineValidationError` | Validation failed |
| `TimelineTrackError` | Track operation failed |
| `TimelineKeyframeError` | Keyframe operation failed |
| `TimelineEvaluationError` | Evaluation failed |
| `TimelineSerializationError` | Serialization failed |
| `TimelineNotFoundError` | Track/keyframe not found |
| `TimelineDuplicateIDError` | Duplicate ID detected |

## Public API

### Classes

| Class | Description |
|-------|-------------|
| `Timeline` | Main timeline container |
| `TimelineMetadata` | Timeline metadata |
| `TimelineSettings` | Timeline settings |
| `Track` | Animation track |
| `Keyframe` | Keyframe |
| `InterpolationType` | Interpolation enum (STEP, LINEAR) |
| `Time` | Time representation |
| `TimeRange` | Time range |
| `TimelineSerializer` | JSON serialization |

### Functions

| Function | Description |
|----------|-------------|
| `seconds_to_frame()` | Convert seconds to frame number |
| `frame_to_seconds()` | Convert frame to seconds |

## Integration Points

### With core/scene

`core/timeline` does not directly depend on `core/scene`. Integration is done via:
- Generic `target_id`: References scene objects by ID
- Generic `property_name`: References object properties by name
- Evaluation returns raw values that can be applied to scene objects

### Future Integrations

Future modules may use timeline:
- **Character animation**: Tracks for bone transforms
- **Camera animation**: Tracks for camera properties
- **VFX animation**: Tracks for effect parameters
- **Audio sync**: Timeline for audio event triggers

## Known Limitations

1. **No bezier/curve editing**: Only STEP and LINEAR interpolation
2. **No animation curves UI**: Data-only interface
3. **No keyframe easing functions**: Simple interpolation only
4. **No animation groups/layers**: Flat track structure
5. **No animation blending**: Single interpolation mode per segment

## Future Extension Points

1. **Advanced interpolation**: Bezier, cubic, easing functions
2. **Animation curves**: Custom interpolation curves
3. **Layer system**: Multiple animation layers
4. **Animation groups**: Group related tracks
5. **Animation clips**: Reusable animation sequences
6. **Inverse kinematics**: IK support for character animation

## Dependencies

- `pydantic>=2.0.0`: Data validation (shared with core/project, core/scene)

## No Dependencies On

This module does not depend on:
- `core/project`
- `core/scene`
- `core/character`
- `core/camera`
- `core/asset`
- `tools/*`
- `agents/*`
- `runtime/*`
- `apps/*`
