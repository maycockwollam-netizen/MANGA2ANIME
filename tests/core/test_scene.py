"""Tests for core/scene module."""

import json

import pytest

from core.scene import (
    EulerRotation,
    ObjectMetadata,
    Scene,
    SceneDuplicateIDError,
    SceneError,
    SceneHierarchyError,
    SceneMetadata,
    SceneNotFoundError,
    SceneObject,
    SceneObjectError,
    SceneSerializationError,
    SceneSerializer,
    SceneSettings,
    SceneValidationError,
    Transform,
    Vector2,
    Vector3,
)


class TestVector2:
    """Tests for Vector2."""

    def test_create_vector2_defaults(self) -> None:
        """Test creating Vector2 with defaults."""
        v = Vector2()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_create_vector2_values(self) -> None:
        """Test creating Vector2 with values."""
        v = Vector2(x=1.5, y=2.5)
        assert v.x == 1.5
        assert v.y == 2.5

    def test_vector2_nan_rejected(self) -> None:
        """Test that NaN values are rejected."""
        with pytest.raises(ValueError, match="NaN"):
            Vector2(x=float("nan"), y=0.0)


class TestVector3:
    """Tests for Vector3."""

    def test_create_vector3_defaults(self) -> None:
        """Test creating Vector3 with defaults."""
        v = Vector3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_create_vector3_values(self) -> None:
        """Test creating Vector3 with values."""
        v = Vector3(x=1.0, y=2.0, z=3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_to_vector2(self) -> None:
        """Test converting Vector3 to Vector2."""
        v3 = Vector3(x=1.0, y=2.0, z=3.0)
        v2 = v3.to_vector2()
        assert v2.x == 1.0
        assert v2.y == 2.0


class TestEulerRotation:
    """Tests for EulerRotation."""

    def test_create_rotation_defaults(self) -> None:
        """Test creating EulerRotation with defaults."""
        r = EulerRotation()
        assert r.x == 0.0
        assert r.y == 0.0
        assert r.z == 0.0

    def test_create_rotation_values(self) -> None:
        """Test creating EulerRotation with values."""
        r = EulerRotation(x=45.0, y=90.0, z=180.0)
        assert r.x == 45.0
        assert r.y == 90.0
        assert r.z == 180.0


class TestTransform:
    """Tests for Transform."""

    def test_create_transform_defaults(self) -> None:
        """Test creating Transform with defaults."""
        t = Transform()
        assert t.position.x == 0.0
        assert t.rotation.x == 0.0
        assert t.scale.x == 1.0
        assert t.scale.y == 1.0
        assert t.scale.z == 1.0

    def test_create_transform_values(self) -> None:
        """Test creating Transform with custom values."""
        t = Transform(
            position=Vector3(x=10.0, y=20.0, z=30.0),
            rotation=EulerRotation(x=45.0, y=0.0, z=0.0),
            scale=Vector3(x=2.0, y=2.0, z=2.0),
        )
        assert t.position.x == 10.0
        assert t.rotation.x == 45.0
        assert t.scale.x == 2.0

    def test_transform_zero_scale_rejected(self) -> None:
        """Test that zero scale is rejected."""
        with pytest.raises(ValueError, match="cannot be zero"):
            Transform(scale=Vector3(x=0.0, y=1.0, z=1.0))

    def test_is_2d(self) -> None:
        """Test 2D detection."""
        t2d = Transform(position=Vector3(x=0, y=0, z=0), rotation=EulerRotation(x=0, y=0))
        assert t2d.is_2d() is True

        t3d = Transform(position=Vector3(x=0, y=0, z=1))
        assert t3d.is_2d() is False


class TestObjectMetadata:
    """Tests for ObjectMetadata."""

    def test_create_metadata_defaults(self) -> None:
        """Test creating ObjectMetadata with defaults."""
        m = ObjectMetadata()
        assert m.created_at is not None
        assert m.updated_at is not None


class TestSceneObject:
    """Tests for SceneObject."""

    def test_create_object_defaults(self) -> None:
        """Test creating SceneObject with defaults."""
        obj = SceneObject()
        assert obj.id is not None
        assert obj.name == ""
        assert obj.object_type == "generic"
        assert obj.parent_id is None
        assert obj.visible is True
        assert obj.enabled is True
        assert obj.transform is not None

    def test_create_object_values(self) -> None:
        """Test creating SceneObject with values."""
        obj = SceneObject(
            name="Test Object",
            object_type="character",
            visible=False,
        )
        assert obj.name == "Test Object"
        assert obj.object_type == "character"
        assert obj.visible is False

    def test_object_unique_id(self) -> None:
        """Test that each object gets unique ID."""
        obj1 = SceneObject()
        obj2 = SceneObject()
        assert obj1.id != obj2.id

    def test_self_parenting_rejected(self) -> None:
        """Test that self-parenting is rejected."""
        obj = SceneObject()
        obj.parent_id = obj.id
        with pytest.raises(ValueError, match="cannot be its own parent"):
            SceneObject.model_validate(obj.model_dump())

    def test_set_parent(self) -> None:
        """Test setting parent."""
        obj = SceneObject(id="child")
        obj.set_parent("parent-123")
        assert obj.parent_id == "parent-123"

    def test_set_self_parent_rejected(self) -> None:
        """Test that set_parent rejects self-parenting."""
        obj = SceneObject()
        with pytest.raises(ValueError, match="cannot be its own parent"):
            obj.set_parent(obj.id)

    def test_remove_parent(self) -> None:
        """Test removing parent."""
        obj = SceneObject()
        obj.set_parent("parent-123")
        obj.remove_parent()
        assert obj.parent_id is None

    def test_update_transform(self) -> None:
        """Test updating transform."""
        obj = SceneObject()
        obj.update_transform(position=(10.0, 20.0, 30.0))
        assert obj.transform.position.x == 10.0
        assert obj.transform.position.y == 20.0
        assert obj.transform.position.z == 30.0


class TestSceneMetadata:
    """Tests for SceneMetadata."""

    def test_create_metadata_defaults(self) -> None:
        """Test creating SceneMetadata with defaults."""
        m = SceneMetadata()
        assert m.name == ""
        assert m.description == ""
        assert m.created_at is not None
        assert m.updated_at is not None


class TestSceneSettings:
    """Tests for SceneSettings."""

    def test_create_settings_defaults(self) -> None:
        """Test creating SceneSettings with defaults."""
        s = SceneSettings()
        assert s.background_color == "#000000"
        assert s.ambient_light == 0.5

    def test_invalid_ambient_light(self) -> None:
        """Test that invalid ambient light is rejected."""
        with pytest.raises(ValueError):
            SceneSettings(ambient_light=2.0)


class TestScene:
    """Tests for Scene."""

    def test_create_scene_defaults(self) -> None:
        """Test creating Scene with defaults."""
        scene = Scene()
        assert scene.id is not None
        assert scene.metadata is not None
        assert scene.settings is not None
        assert scene.objects == {}

    def test_create_scene_values(self) -> None:
        """Test creating Scene with values."""
        scene = Scene(
            metadata=SceneMetadata(name="Test Scene"),
            settings=SceneSettings(background_color="#ffffff"),
        )
        assert scene.metadata.name == "Test Scene"
        assert scene.settings.background_color == "#ffffff"

    def test_scene_unique_id(self) -> None:
        """Test that each scene gets unique ID."""
        scene1 = Scene()
        scene2 = Scene()
        assert scene1.id != scene2.id

    def test_add_object(self) -> None:
        """Test adding an object to scene."""
        scene = Scene()
        obj = SceneObject(name="Test Object")
        added = scene.add_object(obj)
        assert added.id in scene.objects
        assert scene.has_object(added.id)

    def test_add_duplicate_object_rejected(self) -> None:
        """Test that adding duplicate object ID is rejected."""
        scene = Scene()
        obj = SceneObject(id="same-id")
        scene.add_object(obj)
        with pytest.raises(SceneDuplicateIDError):
            scene.add_object(SceneObject(id="same-id"))

    def test_remove_object(self) -> None:
        """Test removing an object."""
        scene = Scene()
        obj = scene.add_object(SceneObject(name="To Remove"))
        scene.remove_object(obj.id)
        assert not scene.has_object(obj.id)

    def test_remove_nonexistent_object(self) -> None:
        """Test removing nonexistent object raises error."""
        scene = Scene()
        with pytest.raises(SceneNotFoundError):
            scene.remove_object("nonexistent-id")

    def test_get_object(self) -> None:
        """Test getting an object."""
        scene = Scene()
        obj = scene.add_object(SceneObject(name="Get Me"))
        retrieved = scene.get_object(obj.id)
        assert retrieved.id == obj.id
        assert retrieved.name == "Get Me"

    def test_get_nonexistent_object(self) -> None:
        """Test getting nonexistent object raises error."""
        scene = Scene()
        with pytest.raises(SceneNotFoundError):
            scene.get_object("nonexistent-id")

    def test_update_object(self) -> None:
        """Test updating an object."""
        scene = Scene()
        obj = scene.add_object(SceneObject(name="Original"))
        updated = scene.update_object(obj.id, name="Updated")
        assert updated.name == "Updated"

    def test_has_object(self) -> None:
        """Test checking object existence."""
        scene = Scene()
        obj = scene.add_object(SceneObject())
        assert scene.has_object(obj.id) is True
        assert scene.has_object("nonexistent") is False


class TestSceneHierarchy:
    """Tests for scene hierarchy."""

    def test_set_parent(self) -> None:
        """Test setting parent relationship."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent", name="Parent"))
        child = scene.add_object(SceneObject(id="child", name="Child"))
        scene.set_parent(child.id, parent.id)
        assert child.parent_id == parent.id

    def test_set_nonexistent_parent(self) -> None:
        """Test setting nonexistent parent raises error."""
        scene = Scene()
        child = scene.add_object(SceneObject(id="child"))
        with pytest.raises(SceneHierarchyError, match="not found"):
            scene.set_parent(child.id, "nonexistent")

    def test_self_parenting(self) -> None:
        """Test that self-parenting is rejected."""
        scene = Scene()
        obj = scene.add_object(SceneObject(id="self"))
        with pytest.raises(SceneHierarchyError, match="cannot be its own parent"):
            scene.set_parent(obj.id, obj.id)

    def test_circular_hierarchy(self) -> None:
        """Test that circular hierarchy is rejected."""
        scene = Scene()
        obj1 = scene.add_object(SceneObject(id="obj1"))
        obj2 = scene.add_object(SceneObject(id="obj2"))
        scene.set_parent(obj1.id, obj2.id)
        with pytest.raises(SceneHierarchyError, match="circular"):
            scene.set_parent(obj2.id, obj1.id)

    def test_complex_hierarchy_cycle(self) -> None:
        """Test cycle detection in complex hierarchy."""
        scene = Scene()
        a = scene.add_object(SceneObject(id="a"))
        b = scene.add_object(SceneObject(id="b"))
        c = scene.add_object(SceneObject(id="c"))
        scene.set_parent(a.id, b.id)
        scene.set_parent(b.id, c.id)
        with pytest.raises(SceneHierarchyError, match="circular"):
            scene.set_parent(c.id, a.id)

    def test_get_children(self) -> None:
        """Test getting children of an object."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent"))
        child1 = scene.add_object(SceneObject(id="child1"))
        child2 = scene.add_object(SceneObject(id="child2"))
        scene.set_parent(child1.id, parent.id)
        scene.set_parent(child2.id, parent.id)
        child_ids = scene.get_children(parent.id)
        assert set(child_ids) == {"child1", "child2"}

    def test_get_root_objects(self) -> None:
        """Test getting root objects (no parent)."""
        scene = Scene()
        root1 = scene.add_object(SceneObject(id="root1"))
        scene.add_object(SceneObject(id="root2"))
        child = scene.add_object(SceneObject(id="child"))
        scene.set_parent(child.id, root1.id)
        roots = scene.get_root_objects()
        root_ids = {obj.id for obj in roots}
        assert root_ids == {"root1", "root2"}

    def test_remove_object_with_children(self) -> None:
        """Test removing object with children (no cascade)."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent"))
        child = scene.add_object(SceneObject(id="child"))
        scene.set_parent(child.id, parent.id)
        scene.remove_object(parent.id, cascade=False)
        assert not scene.has_object(parent.id)
        assert scene.has_object(child.id)
        assert child.parent_id is None

    def test_remove_object_with_children_cascade(self) -> None:
        """Test removing object with children (cascade)."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent"))
        child = scene.add_object(SceneObject(id="child"))
        scene.set_parent(child.id, parent.id)
        scene.remove_object(parent.id, cascade=True)
        assert not scene.has_object(parent.id)
        assert not scene.has_object(child.id)

    def test_remove_parent(self) -> None:
        """Test removing parent (setting to None)."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent"))
        child = scene.add_object(SceneObject(id="child"))
        scene.set_parent(child.id, parent.id)
        scene.set_parent(child.id, None)
        assert child.parent_id is None

    def test_get_hierarchy_tree(self) -> None:
        """Test getting hierarchy as tree."""
        scene = Scene(metadata=SceneMetadata(name="Test Scene"))
        root = scene.add_object(SceneObject(id="root", name="Root"))
        child = scene.add_object(SceneObject(id="child", name="Child"))
        scene.set_parent(child.id, root.id)
        tree = scene.get_hierarchy_tree()
        assert tree["id"] == scene.id
        assert tree["name"] == "Test Scene"
        assert len(tree["children"]) == 1
        assert tree["children"][0]["id"] == "root"
        assert len(tree["children"][0]["children"]) == 1
        assert tree["children"][0]["children"][0]["id"] == "child"


class TestSceneValidation:
    """Tests for scene validation."""

    def test_validate_valid_scene(self) -> None:
        """Test validating a valid scene."""
        scene = Scene(metadata=SceneMetadata(name="Valid Scene"))
        errors = scene.validate()
        assert errors == []

    def test_validate_empty_name(self) -> None:
        """Test validation allows empty name."""
        scene = Scene(metadata=SceneMetadata(name=""))
        errors = scene.validate()
        assert errors == []

    def test_validate_invalid_hierarchy(self) -> None:
        """Test validation detects invalid hierarchy."""
        scene = Scene()
        parent = scene.add_object(SceneObject(id="parent"))
        child = scene.add_object(SceneObject(id="child"))
        scene.set_parent(child.id, parent.id)
        # Manually break hierarchy for test
        scene.objects["child"].parent_id = "nonexistent"
        errors = scene.validate()
        assert any("invalid parent" in e.lower() for e in errors)

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise raises on invalid."""
        scene = Scene()
        scene.add_object(SceneObject(id="obj"))
        scene.objects["obj"].parent_id = "nonexistent"
        with pytest.raises(SceneValidationError):
            scene.validate_or_raise()


class TestSceneSerialization:
    """Tests for scene serialization."""

    def test_serialize_empty_scene(self) -> None:
        """Test serializing empty scene."""
        scene = Scene()
        data = SceneSerializer.serialize(scene)
        assert data["id"] == scene.id
        assert data["metadata"]["name"] == ""
        assert data["objects"] == {}

    def test_serialize_scene_with_objects(self) -> None:
        """Test serializing scene with objects."""
        scene = Scene(metadata=SceneMetadata(name="Test Scene"))
        obj = scene.add_object(SceneObject(name="Object 1", object_type="character"))
        data = SceneSerializer.serialize(scene)
        assert obj.id in data["objects"]
        assert data["objects"][obj.id]["name"] == "Object 1"
        assert data["objects"][obj.id]["object_type"] == "character"

    def test_deserialize_scene(self) -> None:
        """Test deserializing scene."""
        scene = Scene(metadata=SceneMetadata(name="Original"))
        data = SceneSerializer.serialize(scene)
        restored = SceneSerializer.deserialize(data)
        assert restored.id == scene.id
        assert restored.metadata.name == "Original"

    def test_roundtrip_preservation(self) -> None:
        """Test serialization roundtrip preserves data."""
        scene = Scene(metadata=SceneMetadata(name="Roundtrip Test"))
        obj1 = scene.add_object(SceneObject(id="obj1", name="Obj1", object_type="background"))
        obj2 = scene.add_object(SceneObject(id="obj2", name="Obj2"))
        scene.set_parent(obj2.id, obj1.id)
        obj1.custom_data = {"key": "value"}

        data = SceneSerializer.serialize(scene)
        restored = SceneSerializer.deserialize(data)

        assert restored.id == scene.id
        assert restored.metadata.name == "Roundtrip Test"
        assert "obj1" in restored.objects
        assert "obj2" in restored.objects
        assert restored.objects["obj2"].parent_id == "obj1"
        assert restored.objects["obj1"].custom_data == {"key": "value"}

    def test_to_json(self) -> None:
        """Test serializing to JSON."""
        scene = Scene(metadata=SceneMetadata(name="JSON Test"))
        json_str = SceneSerializer.to_json(scene)
        data = json.loads(json_str)
        assert data["metadata"]["name"] == "JSON Test"

    def test_from_json(self) -> None:
        """Test deserializing from JSON."""
        scene = Scene(metadata=SceneMetadata(name="JSON Test"))
        json_str = SceneSerializer.to_json(scene)
        restored = SceneSerializer.from_json(json_str)
        assert restored.metadata.name == "JSON Test"

    def test_deserialize_invalid_data(self) -> None:
        """Test deserializing invalid data raises error."""
        with pytest.raises(SceneSerializationError, match="Missing required field"):
            SceneSerializer.deserialize({})

    def test_from_invalid_json(self) -> None:
        """Test from_json raises error for invalid JSON."""
        with pytest.raises(SceneSerializationError, match="Invalid JSON"):
            SceneSerializer.from_json("not valid json {{{")


class TestSceneExceptions:
    """Tests for scene exceptions."""

    def test_validation_error_with_errors(self) -> None:
        """Test SceneValidationError contains error list."""
        error = SceneValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)

    def test_scene_error_hierarchy(self) -> None:
        """Test exception hierarchy."""
        assert issubclass(SceneHierarchyError, SceneObjectError)
        assert issubclass(SceneObjectError, SceneError)
        assert issubclass(SceneNotFoundError, SceneObjectError)
        assert issubclass(SceneDuplicateIDError, SceneObjectError)

    def test_scene_error_raising(self) -> None:
        """Test exceptions can be raised."""
        with pytest.raises(SceneNotFoundError):
            raise SceneNotFoundError("Not found")

        with pytest.raises(SceneDuplicateIDError):
            raise SceneDuplicateIDError("Duplicate ID")

        with pytest.raises(SceneHierarchyError):
            raise SceneHierarchyError("Invalid hierarchy")
