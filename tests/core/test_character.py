"""Tests for core/character module."""

import json

import pytest

from core.character import (
    Character,
    CharacterAppearance,
    CharacterCollection,
    CharacterDuplicateIDError,
    CharacterError,
    CharacterMetadata,
    CharacterNotFoundError,
    CharacterProperties,
    CharacterReferenceError,
    CharacterReferences,
    CharacterSerializationError,
    CharacterSerializer,
    CharacterState,
    CharacterValidationError,
)


class TestCharacterCreation:
    """Tests for character creation."""

    def test_create_character_defaults(self) -> None:
        """Test creating character with defaults."""
        char = Character()
        assert char.id is not None
        assert char.name == ""
        assert char.display_name == ""
        assert char.metadata is not None
        assert char.appearance is not None
        assert char.properties is not None
        assert char.state is not None
        assert char.references is not None

    def test_create_character_with_values(self) -> None:
        """Test creating character with values."""
        char = Character(
            name="Hero",
            display_name="The Hero",
        )
        assert char.name == "Hero"
        assert char.display_name == "The Hero"

    def test_character_unique_id(self) -> None:
        """Test that each character gets unique ID."""
        char1 = Character()
        char2 = Character()
        assert char1.id != char2.id

    def test_character_with_custom_id(self) -> None:
        """Test creating character with custom ID."""
        char = Character(id="custom-id-123")
        assert char.id == "custom-id-123"


class TestCharacterMetadata:
    """Tests for character metadata."""

    def test_metadata_defaults(self) -> None:
        """Test metadata defaults."""
        metadata = CharacterMetadata()
        assert metadata.description == ""
        assert metadata.tags == []
        assert metadata.notes == ""
        assert metadata.created_at is not None
        assert metadata.updated_at is not None

    def test_metadata_with_values(self) -> None:
        """Test metadata with values."""
        metadata = CharacterMetadata(
            description="A brave hero",
            tags=["hero", "protagonist"],
            notes="Important character",
        )
        assert metadata.description == "A brave hero"
        assert metadata.tags == ["hero", "protagonist"]


class TestCharacterAppearance:
    """Tests for character appearance."""

    def test_appearance_defaults(self) -> None:
        """Test appearance defaults."""
        appearance = CharacterAppearance()
        assert appearance.description == ""
        assert appearance.style == ""
        assert appearance.hair_color == ""
        assert appearance.eye_color == ""
        assert appearance.asset_references == {}

    def test_appearance_with_values(self) -> None:
        """Test appearance with values."""
        appearance = CharacterAppearance(
            description="Tall with blue hair",
            style="anime",
            hair_color="blue",
            eye_color="green",
        )
        assert appearance.style == "anime"
        assert appearance.hair_color == "blue"

    def test_asset_references(self) -> None:
        """Test asset reference operations."""
        appearance = CharacterAppearance()
        appearance.set_asset_reference("design", "asset-001")
        assert appearance.has_asset_reference("design") is True
        assert appearance.get_asset_reference("design") == "asset-001"

        appearance.remove_asset_reference("design")
        assert appearance.has_asset_reference("design") is False


class TestCharacterProperties:
    """Tests for character properties."""

    def test_properties_defaults(self) -> None:
        """Test properties defaults."""
        props = CharacterProperties()
        assert props.height == ""
        assert props.age == ""
        assert props.role == ""
        assert props.faction == ""

    def test_properties_with_values(self) -> None:
        """Test properties with values."""
        props = CharacterProperties(
            height="tall",
            age="young adult",
            role="warrior",
            faction="knights",
        )
        assert props.height == "tall"
        assert props.role == "warrior"


class TestCharacterState:
    """Tests for character state."""

    def test_state_defaults(self) -> None:
        """Test state defaults."""
        state = CharacterState()
        assert state.active is True
        assert state.visible is True
        assert state.enabled is True

    def test_state_with_values(self) -> None:
        """Test state with values."""
        state = CharacterState(active=False, visible=True, enabled=False)
        assert state.active is False
        assert state.enabled is False


class TestCharacterReferences:
    """Tests for character references."""

    def test_references_defaults(self) -> None:
        """Test references defaults."""
        refs = CharacterReferences()
        assert refs.design_asset_id == ""
        assert refs.scene_id == ""
        assert refs.track_ids == []

    def test_scene_reference(self) -> None:
        """Test scene reference operations."""
        refs = CharacterReferences()
        refs.set_scene_reference("scene-001")
        assert refs.get_scene_reference() == "scene-001"

    def test_object_reference(self) -> None:
        """Test object reference operations."""
        refs = CharacterReferences()
        refs.set_object_reference("object-001")
        assert refs.get_object_reference() == "object-001"

    def test_track_references(self) -> None:
        """Test track reference operations."""
        refs = CharacterReferences()
        refs.add_track_reference("track-001")
        refs.add_track_reference("track-002")
        assert "track-001" in refs.get_track_references()
        assert "track-002" in refs.get_track_references()

        refs.remove_track_reference("track-001")
        assert "track-001" not in refs.get_track_references()

    def test_asset_references(self) -> None:
        """Test asset reference operations."""
        refs = CharacterReferences()
        refs.set_asset_reference("design", "design-001")
        assert refs.get_asset_reference("design") == "design-001"

    def test_invalid_asset_reference(self) -> None:
        """Test invalid asset reference raises error."""
        refs = CharacterReferences()
        with pytest.raises(CharacterReferenceError):
            refs.set_asset_reference("invalid", "value")


class TestCharacter:
    """Tests for main character model."""

    def test_update_name(self) -> None:
        """Test updating character name."""
        char = Character(name="Original")
        char.update_name("Updated")
        assert char.name == "Updated"

    def test_update_display_name(self) -> None:
        """Test updating display name."""
        char = Character()
        char.update_display_name("Display")
        assert char.display_name == "Display"

    def test_set_active(self) -> None:
        """Test setting active state."""
        char = Character()
        char.set_active(False)
        assert char.state.active is False

    def test_set_visible(self) -> None:
        """Test setting visible state."""
        char = Character()
        char.set_visible(False)
        assert char.state.visible is False

    def test_set_enabled(self) -> None:
        """Test setting enabled state."""
        char = Character()
        char.set_enabled(False)
        assert char.state.enabled is False

    def test_tags(self) -> None:
        """Test tag operations."""
        char = Character()
        char.add_tag("hero")
        assert char.has_tag("hero") is True
        char.remove_tag("hero")
        assert char.has_tag("hero") is False

    def test_custom_properties(self) -> None:
        """Test custom property operations."""
        char = Character()
        char.set_custom_property("key1", "value1")
        assert char.get_custom_property("key1") == "value1"
        char.remove_custom_property("key1")
        assert char.get_custom_property("key1") is None

    def test_scene_reference(self) -> None:
        """Test scene reference through character."""
        char = Character()
        char.set_scene_reference("scene-001")
        assert char.get_scene_reference() == "scene-001"

    def test_object_reference(self) -> None:
        """Test object reference through character."""
        char = Character()
        char.set_object_reference("object-001")
        assert char.get_object_reference() == "object-001"

    def test_track_references(self) -> None:
        """Test track references through character."""
        char = Character()
        char.add_track_reference("track-001")
        assert "track-001" in char.get_track_references()
        char.remove_track_reference("track-001")
        assert "track-001" not in char.get_track_references()


class TestCharacterValidation:
    """Tests for character validation."""

    def test_validate_valid_character(self) -> None:
        """Test validating a valid character."""
        char = Character(name="Valid Character")
        errors = char.validate()
        assert errors == []

    def test_validate_empty_name(self) -> None:
        """Test validation allows empty name."""
        char = Character()
        errors = char.validate()
        assert errors == []

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise works for valid character."""
        char = Character(name="Valid")
        char.validate_or_raise()  # Should not raise


class TestCharacterCollection:
    """Tests for character collection."""

    def test_create_empty_collection(self) -> None:
        """Test creating empty collection."""
        collection = CharacterCollection()
        assert collection.count() == 0

    def test_add_character(self) -> None:
        """Test adding character to collection."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        assert collection.count() == 1
        assert collection.has(char.id) is True

    def test_add_duplicate_rejected(self) -> None:
        """Test adding duplicate character raises error."""
        collection = CharacterCollection()
        char = Character(id="same-id", name="Hero")
        collection.add(char)
        with pytest.raises(CharacterDuplicateIDError):
            collection.add(Character(id="same-id", name="Villain"))

    def test_remove_character(self) -> None:
        """Test removing character from collection."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        removed = collection.remove(char.id)
        assert removed.name == "Hero"
        assert collection.count() == 0

    def test_remove_nonexistent(self) -> None:
        """Test removing nonexistent character raises error."""
        collection = CharacterCollection()
        with pytest.raises(CharacterNotFoundError):
            collection.remove("nonexistent")

    def test_get_character(self) -> None:
        """Test getting character from collection."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        retrieved = collection.get(char.id)
        assert retrieved.name == "Hero"

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent character raises error."""
        collection = CharacterCollection()
        with pytest.raises(CharacterNotFoundError):
            collection.get("nonexistent")

    def test_has_character(self) -> None:
        """Test checking character existence."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        assert collection.has(char.id) is True
        assert collection.has("nonexistent") is False

    def test_list_characters(self) -> None:
        """Test listing characters."""
        collection = CharacterCollection()
        char1 = Character(name="Zara")
        char2 = Character(name="Alpha")
        collection.add(char1)
        collection.add(char2)
        names = [c.name for c in collection.list()]
        assert names == ["Alpha", "Zara"]  # Sorted alphabetically

    def test_list_by_tag(self) -> None:
        """Test listing characters by tag."""
        collection = CharacterCollection()
        char1 = Character(name="Hero")
        char1.add_tag("protagonist")
        char2 = Character(name="Villain")
        collection.add(char1)
        collection.add(char2)
        protagonists = collection.list_by_tag("protagonist")
        assert len(protagonists) == 1
        assert protagonists[0].name == "Hero"

    def test_find_by_name(self) -> None:
        """Test finding character by name."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        found = collection.find_by_name("Hero")
        assert found is not None
        assert found.name == "Hero"

    def test_find_by_display_name(self) -> None:
        """Test finding character by display name."""
        collection = CharacterCollection()
        char = Character(name="Hero", display_name="The Hero")
        collection.add(char)
        found = collection.find_by_display_name("The Hero")
        assert found is not None
        assert found.name == "Hero"

    def test_count(self) -> None:
        """Test counting characters."""
        collection = CharacterCollection()
        assert collection.count() == 0
        collection.add(Character(name="A"))
        collection.add(Character(name="B"))
        assert collection.count() == 2

    def test_clear(self) -> None:
        """Test clearing collection."""
        collection = CharacterCollection()
        collection.add(Character(name="A"))
        collection.add(Character(name="B"))
        collection.clear()
        assert collection.count() == 0

    def test_update(self) -> None:
        """Test updating character."""
        collection = CharacterCollection()
        char = Character(id="char-1", name="Original")
        collection.add(char)
        updated = collection.update(char.id, name="Updated")
        assert updated.name == "Updated"

    def test_validate_all(self) -> None:
        """Test validating all characters."""
        collection = CharacterCollection()
        char = Character(name="Valid")
        collection.add(char)
        invalid = collection.validate_all()
        assert invalid == []

    def test_iteration(self) -> None:
        """Test iterating over collection."""
        collection = CharacterCollection()
        char1 = Character(name="B")
        char2 = Character(name="A")
        collection.add(char1)
        collection.add(char2)
        names = [c.name for c in collection]
        assert names == ["A", "B"]

    def test_bracket_notation(self) -> None:
        """Test bracket notation access."""
        collection = CharacterCollection()
        char = Character(name="Hero")
        collection.add(char)
        retrieved = collection[char.id]
        assert retrieved.name == "Hero"


class TestCharacterSerialization:
    """Tests for character serialization."""

    def test_serialize_empty_character(self) -> None:
        """Test serializing character with defaults."""
        char = Character()
        data = CharacterSerializer.serialize(char)
        assert data["id"] == char.id
        assert data["name"] == ""

    def test_serialize_full_character(self) -> None:
        """Test serializing full character."""
        char = Character(
            name="Hero",
            display_name="The Hero",
        )
        char.metadata.tags.append("protagonist")
        char.appearance.style = "anime"
        char.set_scene_reference("scene-001")
        char.add_track_reference("track-001")

        data = CharacterSerializer.serialize(char)
        assert data["name"] == "Hero"
        assert data["display_name"] == "The Hero"
        assert "protagonist" in data["metadata"]["tags"]
        assert data["appearance"]["style"] == "anime"
        assert data["references"]["scene_id"] == "scene-001"
        assert "track-001" in data["references"]["track_ids"]

    def test_deserialize_character(self) -> None:
        """Test deserializing character."""
        char = Character(name="Original")
        data = CharacterSerializer.serialize(char)
        restored = CharacterSerializer.deserialize(data)
        assert restored.id == char.id
        assert restored.name == "Original"

    def test_roundtrip_preservation(self) -> None:
        """Test serialization roundtrip preserves data."""
        char = Character(
            name="Hero",
            display_name="The Hero",
        )
        char.metadata.description = "A brave hero"
        char.metadata.tags = ["hero", "protagonist"]
        char.appearance.style = "anime"
        char.appearance.hair_color = "blue"
        char.properties.role = "warrior"
        char.state.active = False
        char.set_scene_reference("scene-001")
        char.add_track_reference("track-001")
        char.set_custom_property("key1", "value1")

        data = CharacterSerializer.serialize(char)
        restored = CharacterSerializer.deserialize(data)

        assert restored.id == char.id
        assert restored.name == "Hero"
        assert restored.display_name == "The Hero"
        assert restored.metadata.description == "A brave hero"
        assert restored.metadata.tags == ["hero", "protagonist"]
        assert restored.appearance.style == "anime"
        assert restored.appearance.hair_color == "blue"
        assert restored.properties.role == "warrior"
        assert restored.state.active is False
        assert restored.get_scene_reference() == "scene-001"
        assert "track-001" in restored.get_track_references()
        assert restored.get_custom_property("key1") == "value1"

    def test_to_json(self) -> None:
        """Test serializing to JSON."""
        char = Character(name="Hero")
        json_str = CharacterSerializer.to_json(char)
        data = json.loads(json_str)
        assert data["name"] == "Hero"

    def test_from_json(self) -> None:
        """Test deserializing from JSON."""
        char = Character(name="Hero")
        json_str = CharacterSerializer.to_json(char)
        restored = CharacterSerializer.from_json(json_str)
        assert restored.name == "Hero"

    def test_deserialize_invalid_data(self) -> None:
        """Test deserializing invalid data raises error."""
        with pytest.raises(
            CharacterSerializationError, match="Missing required field"
        ):
            CharacterSerializer.deserialize({})

    def test_from_invalid_json(self) -> None:
        """Test from_json raises error for invalid JSON."""
        with pytest.raises(CharacterSerializationError, match="Invalid JSON"):
            CharacterSerializer.from_json("not valid json {{{")


class TestCharacterExceptions:
    """Tests for character exceptions."""

    def test_validation_error_with_errors(self) -> None:
        """Test CharacterValidationError contains error list."""
        error = CharacterValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)

    def test_exception_hierarchy(self) -> None:
        """Test exception hierarchy."""
        assert issubclass(CharacterValidationError, CharacterError)
        assert issubclass(CharacterNotFoundError, CharacterError)
        assert issubclass(CharacterDuplicateIDError, CharacterError)
        assert issubclass(CharacterSerializationError, CharacterError)
        assert issubclass(CharacterReferenceError, CharacterError)

    def test_exception_raising(self) -> None:
        """Test exceptions can be raised."""
        with pytest.raises(CharacterNotFoundError):
            raise CharacterNotFoundError("Not found")

        with pytest.raises(CharacterDuplicateIDError):
            raise CharacterDuplicateIDError("Duplicate ID")

        with pytest.raises(CharacterReferenceError):
            raise CharacterReferenceError("Invalid reference")
