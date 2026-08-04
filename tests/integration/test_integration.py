"""Tests for integration layer."""

import pytest

from core.asset import Asset, AssetType
from core.camera import Camera
from core.character import Character
from core.project import Project
from core.scene import Scene, SceneObject
from core.timeline import Timeline, Track
from integration import (
    DanglingReferenceError,
    DuplicateRegistrationError,
    EntityNotFoundError,
    IntegrationError,
    IntegrationValidationError,
    IntegrationValidator,
    ProjectContext,
    ReferenceResolutionError,
    ReferenceResolver,
    Registry,
)


class TestRegistry:
    """Tests for Registry."""

    def test_create_empty_registry(self) -> None:
        """Test creating empty registry."""
        registry = Registry()
        assert registry.count() == 0

    def test_register_entity(self) -> None:
        """Test registering an entity."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        assert registry.count() == 1
        assert registry.exists("scene-1")

    def test_register_duplicate_rejected(self) -> None:
        """Test registering duplicate entity raises error."""
        registry = Registry()
        scene1 = Scene(id="scene-1", name="Scene 1")
        scene2 = Scene(id="scene-1", name="Scene 2")
        registry.register(scene1)
        with pytest.raises(DuplicateRegistrationError):
            registry.register(scene2)

    def test_unregister_entity(self) -> None:
        """Test unregistering an entity."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        removed = registry.unregister("scene-1")
        assert removed.id == "scene-1"
        assert registry.count() == 0

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering nonexistent entity raises error."""
        registry = Registry()
        with pytest.raises(EntityNotFoundError):
            registry.unregister("nonexistent")

    def test_get_entity(self) -> None:
        """Test getting an entity."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        retrieved = registry.get("scene-1")
        assert retrieved.id == "scene-1"

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent entity raises error."""
        registry = Registry()
        with pytest.raises(EntityNotFoundError):
            registry.get("nonexistent")

    def test_exists(self) -> None:
        """Test checking entity existence."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        assert registry.exists("scene-1") is True
        assert registry.exists("nonexistent") is False

    def test_list_entities(self) -> None:
        """Test listing entities."""
        registry = Registry()
        scene1 = Scene(id="b-scene", name="B Scene")
        scene2 = Scene(id="a-scene", name="A Scene")
        registry.register(scene1)
        registry.register(scene2)
        names = [s.id for s in registry.list()]
        assert names == ["a-scene", "b-scene"]

    def test_clear(self) -> None:
        """Test clearing registry."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        registry.clear()
        assert registry.count() == 0

    def test_iteration(self) -> None:
        """Test iterating over registry."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        for s in registry:
            assert s.id == "scene-1"

    def test_bracket_notation(self) -> None:
        """Test bracket notation access."""
        registry = Registry()
        scene = Scene(id="scene-1", name="Test Scene")
        registry.register(scene)
        retrieved = registry["scene-1"]
        assert retrieved.id == "scene-1"


class TestProjectContext:
    """Tests for ProjectContext."""

    def test_create_empty_context(self) -> None:
        """Test creating empty context."""
        context = ProjectContext()
        assert context.total_count() == 0
        assert context.has_project() is False

    def test_set_and_get_project(self) -> None:
        """Test setting and getting project."""
        context = ProjectContext()
        project = Project(id="project-1", name="Test Project")
        context.set_project(project)
        assert context.has_project()
        assert context.get_project().id == "project-1"

    def test_register_scenes(self) -> None:
        """Test registering scenes."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        context.register_scene(scene)
        assert context.has_scene("scene-1")
        assert context.scene_count() == 1

    def test_register_characters(self) -> None:
        """Test registering characters."""
        context = ProjectContext()
        character = Character(id="char-1", name="Test Character")
        context.register_character(character)
        assert context.has_character("char-1")
        assert context.character_count() == 1

    def test_register_cameras(self) -> None:
        """Test registering cameras."""
        context = ProjectContext()
        camera = Camera(id="cam-1", name="Test Camera")
        context.register_camera(camera)
        assert context.has_camera("cam-1")
        assert context.camera_count() == 1

    def test_register_timelines(self) -> None:
        """Test registering timelines."""
        context = ProjectContext()
        timeline = Timeline(id="timeline-1", name="Test Timeline")
        context.register_timeline(timeline)
        assert context.has_timeline("timeline-1")
        assert context.timeline_count() == 1

    def test_register_assets(self) -> None:
        """Test registering assets."""
        context = ProjectContext()
        asset = Asset(id="asset-1", name="Test Asset", asset_type=AssetType.IMAGE)
        context.register_asset(asset)
        assert context.has_asset("asset-1")
        assert context.asset_count() == 1

    def test_register_duplicate_rejected(self) -> None:
        """Test registering duplicate entities raises error."""
        context = ProjectContext()
        scene1 = Scene(id="scene-1", name="Scene 1")
        scene2 = Scene(id="scene-1", name="Scene 2")
        context.register_scene(scene1)
        with pytest.raises(DuplicateRegistrationError):
            context.register_scene(scene2)

    def test_unregister_entities(self) -> None:
        """Test unregistering entities."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        context.register_scene(scene)
        removed = context.unregister_scene("scene-1")
        assert removed.id == "scene-1"
        assert context.scene_count() == 0

    def test_list_entities(self) -> None:
        """Test listing entities."""
        context = ProjectContext()
        scene1 = Scene(id="b-scene", name="B Scene")
        scene2 = Scene(id="a-scene", name="A Scene")
        context.register_scene(scene1)
        context.register_scene(scene2)
        names = [s.id for s in context.list_scenes()]
        assert names == ["a-scene", "b-scene"]

    def test_clear_context(self) -> None:
        """Test clearing context."""
        context = ProjectContext()
        project = Project(id="project-1", name="Test Project")
        scene = Scene(id="scene-1", name="Test Scene")
        context.set_project(project)
        context.register_scene(scene)
        context.clear()
        assert context.total_count() == 0
        assert context.has_project() is False


class TestReferenceResolver:
    """Tests for ReferenceResolver."""

    def test_resolve_scene_reference(self) -> None:
        """Test resolving valid scene reference."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        context.register_scene(scene)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_scene_reference("scene-1")
        assert resolved.id == "scene-1"

    def test_resolve_empty_scene_reference(self) -> None:
        """Test resolving empty scene reference raises error."""
        context = ProjectContext()
        resolver = ReferenceResolver(context)
        with pytest.raises(ReferenceResolutionError):
            resolver.resolve_scene_reference("")

    def test_resolve_nonexistent_scene_reference(self) -> None:
        """Test resolving nonexistent scene reference raises error."""
        context = ProjectContext()
        resolver = ReferenceResolver(context)
        with pytest.raises(DanglingReferenceError):
            resolver.resolve_scene_reference("nonexistent")

    def test_resolve_character_reference(self) -> None:
        """Test resolving valid character reference."""
        context = ProjectContext()
        character = Character(id="char-1", name="Test Character")
        context.register_character(character)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_character_reference("char-1")
        assert resolved.id == "char-1"

    def test_resolve_nonexistent_character_reference(self) -> None:
        """Test resolving nonexistent character reference raises error."""
        context = ProjectContext()
        resolver = ReferenceResolver(context)
        with pytest.raises(DanglingReferenceError):
            resolver.resolve_character_reference("nonexistent")

    def test_resolve_camera_reference(self) -> None:
        """Test resolving valid camera reference."""
        context = ProjectContext()
        camera = Camera(id="cam-1", name="Test Camera")
        context.register_camera(camera)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_camera_reference("cam-1")
        assert resolved.id == "cam-1"

    def test_resolve_timeline_reference(self) -> None:
        """Test resolving valid timeline reference."""
        context = ProjectContext()
        timeline = Timeline(id="timeline-1", name="Test Timeline")
        context.register_timeline(timeline)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_timeline_reference("timeline-1")
        assert resolved.id == "timeline-1"

    def test_resolve_asset_reference(self) -> None:
        """Test resolving valid asset reference."""
        context = ProjectContext()
        asset = Asset(id="asset-1", name="Test Asset", asset_type=AssetType.IMAGE)
        context.register_asset(asset)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_asset_reference("asset-1")
        assert resolved.id == "asset-1"

    def test_resolve_object_reference(self) -> None:
        """Test resolving valid object reference."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        obj = SceneObject(id="obj-1", name="Test Object")
        scene.add_object(obj)
        context.register_scene(scene)
        resolver = ReferenceResolver(context)
        resolved = resolver.resolve_object_reference("scene-1", "obj-1")
        assert resolved.id == "obj-1"

    def test_resolve_object_reference_missing_scene(self) -> None:
        """Test resolving object reference with missing scene raises error."""
        context = ProjectContext()
        resolver = ReferenceResolver(context)
        with pytest.raises(DanglingReferenceError):
            resolver.resolve_object_reference("nonexistent", "obj-1")

    def test_resolve_object_reference_missing_object(self) -> None:
        """Test resolving object reference with missing object raises error."""
        from core.scene.exceptions import SceneNotFoundError

        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        context.register_scene(scene)
        resolver = ReferenceResolver(context)
        # Scene.get_object raises SceneNotFoundError
        with pytest.raises(SceneNotFoundError):
            resolver.resolve_object_reference("scene-1", "nonexistent")


class TestIntegrationValidator:
    """Tests for IntegrationValidator."""

    def test_validate_empty_context(self) -> None:
        """Test validating empty context."""
        context = ProjectContext()
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert errors == []

    def test_validate_valid_context(self) -> None:
        """Test validating valid context."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        character = Character(id="char-1", name="Test Character", scene_id="scene-1")
        context.register_scene(scene)
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert errors == []

    def test_validate_duplicate_ids(self) -> None:
        """Test detecting duplicate IDs."""
        context = ProjectContext()
        scene = Scene(id="duplicate-id", name="Scene 1")
        character = Character(id="duplicate-id", name="Character 1")
        context.register_scene(scene)
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert len(errors) > 0
        assert "Duplicate ID" in errors[0]

    def test_validate_missing_scene_reference(self) -> None:
        """Test detecting missing scene reference."""
        context = ProjectContext()
        character = Character(id="char-1", name="Test Character")
        character.set_scene_reference("nonexistent")
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert len(errors) > 0
        assert "non-existent scene" in errors[0]

    def test_validate_missing_object_reference(self) -> None:
        """Test detecting missing object reference."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        character = Character(id="char-1", name="Test Character")
        character.set_scene_reference("scene-1")
        character.set_object_reference("nonexistent")
        context.register_scene(scene)
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert len(errors) > 0
        assert "non-existent object" in errors[0]

    def test_validate_camera_scene_reference(self) -> None:
        """Test validating camera scene reference."""
        context = ProjectContext()
        scene = Scene(id="scene-1", name="Test Scene")
        camera = Camera(id="cam-1", name="Test Camera")
        camera.set_scene_reference("scene-1")
        context.register_scene(scene)
        context.register_camera(camera)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert errors == []

    def test_validate_missing_camera_scene_reference(self) -> None:
        """Test detecting missing camera scene reference."""
        context = ProjectContext()
        camera = Camera(id="cam-1", name="Test Camera")
        camera.set_scene_reference("nonexistent")
        context.register_camera(camera)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert len(errors) > 0
        assert "non-existent scene" in errors[0]

    def test_validate_asset_references(self) -> None:
        """Test validating asset references in characters."""
        context = ProjectContext()
        asset = Asset(id="asset-1", name="Design Asset", asset_type=AssetType.IMAGE)
        character = Character(
            id="char-1", name="Test Character", design_asset_id="asset-1"
        )
        context.register_asset(asset)
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert errors == []

    def test_validate_missing_asset_reference(self) -> None:
        """Test detecting missing asset reference."""
        context = ProjectContext()
        character = Character(id="char-1", name="Test Character")
        character.references.design_asset_id = "nonexistent"
        context.register_character(character)
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert len(errors) > 0
        assert "non-existent" in errors[0]

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise raises on invalid context."""
        context = ProjectContext()
        character = Character(id="char-1", name="Test Character")
        character.set_scene_reference("nonexistent")
        context.register_character(character)
        validator = IntegrationValidator(context)
        with pytest.raises(IntegrationValidationError):
            validator.validate_or_raise()


class TestIntegrationExceptions:
    """Tests for integration exceptions."""

    def test_integration_error(self) -> None:
        """Test IntegrationError."""
        with pytest.raises(IntegrationError):
            raise IntegrationError("Test error")

    def test_duplicate_registration_error(self) -> None:
        """Test DuplicateRegistrationError."""
        with pytest.raises(DuplicateRegistrationError):
            raise DuplicateRegistrationError("Duplicate")

    def test_entity_not_found_error(self) -> None:
        """Test EntityNotFoundError."""
        with pytest.raises(EntityNotFoundError):
            raise EntityNotFoundError("Not found")

    def test_reference_resolution_error(self) -> None:
        """Test ReferenceResolutionError."""
        error = ReferenceResolutionError(
            "Resolution failed", reference_id="id-1", reference_type="scene"
        )
        assert error.reference_id == "id-1"
        assert error.reference_type == "scene"

    def test_dangling_reference_error(self) -> None:
        """Test DanglingReferenceError."""
        error = DanglingReferenceError(
            "Dangling ref", reference_id="id-1", reference_type="scene"
        )
        assert error.reference_id == "id-1"
        assert isinstance(error, ReferenceResolutionError)

    def test_integration_validation_error(self) -> None:
        """Test IntegrationValidationError."""
        error = IntegrationValidationError("Validation failed", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)


class TestIntegrationScenario:
    """Integration scenario tests."""

    def test_full_project_context(self) -> None:
        """Test full project context with all entity types."""
        context = ProjectContext()

        # Create project
        project = Project(id="project-1", name="Test Project")
        context.set_project(project)

        # Create scenes
        scene1 = Scene(id="scene-1", name="Scene 1")
        obj1 = SceneObject(id="obj-1", name="Object 1")
        scene1.add_object(obj1)
        context.register_scene(scene1)

        # Create timeline
        timeline1 = Timeline(id="timeline-1", name="Timeline 1")
        track1 = Track(id="track-1", name="Track 1")
        timeline1.add_track(track1)
        context.register_timeline(timeline1)

        # Create assets
        asset1 = Asset(id="asset-1", name="Design", asset_type=AssetType.IMAGE)
        asset2 = Asset(id="asset-2", name="Portrait", asset_type=AssetType.IMAGE)
        context.register_asset(asset1)
        context.register_asset(asset2)

        # Create characters
        char1 = Character(id="char-1", name="Character 1")
        char1.set_scene_reference("scene-1")
        char1.set_object_reference("obj-1")
        char1.references.track_ids = ["track-1"]
        char1.references.design_asset_id = "asset-1"
        char1.references.portrait_asset_id = "asset-2"
        context.register_character(char1)

        # Create camera
        camera1 = Camera(id="cam-1", name="Camera 1")
        camera1.set_scene_reference("scene-1")
        camera1.set_target_reference("obj-1")
        context.register_camera(camera1)

        # Validate
        validator = IntegrationValidator(context)
        errors = validator.validate()
        assert errors == []

        # Resolve references
        resolver = ReferenceResolver(context)
        scene = resolver.resolve_scene_reference("scene-1")
        assert scene.id == "scene-1"

        char = resolver.resolve_character_reference("char-1")
        assert char.id == "char-1"

        # Verify counts
        assert context.total_count() == 7
        assert context.scene_count() == 1
        assert context.character_count() == 1
        assert context.camera_count() == 1
        assert context.timeline_count() == 1
        assert context.asset_count() == 2
