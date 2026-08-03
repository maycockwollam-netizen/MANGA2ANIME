"""Tests for core/asset module."""

import json

import pytest

from core.asset import (
    Asset,
    AssetCollection,
    AssetDuplicateIDError,
    AssetError,
    AssetMetadata,
    AssetNotFoundError,
    AssetProperties,
    AssetReference,
    AssetReferenceError,
    AssetSerializationError,
    AssetSerializer,
    AssetState,
    AssetType,
    AssetTypeError,
    AssetValidationError,
    AssetValidator,
)


class TestAssetCreation:
    """Tests for asset creation."""

    def test_create_asset_defaults(self) -> None:
        """Test creating asset with defaults."""
        asset = Asset()
        assert asset.id is not None
        assert asset.name == ""
        assert asset.asset_type == AssetType.OTHER
        assert asset.metadata is not None
        assert asset.reference is not None
        assert asset.properties is not None
        assert asset.state is not None

    def test_create_asset_with_values(self) -> None:
        """Test creating asset with values."""
        asset = Asset(name="test_asset", asset_type=AssetType.IMAGE)
        assert asset.name == "test_asset"
        assert asset.asset_type == AssetType.IMAGE

    def test_asset_unique_id(self) -> None:
        """Test that each asset gets unique ID."""
        asset1 = Asset()
        asset2 = Asset()
        assert asset1.id != asset2.id

    def test_asset_with_custom_id(self) -> None:
        """Test creating asset with custom ID."""
        asset = Asset(id="custom-id-123")
        assert asset.id == "custom-id-123"


class TestAssetType:
    """Tests for AssetType enum."""

    def test_all_asset_types(self) -> None:
        """Test all asset type values exist."""
        assert AssetType.IMAGE.value == "image"
        assert AssetType.MANGA_PAGE.value == "manga_page"
        assert AssetType.CHARACTER_REFERENCE.value == "character_reference"
        assert AssetType.BACKGROUND.value == "background"
        assert AssetType.SPRITE.value == "sprite"
        assert AssetType.TEXTURE.value == "texture"
        assert AssetType.AUDIO.value == "audio"
        assert AssetType.VOICE.value == "voice"
        assert AssetType.MUSIC.value == "music"
        assert AssetType.SFX.value == "sfx"
        assert AssetType.VIDEO.value == "video"
        assert AssetType.ANIMATION.value == "animation"
        assert AssetType.FONT.value == "font"
        assert AssetType.TEXTURE_ATLAS.value == "texture_atlas"
        assert AssetType.DATA.value == "data"
        assert AssetType.CONFIG.value == "config"
        assert AssetType.OTHER.value == "other"

    def test_is_image(self) -> None:
        """Test is_image classification."""
        assert AssetType.is_image(AssetType.IMAGE) is True
        assert AssetType.is_image(AssetType.MANGA_PAGE) is True
        assert AssetType.is_image(AssetType.BACKGROUND) is True
        assert AssetType.is_image(AssetType.AUDIO) is False

    def test_is_audio(self) -> None:
        """Test is_audio classification."""
        assert AssetType.is_audio(AssetType.AUDIO) is True
        assert AssetType.is_audio(AssetType.VOICE) is True
        assert AssetType.is_audio(AssetType.MUSIC) is True
        assert AssetType.is_audio(AssetType.IMAGE) is False

    def test_is_video(self) -> None:
        """Test is_video classification."""
        assert AssetType.is_video(AssetType.VIDEO) is True
        assert AssetType.is_video(AssetType.ANIMATION) is True
        assert AssetType.is_video(AssetType.IMAGE) is False


class TestAssetMetadata:
    """Tests for asset metadata."""

    def test_defaults(self) -> None:
        """Test metadata defaults."""
        metadata = AssetMetadata()
        assert metadata.name == ""
        assert metadata.display_name == ""
        assert metadata.tags == []
        assert metadata.author == ""
        assert metadata.source == ""

    def test_with_values(self) -> None:
        """Test metadata with values."""
        metadata = AssetMetadata(
            name="Test Asset",
            display_name="Test Display",
            tags=["tag1", "tag2"],
            author="Test Author",
        )
        assert metadata.name == "Test Asset"
        assert metadata.tags == ["tag1", "tag2"]


class TestAssetReference:
    """Tests for asset reference."""

    def test_defaults(self) -> None:
        """Test reference defaults."""
        ref = AssetReference()
        assert ref.path == ""
        assert ref.uri == ""
        assert ref.checksum == ""

    def test_with_values(self) -> None:
        """Test reference with values."""
        ref = AssetReference(
            path="/path/to/asset.png",
            uri="file:///path/to/asset.png",
            mime_type="image/png",
            extension="png",
            size_bytes=1024,
        )
        assert ref.path == "/path/to/asset.png"
        assert ref.size_bytes == 1024

    def test_has_methods(self) -> None:
        """Test has methods."""
        ref = AssetReference(path="/path/to/asset.png", checksum="abc123")
        assert ref.has_path() is True
        assert ref.has_uri() is False
        assert ref.has_checksum() is True


class TestAssetProperties:
    """Tests for asset properties."""

    def test_defaults(self) -> None:
        """Test properties defaults."""
        props = AssetProperties()
        assert props.width is None
        assert props.height is None
        assert props.duration is None

    def test_image_properties(self) -> None:
        """Test image properties."""
        props = AssetProperties(width=1920, height=1080, format="PNG")
        assert props.is_image_like() is True
        assert props.is_video_like() is False
        dims = props.get_dimensions()
        assert dims == (1920, 1080)

    def test_audio_properties(self) -> None:
        """Test audio properties."""
        props = AssetProperties(duration=180.0, sample_rate=44100, channels=2)
        assert props.is_audio_like() is True
        assert props.is_image_like() is False

    def test_video_properties(self) -> None:
        """Test video properties."""
        props = AssetProperties(
            width=1920,
            height=1080,
            duration=120.0,
        )
        assert props.is_video_like() is True
        ar = props.get_aspect_ratio()
        assert abs(ar - 16 / 9) < 0.001

    def test_invalid_dimensions(self) -> None:
        """Test invalid dimensions are rejected."""
        with pytest.raises(ValueError):
            AssetProperties(width=-1)
        with pytest.raises(ValueError):
            AssetProperties(height=-1)


class TestAssetState:
    """Tests for asset state."""

    def test_defaults(self) -> None:
        """Test state defaults."""
        state = AssetState()
        assert state.enabled is True
        assert state.available is True
        assert state.verified is False

    def test_with_values(self) -> None:
        """Test state with values."""
        state = AssetState(enabled=False, available=True, verified=True)
        assert state.enabled is False
        assert state.verified is True


class TestAsset:
    """Tests for main asset model."""

    def test_update_name(self) -> None:
        """Test updating asset name."""
        asset = Asset(name="Original")
        asset.update_name("Updated")
        assert asset.name == "Updated"

    def test_update_display_name(self) -> None:
        """Test updating display name."""
        asset = Asset()
        asset.update_display_name("Display")
        assert asset.metadata.display_name == "Display"

    def test_set_asset_type(self) -> None:
        """Test setting asset type."""
        asset = Asset(asset_type=AssetType.IMAGE)
        asset.set_asset_type(AssetType.VIDEO)
        assert asset.asset_type == AssetType.VIDEO

    def test_state_methods(self) -> None:
        """Test state methods."""
        asset = Asset()
        asset.set_enabled(False)
        asset.set_available(False)
        asset.set_verified(True)
        assert asset.state.enabled is False
        assert asset.state.available is False
        assert asset.state.verified is True

    def test_tags(self) -> None:
        """Test tag operations."""
        asset = Asset()
        asset.add_tag("test")
        assert asset.has_tag("test") is True
        asset.remove_tag("test")
        assert asset.has_tag("test") is False

    def test_path_operations(self) -> None:
        """Test path operations."""
        asset = Asset()
        asset.set_path("/path/to/asset.png")
        assert asset.get_path() == "/path/to/asset.png"

    def test_uri_operations(self) -> None:
        """Test URI operations."""
        asset = Asset()
        asset.set_uri("file:///path/to/asset.png")
        assert asset.get_uri() == "file:///path/to/asset.png"

    def test_checksum_operations(self) -> None:
        """Test checksum operations."""
        asset = Asset()
        asset.set_checksum("abc123")
        assert asset.get_checksum() == "abc123"

    def test_size_operations(self) -> None:
        """Test size operations."""
        asset = Asset()
        asset.set_size(1024)
        assert asset.get_size() == 1024


class TestAssetValidation:
    """Tests for asset validation."""

    def test_validate_valid_asset(self) -> None:
        """Test validating a valid asset."""
        asset = Asset(name="Valid Asset")
        errors = asset.validate()
        assert errors == []

    def test_validate_or_raise(self) -> None:
        """Test validate_or_raise works for valid asset."""
        asset = Asset(name="Valid")
        asset.validate_or_raise()  # Should not raise


class TestAssetValidator:
    """Tests for AssetValidator."""

    def test_validate_path(self) -> None:
        """Test path validation."""
        errors = AssetValidator.validate_path("")
        assert "empty" in errors[0].lower()
        errors = AssetValidator.validate_path("/valid/path.png")
        assert errors == []

    def test_validate_uri(self) -> None:
        """Test URI validation."""
        errors = AssetValidator.validate_uri("")
        assert "empty" in errors[0].lower()
        errors = AssetValidator.validate_uri("https://example.com/asset.png")
        assert errors == []

    def test_validate_dimensions(self) -> None:
        """Test dimension validation."""
        errors = AssetValidator.validate_dimensions(0, 100)
        assert any("positive" in e.lower() for e in errors)
        errors = AssetValidator.validate_dimensions(1920, 1080)
        assert errors == []

    def test_validate_duration(self) -> None:
        """Test duration validation."""
        errors = AssetValidator.validate_duration(-1.0)
        assert any("non-negative" in e.lower() for e in errors)
        errors = AssetValidator.validate_duration(60.0)
        assert errors == []


class TestAssetCollection:
    """Tests for asset collection."""

    def test_create_empty_collection(self) -> None:
        """Test creating empty collection."""
        collection = AssetCollection()
        assert collection.count() == 0

    def test_add_asset(self) -> None:
        """Test adding asset to collection."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        assert collection.count() == 1
        assert collection.has(asset.id) is True

    def test_add_duplicate_rejected(self) -> None:
        """Test adding duplicate asset raises error."""
        collection = AssetCollection()
        asset = Asset(id="same-id", name="Asset 1")
        collection.add(asset)
        with pytest.raises(AssetDuplicateIDError):
            collection.add(Asset(id="same-id", name="Asset 2"))

    def test_remove_asset(self) -> None:
        """Test removing asset from collection."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        removed = collection.remove(asset.id)
        assert removed.name == "Test Asset"
        assert collection.count() == 0

    def test_remove_nonexistent(self) -> None:
        """Test removing nonexistent asset raises error."""
        collection = AssetCollection()
        with pytest.raises(AssetNotFoundError):
            collection.remove("nonexistent")

    def test_get_asset(self) -> None:
        """Test getting asset from collection."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        retrieved = collection.get(asset.id)
        assert retrieved.name == "Test Asset"

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent asset raises error."""
        collection = AssetCollection()
        with pytest.raises(AssetNotFoundError):
            collection.get("nonexistent")

    def test_has_asset(self) -> None:
        """Test checking asset existence."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        assert collection.has(asset.id) is True
        assert collection.has("nonexistent") is False

    def test_list_assets(self) -> None:
        """Test listing assets."""
        collection = AssetCollection()
        asset1 = Asset(name="Zara")
        asset2 = Asset(name="Alpha")
        collection.add(asset1)
        collection.add(asset2)
        names = [a.name for a in collection.list()]
        assert names == ["Alpha", "Zara"]

    def test_list_by_type(self) -> None:
        """Test listing assets by type."""
        collection = AssetCollection()
        asset1 = Asset(name="Image", asset_type=AssetType.IMAGE)
        asset2 = Asset(name="Audio", asset_type=AssetType.AUDIO)
        collection.add(asset1)
        collection.add(asset2)
        images = collection.list_by_type(AssetType.IMAGE)
        assert len(images) == 1
        assert images[0].name == "Image"

    def test_list_by_tag(self) -> None:
        """Test listing assets by tag."""
        collection = AssetCollection()
        asset1 = Asset(name="Tagged")
        asset1.add_tag("important")
        asset2 = Asset(name="Untagged")
        collection.add(asset1)
        collection.add(asset2)
        tagged = collection.list_by_tag("important")
        assert len(tagged) == 1
        assert tagged[0].name == "Tagged"

    def test_find_by_name(self) -> None:
        """Test finding asset by name."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        found = collection.find_by_name("Test Asset")
        assert found is not None
        assert found.name == "Test Asset"

    def test_get_available(self) -> None:
        """Test getting available assets."""
        collection = AssetCollection()
        asset1 = Asset(name="Available")
        asset1.set_available(True)
        asset2 = Asset(name="Unavailable")
        asset2.set_available(False)
        collection.add(asset1)
        collection.add(asset2)
        available = collection.get_available()
        assert len(available) == 1
        assert available[0].name == "Available"

    def test_count(self) -> None:
        """Test counting assets."""
        collection = AssetCollection()
        assert collection.count() == 0
        collection.add(Asset(name="A"))
        collection.add(Asset(name="B"))
        assert collection.count() == 2

    def test_clear(self) -> None:
        """Test clearing collection."""
        collection = AssetCollection()
        collection.add(Asset(name="A"))
        collection.add(Asset(name="B"))
        collection.clear()
        assert collection.count() == 0

    def test_iteration(self) -> None:
        """Test iterating over collection."""
        collection = AssetCollection()
        asset1 = Asset(name="B")
        asset2 = Asset(name="A")
        collection.add(asset1)
        collection.add(asset2)
        names = [a.name for a in collection]
        assert names == ["A", "B"]

    def test_bracket_notation(self) -> None:
        """Test bracket notation access."""
        collection = AssetCollection()
        asset = Asset(name="Test Asset")
        collection.add(asset)
        retrieved = collection[asset.id]
        assert retrieved.name == "Test Asset"


class TestAssetSerialization:
    """Tests for asset serialization."""

    def test_serialize_empty_asset(self) -> None:
        """Test serializing asset with defaults."""
        asset = Asset()
        data = AssetSerializer.serialize(asset)
        assert data["id"] == asset.id
        assert data["name"] == ""

    def test_serialize_full_asset(self) -> None:
        """Test serializing full asset."""
        asset = Asset(name="Test Asset", asset_type=AssetType.IMAGE)
        asset.set_path("/path/to/asset.png")
        asset.properties.width = 1920
        asset.properties.height = 1080

        data = AssetSerializer.serialize(asset)
        assert data["name"] == "Test Asset"
        assert data["asset_type"] == "image"
        assert data["reference"]["path"] == "/path/to/asset.png"
        assert data["properties"]["width"] == 1920

    def test_deserialize_asset(self) -> None:
        """Test deserializing asset."""
        asset = Asset(name="Original")
        data = AssetSerializer.serialize(asset)
        restored = AssetSerializer.deserialize(data)
        assert restored.id == asset.id
        assert restored.name == "Original"

    def test_roundtrip_preservation(self) -> None:
        """Test serialization roundtrip preserves data."""
        asset = Asset(name="Test Asset", asset_type=AssetType.VIDEO)
        asset.add_tag("important")
        asset.set_path("/path/to/video.mp4")
        asset.properties.width = 1920
        asset.properties.height = 1080
        asset.properties.duration = 120.0
        asset.state.verified = True

        data = AssetSerializer.serialize(asset)
        restored = AssetSerializer.deserialize(data)

        assert restored.id == asset.id
        assert restored.name == "Test Asset"
        assert restored.asset_type == AssetType.VIDEO
        assert "important" in restored.metadata.tags
        assert restored.get_path() == "/path/to/video.mp4"
        assert restored.properties.width == 1920
        assert restored.properties.duration == 120.0
        assert restored.state.verified is True

    def test_to_json(self) -> None:
        """Test serializing to JSON."""
        asset = Asset(name="Test Asset")
        json_str = AssetSerializer.to_json(asset)
        data = json.loads(json_str)
        assert data["name"] == "Test Asset"

    def test_from_json(self) -> None:
        """Test deserializing from JSON."""
        asset = Asset(name="Test Asset")
        json_str = AssetSerializer.to_json(asset)
        restored = AssetSerializer.from_json(json_str)
        assert restored.name == "Test Asset"

    def test_deserialize_invalid_data(self) -> None:
        """Test deserializing invalid data raises error."""
        with pytest.raises(
            AssetSerializationError, match="Missing required field"
        ):
            AssetSerializer.deserialize({})

    def test_from_invalid_json(self) -> None:
        """Test from_json raises error for invalid JSON."""
        with pytest.raises(AssetSerializationError, match="Invalid JSON"):
            AssetSerializer.from_json("not valid json {{{")


class TestAssetExceptions:
    """Tests for asset exceptions."""

    def test_validation_error_with_errors(self) -> None:
        """Test AssetValidationError contains error list."""
        error = AssetValidationError("Test", errors=["error1", "error2"])
        assert error.errors == ["error1", "error2"]
        assert "error1" in str(error)

    def test_exception_hierarchy(self) -> None:
        """Test exception hierarchy."""
        assert issubclass(AssetValidationError, AssetError)
        assert issubclass(AssetNotFoundError, AssetError)
        assert issubclass(AssetDuplicateIDError, AssetError)
        assert issubclass(AssetSerializationError, AssetError)
        assert issubclass(AssetReferenceError, AssetError)
        assert issubclass(AssetTypeError, AssetError)

    def test_exception_raising(self) -> None:
        """Test exceptions can be raised."""
        with pytest.raises(AssetNotFoundError):
            raise AssetNotFoundError("Not found")

        with pytest.raises(AssetDuplicateIDError):
            raise AssetDuplicateIDError("Duplicate ID")

        with pytest.raises(AssetReferenceError):
            raise AssetReferenceError("Invalid reference")
