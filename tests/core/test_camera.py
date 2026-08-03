"""Tests for core/camera module."""

import json

import pytest

from core.camera import (
    Camera,
    CameraCollection,
    CameraDuplicateIDError,
    CameraError,
    CameraNotFoundError,
    CameraProjectionError,
    CameraReferenceError,
    CameraReferences,
    CameraSerializationError,
    CameraSerializer,
    CameraState,
    CameraTransform,
    CameraValidationError,
    Framing,
    OrthographicProjection,
    PerspectiveProjection,
    Projection,
    ProjectionType,
    Viewport,
)


class TestCameraCreation:
    """Tests for camera creation."""

    def test_create_camera_defaults(self) -> None:
        """Test creating camera with defaults."""
        cam = Camera()
        assert cam.id is not None
        assert cam.name == ""
        assert cam.metadata is not None
        assert cam.transform is not None
        assert cam.projection is not None
        assert cam.viewport is not None
        assert cam.framing is not None
        assert cam.state is not None
        assert cam.references is not None

    def test_create_camera_with_values(self) -> None:
        """Test creating camera with values."""
        cam = Camera(name="Main Camera")
        assert cam.name == "Main Camera"

    def test_camera_unique_id(self) -> None:
        """Test that each camera gets unique ID."""
        cam1 = Camera()
        cam2 = Camera()
        assert cam1.id != cam2.id

    def test_camera_with_custom_id(self) -> None:
        """Test creating camera with custom ID."""
        cam = Camera(id="custom-id-123")
        assert cam.id == "custom-id-123"


class TestCameraTransform:
    """Tests for camera transform."""

    def test_transform_defaults(self) -> None:
        """Test transform defaults."""
        transform = CameraTransform()
        assert transform.position_x == 0.0
        assert transform.position_y == 0.0
        assert transform.position_z == 0.0
        assert transform.rotation_x == 0.0
        assert transform.rotation_y == 0.0
        assert transform.rotation_z == 0.0

    def test_transform_with_values(self) -> None:
        """Test transform with values."""
        transform = CameraTransform(
            position_x=10.0,
            position_y=20.0,
            position_z=30.0,
            rotation_x=45.0,
        )
        assert transform.position_x == 10.0
        assert transform.rotation_x == 45.0

    def test_is_2d(self) -> None:
        """Test 2D detection."""
        transform_2d = CameraTransform(position_z=0.0, rotation_x=0.0, rotation_y=0.0)
        assert transform_2d.is_2d() is True

        transform_3d = CameraTransform(position_z=10.0)
        assert transform_3d.is_2d() is False


class TestProjectionType:
    """Tests for ProjectionType enum."""

    def test_orthographic_value(self) -> None:
        """Test ORTHOGRAPHIC projection value."""
        assert ProjectionType.ORTHOGRAPHIC.value == "orthographic"

    def test_perspective_value(self) -> None:
        """Test PERSPECTIVE projection value."""
        assert ProjectionType.PERSPECTIVE.value == "perspective"


class TestOrthographicProjection:
    """Tests for orthographic projection."""

    def test_defaults(self) -> None:
        """Test orthographic defaults."""
        proj = OrthographicProjection()
        assert proj.size == 5.0

    def test_invalid_size_rejected(self) -> None:
        """Test that non-positive size is rejected."""
        with pytest.raises(ValueError):
            OrthographicProjection(size=0.0)

        with pytest.raises(ValueError):
            OrthographicProjection(size=-1.0)


class TestPerspectiveProjection:
    """Tests for perspective projection."""

    def test_defaults(self) -> None:
        """Test perspective defaults."""
        proj = PerspectiveProjection()
        assert proj.field_of_view == 60.0
        assert proj.near_clip == 0.1
        assert proj.far_clip == 1000.0

    def test_invalid_fov_rejected(self) -> None:
        """Test that invalid FOV is rejected."""
        with pytest.raises(ValueError):
            PerspectiveProjection(field_of_view=0.0)

        with pytest.raises(ValueError):
            PerspectiveProjection(field_of_view=180.0)

    def test_invalid_near_clip_rejected(self) -> None:
        """Test that non-positive near clip is rejected."""
        with pytest.raises(ValueError):
            PerspectiveProjection(near_clip=0.0)

    def test_invalid_far_clip_rejected(self) -> None:
        """Test that far clip <= near clip is rejected."""
        with pytest.raises(ValueError):
            PerspectiveProjection(near_clip=10.0, far_clip=5.0)


class TestProjection:
    """Tests for projection."""

    def test_defaults(self) -> None:
        """Test projection defaults."""
        proj = Projection()
        assert proj.type == ProjectionType.PERSPECTIVE
        assert proj.orthographic is not None
        assert proj.perspective is not None

    def test_set_orthographic(self) -> None:
        """Test setting orthographic type."""
        proj = Projection(type=ProjectionType.ORTHOGRAPHIC)
        assert proj.type == ProjectionType.ORTHOGRAPHIC

    def test_validate_orthographic(self) -> None:
        """Test validating orthographic projection."""
        proj = Projection(type=ProjectionType.ORTHOGRAPHIC)
        errors = proj.validate()
        assert errors == []


class TestViewport:
    """Tests for viewport."""

    def test_defaults(self) -> None:
        """Test viewport defaults."""
        vp = Viewport()
        assert vp.width == 1920
        assert vp.height == 1080

    def test_aspect_ratio(self) -> None:
        """Test aspect ratio calculation."""
        vp = Viewport(width=1920, height=1080)
        assert abs(vp.aspect_ratio - 16 / 9) < 0.001

    def test_invalid_width_rejected(self) -> None:
        """Test that non-positive width is rejected."""
        with pytest.raises(ValueError):
            Viewport(width=0)

        with pytest.raises(ValueError):
            Viewport(width=-1)

    def test_invalid_height_rejected(self) -> None:
        """Test that non-positive height is rejected."""
        with pytest.raises(ValueError):
            Viewport(height=0)


class TestFraming:
    """Tests for framing."""

    def test_defaults(self) -> None:
        """Test framing defaults."""
        framing = Framing()
        assert framing.center_x == 0.0
        assert framing.center_y == 0.0
        assert framing.size_width == 1.0
        assert framing.size_height == 1.0
        assert framing.zoom == 1.0
        assert framing.margin_left == 0.0

    def test_invalid_size_rejected(self) -> None:
        """Test that non-positive size is rejected."""
        with pytest.raises(ValueError):
            Framing(size_width=0.0)

        with pytest.raises(ValueError):
            Framing(size_height=0.0)

    def test_invalid_zoom_rejected(self) -> None:
        """Test that non-positive zoom is rejected."""
        with pytest.raises(ValueError):
            Framing(zoom=0.0)


class TestCameraState:
    """Tests for camera state."""

    def test_defaults(self) -> None:
        """Test state defaults."""
        state = CameraState()
        assert state.enabled is True
        assert state.active is False

    def test_with_values(self) -> None:
        """Test state with values."""
        state = CameraState(enabled=False, active=True)
        assert state.enabled is False
        assert state.active is True


class TestCameraReferences:
    """Tests for camera references."""

    def test_defaults(self) -> None:
        """Test references defaults."""
        refs = CameraReferences()
        assert refs.scene_id == ""
        assert refs.target_id == ""

    def test_scene_reference(self) -> None:
        """Test scene reference operations."""
        refs = CameraReferences()
        refs.set_scene_reference("scene-001")
        assert refs.get_scene_reference() == "scene-001"

    def test_target_reference(self) -> None:
        """Test target reference operations."""
        refs = CameraReferences()
        refs.set_target_reference("target-001")
        assert refs.get_target_reference() == "target-001"


class TestCamera:
    """Tests for main camera model."""

    def test_update_name(self) -> None:
        """Test updating camera name."""
        cam = Camera(name="Original")
        cam.update_name("Updated")
        assert cam.name == "Updated"

    def test_set_enabled(self) -> None:
        """Test setting enabled state."""
        cam = Camera()
        cam.set_enabled(False)
        assert cam.state.enabled is False

    def test_set_active(self) -> None:
        """Test setting active state."""
        cam = Camera()
        cam.set_active(True)
        assert cam.state.active is True

    def test_tags(self) -> None:
        """Test tag operations."""
        cam = Camera()
        cam.add_tag("main")
        assert cam.has_tag("main") is True
        cam.remove_tag("main")
        assert cam.has_tag("main") is False

    def test_set_projection_type(self) -> None:
        """Test setting projection type."""
        cam = Camera()
        cam.set_projection_type(ProjectionType.ORTHOGRAPHIC)
        assert cam.projection.type == ProjectionType.ORTHOGRAPHIC

    def test_scene_reference(self) -> None:
        """Test scene reference through camera."""
        cam = Camera()
        cam.set_scene_reference("scene-001")
        assert cam.get_scene_reference() == "scene-001"

    def test_target_reference(self) -> None:
        """Test target reference through camera."""
        cam = Camera()
        cam.set_target_reference("target-001")
        assert cam.get_target_reference() == "target-001"


class TestCameraValidation:
    """Tests for camera validation."""

    def test_validate_valid_camera(self) -> None:
        """Test validating a valid camera."""
        cam = Camera(name="Valid Camera")
        errors = cam.validate()
        assert errors == []

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise works for valid camera."""
        cam = Camera(name="Valid")
        cam.validate_or_raise()  # Should not raise


class TestCameraCollection:
    """Tests for camera collection."""

    def test_create_empty_collection(self) -> None:
        """Test creating empty collection."""
        collection = CameraCollection()
        assert collection.count() == 0

    def test_add_camera(self) -> None:
        """Test adding camera to collection."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        assert collection.count() == 1
        assert collection.has(cam.id) is True

    def test_add_duplicate_rejected(self) -> None:
        """Test adding duplicate camera raises error."""
        collection = CameraCollection()
        cam = Camera(id="same-id", name="Camera 1")
        collection.add(cam)
        with pytest.raises(CameraDuplicateIDError):
            collection.add(Camera(id="same-id", name="Camera 2"))

    def test_remove_camera(self) -> None:
        """Test removing camera from collection."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        removed = collection.remove(cam.id)
        assert removed.name == "Main Camera"
        assert collection.count() == 0

    def test_remove_nonexistent(self) -> None:
        """Test removing nonexistent camera raises error."""
        collection = CameraCollection()
        with pytest.raises(CameraNotFoundError):
            collection.remove("nonexistent")

    def test_get_camera(self) -> None:
        """Test getting camera from collection."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        retrieved = collection.get(cam.id)
        assert retrieved.name == "Main Camera"

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent camera raises error."""
        collection = CameraCollection()
        with pytest.raises(CameraNotFoundError):
            collection.get("nonexistent")

    def test_has_camera(self) -> None:
        """Test checking camera existence."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        assert collection.has(cam.id) is True
        assert collection.has("nonexistent") is False

    def test_list_cameras(self) -> None:
        """Test listing cameras."""
        collection = CameraCollection()
        cam1 = Camera(name="Zara")
        cam2 = Camera(name="Alpha")
        collection.add(cam1)
        collection.add(cam2)
        names = [c.name for c in collection.list()]
        assert names == ["Alpha", "Zara"]

    def test_list_by_tag(self) -> None:
        """Test listing cameras by tag."""
        collection = CameraCollection()
        cam1 = Camera(name="Main")
        cam1.add_tag("primary")
        cam2 = Camera(name="Secondary")
        collection.add(cam1)
        collection.add(cam2)
        primary = collection.list_by_tag("primary")
        assert len(primary) == 1
        assert primary[0].name == "Main"

    def test_find_by_name(self) -> None:
        """Test finding camera by name."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        found = collection.find_by_name("Main Camera")
        assert found is not None
        assert found.name == "Main Camera"

    def test_get_active(self) -> None:
        """Test getting active cameras."""
        collection = CameraCollection()
        cam1 = Camera(name="Active")
        cam1.set_active(True)
        cam2 = Camera(name="Inactive")
        collection.add(cam1)
        collection.add(cam2)
        active = collection.get_active()
        assert len(active) == 1
        assert active[0].name == "Active"

    def test_count(self) -> None:
        """Test counting cameras."""
        collection = CameraCollection()
        assert collection.count() == 0
        collection.add(Camera(name="A"))
        collection.add(Camera(name="B"))
        assert collection.count() == 2

    def test_clear(self) -> None:
        """Test clearing collection."""
        collection = CameraCollection()
        collection.add(Camera(name="A"))
        collection.add(Camera(name="B"))
        collection.clear()
        assert collection.count() == 0

    def test_update(self) -> None:
        """Test updating camera."""
        collection = CameraCollection()
        cam = Camera(id="cam-1", name="Original")
        collection.add(cam)
        updated = collection.update(cam.id, name="Updated")
        assert updated.name == "Updated"

    def test_iteration(self) -> None:
        """Test iterating over collection."""
        collection = CameraCollection()
        cam1 = Camera(name="B")
        cam2 = Camera(name="A")
        collection.add(cam1)
        collection.add(cam2)
        names = [c.name for c in collection]
        assert names == ["A", "B"]

    def test_bracket_notation(self) -> None:
        """Test bracket notation access."""
        collection = CameraCollection()
        cam = Camera(name="Main Camera")
        collection.add(cam)
        retrieved = collection[cam.id]
        assert retrieved.name == "Main Camera"


class TestCameraSerialization:
    """Tests for camera serialization."""

    def test_serialize_empty_camera(self) -> None:
        """Test serializing camera with defaults."""
        cam = Camera()
        data = CameraSerializer.serialize(cam)
        assert data["id"] == cam.id
        assert data["name"] == ""

    def test_serialize_full_camera(self) -> None:
        """Test serializing full camera."""
        cam = Camera(name="Main Camera")
        cam.set_projection_type(ProjectionType.ORTHOGRAPHIC)
        cam.set_scene_reference("scene-001")

        data = CameraSerializer.serialize(cam)
        assert data["name"] == "Main Camera"
        assert data["projection"]["type"] == "orthographic"
        assert data["references"]["scene_id"] == "scene-001"

    def test_deserialize_camera(self) -> None:
        """Test deserializing camera."""
        cam = Camera(name="Original")
        data = CameraSerializer.serialize(cam)
        restored = CameraSerializer.deserialize(data)
        assert restored.id == cam.id
        assert restored.name == "Original"

    def test_roundtrip_preservation(self) -> None:
        """Test serialization roundtrip preserves data."""
        cam = Camera(name="Main Camera")
        cam.add_tag("primary")
        cam.set_projection_type(ProjectionType.ORTHOGRAPHIC)
        cam.set_scene_reference("scene-001")
        cam.set_target_reference("target-001")
        cam.transform.position_x = 10.0
        cam.viewport.width = 1280
        cam.framing.zoom = 2.0

        data = CameraSerializer.serialize(cam)
        restored = CameraSerializer.deserialize(data)

        assert restored.id == cam.id
        assert restored.name == "Main Camera"
        assert "primary" in restored.metadata.tags
        assert restored.projection.type == ProjectionType.ORTHOGRAPHIC
        assert restored.get_scene_reference() == "scene-001"
        assert restored.get_target_reference() == "target-001"
        assert restored.transform.position_x == 10.0
        assert restored.viewport.width == 1280
        assert restored.framing.zoom == 2.0

    def test_to_json(self) -> None:
        """Test serializing to JSON."""
        cam = Camera(name="Main Camera")
        json_str = CameraSerializer.to_json(cam)
        data = json.loads(json_str)
        assert data["name"] == "Main Camera"

    def test_from_json(self) -> None:
        """Test deserializing from JSON."""
        cam = Camera(name="Main Camera")
        json_str = CameraSerializer.to_json(cam)
        restored = CameraSerializer.from_json(json_str)
        assert restored.name == "Main Camera"

    def test_deserialize_invalid_data(self) -> None:
        """Test deserializing invalid data raises error."""
        with pytest.raises(
            CameraSerializationError, match="Missing required field"
        ):
            CameraSerializer.deserialize({})

    def test_from_invalid_json(self) -> None:
        """Test from_json raises error for invalid JSON."""
        with pytest.raises(CameraSerializationError, match="Invalid JSON"):
            CameraSerializer.from_json("not valid json {{{")


class TestCameraExceptions:
    """Tests for camera exceptions."""

    def test_validation_error_with_errors(self) -> None:
        """Test CameraValidationError contains error list."""
        error = CameraValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)

    def test_exception_hierarchy(self) -> None:
        """Test exception hierarchy."""
        assert issubclass(CameraValidationError, CameraError)
        assert issubclass(CameraNotFoundError, CameraError)
        assert issubclass(CameraDuplicateIDError, CameraError)
        assert issubclass(CameraProjectionError, CameraError)
        assert issubclass(CameraSerializationError, CameraError)
        assert issubclass(CameraReferenceError, CameraError)

    def test_exception_raising(self) -> None:
        """Test exceptions can be raised."""
        with pytest.raises(CameraNotFoundError):
            raise CameraNotFoundError("Not found")

        with pytest.raises(CameraDuplicateIDError):
            raise CameraDuplicateIDError("Duplicate ID")

        with pytest.raises(CameraReferenceError):
            raise CameraReferenceError("Invalid reference")
